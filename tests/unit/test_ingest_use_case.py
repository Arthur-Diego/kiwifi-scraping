from __future__ import annotations

from src.application.use_cases.ingest_transcripts import IngestTranscriptsInput, IngestTranscriptsUseCase
from src.domain.knowledge.entities import TranscriptDocument


class FakeTranscriptRepo:
    def iter_transcripts(self, input_paths: list[str]):
        _ = input_paths
        yield TranscriptDocument(
            source_path="/tmp/a.txt",
            source_file="a.txt",
            text="A" * 2600,
            section="secao1",
            topic_hint="topico1",
        )


class FakeVectorStore:
    def __init__(self):
        self.upserted = []

    def upsert_chunks(self, chunks, *, collection: str):
        self.upserted = chunks
        self.collection = collection

    def search(self, query: str, *, collection: str, top_k: int = 8, section: str | None = None):
        raise NotImplementedError

    def list_sections(self, *, collection: str):
        raise NotImplementedError

    def delete_collection(self, *, collection: str):
        raise NotImplementedError


class FakeLogger:
    def info(self, message: str) -> None:
        _ = message

    def warning(self, message: str) -> None:
        _ = message

    def error(self, message: str) -> None:
        _ = message


def test_ingest_creates_and_upserts_chunks() -> None:
    use_case = IngestTranscriptsUseCase(
        transcript_repo=FakeTranscriptRepo(),
        vector_store=FakeVectorStore(),
        logger=FakeLogger(),
    )

    result = use_case.execute(IngestTranscriptsInput(input_paths=["/tmp"], chunk_size_chars=1000, chunk_overlap_chars=100))

    assert result.files_indexed == 1
    assert result.chunks_indexed >= 3
