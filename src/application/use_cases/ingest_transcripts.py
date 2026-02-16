from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from uuid import uuid5, NAMESPACE_URL

from src.application.ports.chunker import ChunkerPort
from src.application.ports.logger_port import LoggerPort
from src.application.ports.transcript_repo import TranscriptRepositoryPort
from src.application.ports.vector_store import VectorStorePort
from src.domain.knowledge.entities import KnowledgeChunk, TranscriptDocument


@dataclass(frozen=True)
class IngestTranscriptsInput:
    input_paths: list[str]
    collection: str = "transcricoes"
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 120
    transcript_version: str = "v1"
    section_override: str | None = None


@dataclass(frozen=True)
class IngestTranscriptsOutput:
    files_indexed: int
    chunks_indexed: int


class IngestTranscriptsUseCase:
    def __init__(
        self,
        *,
        transcript_repo: TranscriptRepositoryPort,
        vector_store: VectorStorePort,
        logger: LoggerPort,
        chunker: ChunkerPort | None = None,
    ):
        self._transcript_repo = transcript_repo
        self._vector_store = vector_store
        self._logger = logger
        self._chunker = chunker

    def execute(self, data: IngestTranscriptsInput) -> IngestTranscriptsOutput:
        all_chunks: list[KnowledgeChunk] = []
        files_indexed = 0

        for doc in self._transcript_repo.iter_transcripts(data.input_paths):
            files_indexed += 1
            chunks = self._chunk_document(
                doc=doc,
                chunk_size_chars=data.chunk_size_chars,
                chunk_overlap_chars=data.chunk_overlap_chars,
                transcript_version=data.transcript_version,
                section_override=data.section_override,
            )
            all_chunks.extend(chunks)

        if all_chunks:
            self._vector_store.upsert_chunks(all_chunks, collection=data.collection)

        self._logger.info(
            f"Indexed {files_indexed} transcript file(s) and {len(all_chunks)} chunk(s) into '{data.collection}'."
        )

        # TODO: persist .index_manifest.json with file hashes and chunking/embedding versions.
        return IngestTranscriptsOutput(files_indexed=files_indexed, chunks_indexed=len(all_chunks))

    def _chunk_document(
        self,
        *,
        doc: TranscriptDocument,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
        transcript_version: str,
        section_override: str | None,
    ) -> list[KnowledgeChunk]:
        text = doc.text.strip()
        if not text:
            return []

        text_chunks = self._build_text_chunks(
            text=text,
            chunk_size_chars=chunk_size_chars,
            chunk_overlap_chars=chunk_overlap_chars,
        )

        chunks: list[KnowledgeChunk] = []
        for chunk_index, chunk_text in enumerate(text_chunks):
            chunk_hash = sha1(chunk_text.encode("utf-8")).hexdigest()[:12]
            chunk_uid = str(uuid5(NAMESPACE_URL, f"{doc.source_path}:{chunk_index}:{chunk_hash}"))
            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_uid,
                    text=chunk_text,
                    source_path=doc.source_path,
                    source_file=doc.source_file,
                    chunk_index=chunk_index,
                    section=section_override or doc.section,
                    topic_hint=doc.topic_hint,
                    transcript_version=transcript_version,
                )
            )
        return chunks

    def _build_text_chunks(self, *, text: str, chunk_size_chars: int, chunk_overlap_chars: int) -> list[str]:
        if self._chunker is not None:
            try:
                chunks = self._chunker.chunk_text(
                    text,
                    chunk_size_chars=chunk_size_chars,
                    chunk_overlap_chars=chunk_overlap_chars,
                )
                if chunks:
                    return [chunk for chunk in chunks if chunk.strip()]
            except Exception as exc:
                self._logger.warning(f"Semantic chunker failed, using char-window fallback: {exc}")
        return self._fallback_char_window_chunks(
            text=text,
            chunk_size_chars=chunk_size_chars,
            chunk_overlap_chars=chunk_overlap_chars,
        )

    @staticmethod
    def _fallback_char_window_chunks(*, text: str, chunk_size_chars: int, chunk_overlap_chars: int) -> list[str]:
        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size_chars, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)

            if end >= len(text):
                break
            start = max(0, end - chunk_overlap_chars)

        return chunks
