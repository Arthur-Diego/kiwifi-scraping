from __future__ import annotations

from typing import Protocol

from src.domain.knowledge.entities import KnowledgeChunk, RetrievedContext


class VectorStorePort(Protocol):
    def upsert_chunks(self, chunks: list[KnowledgeChunk], *, collection: str) -> None:
        ...

    def search(self, query: str, *, collection: str, top_k: int = 8, section: str | None = None) -> list[RetrievedContext]:
        ...

    def list_sections(self, *, collection: str) -> list[str]:
        ...

    def delete_collection(self, *, collection: str) -> None:
        ...
