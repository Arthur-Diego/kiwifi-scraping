from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backup_legacy.rag_qdrant.step1_ingestion import TextLoader
from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeInput, ChatWithKnowledgeUseCase
from src.application.use_cases.ingest_transcripts import IngestTranscriptsInput, IngestTranscriptsUseCase
from src.domain.knowledge.entities import RetrievedContext, TranscriptDocument
from src.infrastructure.fs.local_transcript_repository import LocalTranscriptRepository


class _FakeTranscriptRepo:
    def __init__(self, docs: list[TranscriptDocument]):
        self._docs = docs

    def iter_transcripts(self, input_paths: list[str]):
        _ = input_paths
        for doc in self._docs:
            yield doc


class _CaptureVectorStore:
    def __init__(self):
        self.chunks = []

    def upsert_chunks(self, chunks, *, collection: str) -> None:
        _ = collection
        self.chunks.extend(chunks)

    def search(self, query: str, *, collection: str, top_k: int = 8, section: str | None = None):
        _ = query
        _ = collection
        _ = top_k
        _ = section
        return []

    def list_sections(self, *, collection: str):
        _ = collection
        return []

    def delete_collection(self, *, collection: str) -> None:
        _ = collection


class _FakeLogger:
    def info(self, message: str) -> None:
        _ = message

    def warning(self, message: str) -> None:
        _ = message

    def error(self, message: str) -> None:
        _ = message


class _FakeVectorStoreForChat:
    def __init__(self, contexts: list[RetrievedContext]):
        self._contexts = contexts

    def search(self, query: str, *, collection: str, top_k: int = 8, section: str | None = None):
        _ = query
        _ = collection
        _ = top_k
        _ = section
        return self._contexts[:top_k]


class _FakeLLM:
    def __init__(self):
        self.calls = []

    def generate_answer(self, *, query: str, contexts: list[RetrievedContext], model_name: str, temperature: float) -> str:
        self.calls.append({"query": query, "contexts": contexts, "model_name": model_name, "temperature": temperature})
        return f"new-ok:{len(contexts)}"


class RegressionLegacyVsNewTest(unittest.TestCase):
    def test_ingestion_loader_equivalence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            target = base / "secao1" / "topicoA"
            target.mkdir(parents=True, exist_ok=True)
            file_path = target / "video01.txt"
            file_path.write_text("linha 1. linha 2.", encoding="utf-8")

            legacy_items = list(TextLoader().iter_texts(str(base)))
            new_items = list(LocalTranscriptRepository().iter_transcripts([str(base)]))

            self.assertEqual(len(legacy_items), 1)
            self.assertEqual(len(new_items), 1)

            legacy_source, legacy_text, legacy_meta = legacy_items[0]
            new_doc = new_items[0]

            self.assertEqual(new_doc.source_path, legacy_source)
            self.assertEqual(new_doc.text, legacy_text)
            self.assertEqual(new_doc.section, legacy_meta.get("section"))
            self.assertEqual(new_doc.topic_hint, legacy_meta.get("topic_hint"))

    def test_ingestion_generates_chunks(self) -> None:
        text = " ".join(["Frase de teste para chunking"] * 220)

        capture_store = _CaptureVectorStore()
        use_case = IngestTranscriptsUseCase(
            transcript_repo=_FakeTranscriptRepo(
                [TranscriptDocument(source_path="/tmp/doc.txt", source_file="doc.txt", text=text)]
            ),
            vector_store=capture_store,
            logger=_FakeLogger(),
        )

        output = use_case.execute(
            IngestTranscriptsInput(input_paths=["/tmp"], chunk_size_chars=1200, chunk_overlap_chars=120)
        )

        self.assertGreater(output.files_indexed, 0)
        self.assertGreater(output.chunks_indexed, 0)
        self.assertGreater(len(capture_store.chunks), 0)

    def test_embedding_contract_source_based(self) -> None:
        legacy_code = Path("backup_legacy/rag_qdrant/step3_embeddings.py").read_text(encoding="utf-8")
        new_code = Path("src/infrastructure/vectorstores/qdrant_store.py").read_text(encoding="utf-8")

        self.assertIn("SentenceTransformer", legacy_code)
        self.assertIn("normalize_embeddings=True", legacy_code)
        self.assertIn("SentenceTransformer", new_code)
        self.assertIn("normalize_embeddings=True", new_code)

    def test_retrieval_top_k_and_chat_non_empty(self) -> None:
        contexts = [
            RetrievedContext(text=f"ctx-{i}", source_file="video.txt", source_path="secao/video.txt", chunk_index=i)
            for i in range(5)
        ]
        llm = _FakeLLM()
        use_case = ChatWithKnowledgeUseCase(
            vector_store=_FakeVectorStoreForChat(contexts),
            llm=llm,
            logger=_FakeLogger(),
        )

        result = use_case.execute(ChatWithKnowledgeInput(query="Pergunta", top_k=3))

        self.assertTrue(result.answer)
        self.assertEqual(result.answer, "new-ok:3")
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(len(llm.calls[0]["contexts"]), 3)

    def test_chat_fallback_legacy_vs_new(self) -> None:
        legacy_code = Path("backup_legacy/service/rag_service.py").read_text(encoding="utf-8")

        llm = _FakeLLM()
        new_use_case = ChatWithKnowledgeUseCase(
            vector_store=_FakeVectorStoreForChat([]),
            llm=llm,
            logger=_FakeLogger(),
        )
        new_fallback = new_use_case.execute(ChatWithKnowledgeInput(query="Pergunta")).answer

        self.assertIn("Nao encontrei base", legacy_code)
        self.assertIn("Nao encontrei base", new_fallback)

    def test_chat_context_usage_contract_source_and_runtime(self) -> None:
        legacy_code = Path("backup_legacy/service/rag_service.py").read_text(encoding="utf-8")
        self.assertIn("llm.generate_answer", legacy_code)
        self.assertIn("if not contexts", legacy_code)

        llm = _FakeLLM()
        contexts = [RetrievedContext(text="ctx", source_file="f", source_path="f", chunk_index=0)]
        use_case = ChatWithKnowledgeUseCase(
            vector_store=_FakeVectorStoreForChat(contexts),
            llm=llm,
            logger=_FakeLogger(),
        )
        result = use_case.execute(ChatWithKnowledgeInput(query="Pergunta", top_k=1))

        self.assertEqual(result.answer, "new-ok:1")
        self.assertEqual(len(llm.calls[0]["contexts"]), 1)


if __name__ == "__main__":
    unittest.main()
