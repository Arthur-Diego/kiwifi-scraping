from __future__ import annotations

import math
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from qdrant_client.http.models import NearestQuery
from sentence_transformers import SentenceTransformer

from src.domain.knowledge.entities import KnowledgeChunk, RetrievedContext


class QdrantVectorStore:
    def __init__(self, *, qdrant_url: str, embedder_model: str | None = None, embedder: SentenceTransformer | None = None):
        if embedder is None and not embedder_model:
            raise ValueError("Provide either `embedder` or `embedder_model`.")
        self._client = QdrantClient(url=qdrant_url)
        self._embedder = embedder or SentenceTransformer(str(embedder_model))

    def upsert_chunks(self, chunks: list[KnowledgeChunk], *, collection: str) -> None:
        if not chunks:
            return

        self._ensure_collection(collection=collection)

        batch_size = 128
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [chunk.text for chunk in batch]
            vectors = self._embedder.encode(texts, batch_size=64, convert_to_numpy=True, normalize_embeddings=True)

            points: list[PointStruct] = []
            for idx, chunk in enumerate(batch):
                points.append(
                    PointStruct(
                        id=chunk.chunk_id if chunk.chunk_id else str(uuid.uuid4()),
                        vector=vectors[idx].tolist(),
                        payload={
                            "text": chunk.text,
                            "source_file": chunk.source_file,
                            "source_path": chunk.source_path,
                            "chunk_index": chunk.chunk_index,
                            "section": chunk.section,
                            "topic_hint": chunk.topic_hint,
                            "transcript_version": chunk.transcript_version,
                        },
                    )
                )

            self._client.upsert(collection_name=collection, points=points)

    def search(self, query: str, *, collection: str, top_k: int = 8, section: str | None = None) -> list[RetrievedContext]:
        query_vector = self._embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].tolist()
        query_filter = self._build_section_filter(section)
        self._validate_query_dim(collection=collection, query_vector=query_vector)
        hits = self._search_points(
            collection=collection,
            query_vector=query_vector,
            query_filter=query_filter,
            top_k=top_k,
        )

        output: list[RetrievedContext] = []
        for hit in hits:
            payload = hit.payload or {}
            text = payload.get("text")
            if not text:
                continue
            output.append(
                RetrievedContext(
                    text=text,
                    source_file=payload.get("source_file", "unknown"),
                    source_path=payload.get("source_path", "unknown"),
                    chunk_index=int(payload.get("chunk_index", -1)),
                    section=payload.get("section"),
                    topic_hint=payload.get("topic_hint"),
                    score=getattr(hit, "score", None),
                )
            )
        return output

    def _search_points(
        self,
        *,
        collection: str,
        query_vector: list[float],
        query_filter: Filter | None,
        top_k: int,
    ) -> list:
        # qdrant-client API changed across versions:
        # - older: client.search(...)
        # - newer: client.query_points(...)
        if hasattr(self._client, "search"):
            return self._client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
            )

        try:
            query_result = self._client.query_points(
                collection_name=collection,
                query=NearestQuery(nearest=query_vector),
                query_filter=query_filter,
                limit=top_k,
                with_vectors=False,
            )
        except UnexpectedResponse as exc:
            raw = str(exc)
            if "OutputTooSmall" in raw or "Internal Server Error" in raw:
                return self._search_points_fallback_by_scroll(
                    collection=collection,
                    query_vector=query_vector,
                    section_value=self._extract_section_value(query_filter),
                    top_k=top_k,
                )
            raise

        points = getattr(query_result, "points", None)
        if points is None:
            return []
        return points

    def _search_points_fallback_by_scroll(
        self,
        *,
        collection: str,
        query_vector: list[float],
        section_value: str | None,
        top_k: int,
    ) -> list:
        # Fallback robusto inspirado no comportamento estável legado:
        # varre pontos no Qdrant e calcula similaridade localmente.
        candidates: list[tuple[float, object]] = []
        offset = None

        while True:
            points, offset = self._client.scroll(
                collection_name=collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            for point in points:
                payload = getattr(point, "payload", None) or {}
                if section_value and payload.get("section") != section_value:
                    continue

                vector = self._extract_vector(point)
                if not vector:
                    continue

                score = self._cosine(query_vector, vector)
                candidates.append((score, point))

            if offset is None:
                break

        candidates.sort(key=lambda item: item[0], reverse=True)
        top_points = []
        for score, point in candidates[:top_k]:
            setattr(point, "score", score)
            top_points.append(point)
        return top_points

    @staticmethod
    def _extract_vector(point: object) -> list[float] | None:
        vector = getattr(point, "vector", None)
        if vector is None:
            return None
        if isinstance(vector, list):
            return [float(v) for v in vector]
        # named vectors format
        if isinstance(vector, dict):
            for _, value in vector.items():
                if isinstance(value, list):
                    return [float(v) for v in value]
        return None

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _extract_section_value(query_filter: Filter | None) -> str | None:
        if query_filter is None:
            return None
        must_items = getattr(query_filter, "must", None) or []
        for item in must_items:
            key = getattr(item, "key", None)
            match = getattr(item, "match", None)
            value = getattr(match, "value", None)
            if key == "section" and isinstance(value, str):
                return value
        return None

    def _validate_query_dim(self, *, collection: str, query_vector: list[float]) -> None:
        info = self._client.get_collection(collection)
        vectors_cfg = getattr(info.config.params, "vectors", None)
        expected_size = getattr(vectors_cfg, "size", None)
        if expected_size is None:
            return
        if len(query_vector) != int(expected_size):
            raise ValueError(
                f"Dimensão do vetor de consulta ({len(query_vector)}) difere da coleção "
                f"'{collection}' ({expected_size}). Verifique modelo de embedding e reindexação."
            )

    def list_sections(self, *, collection: str) -> list[str]:
        sections: set[str] = set()
        offset = None
        while True:
            points, offset = self._client.scroll(
                collection_name=collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                section = payload.get("section")
                if section:
                    sections.add(section)
            if offset is None:
                break
        return sorted(sections)

    def delete_collection(self, *, collection: str) -> None:
        collections = [item.name for item in self._client.get_collections().collections]
        if collection in collections:
            self._client.delete_collection(collection_name=collection)

    def _ensure_collection(self, *, collection: str) -> None:
        collections = [item.name for item in self._client.get_collections().collections]
        if collection in collections:
            return

        vector_dim = int(self._embedder.get_sentence_embedding_dimension())
        self._client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
        )

    @staticmethod
    def _build_section_filter(section: str | None) -> Filter | None:
        if not section:
            return None
        return Filter(
            must=[FieldCondition(key="section", match=MatchValue(value=section))],
        )
