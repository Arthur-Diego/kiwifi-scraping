from typing import Iterable
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from .domain import Chunk
from .embeddings import SentenceEmbedder
from .config import QdrantConfig

class QdrantRepository:
    """
    SRP: isolar a persistência Qdrant (criação de coleção e upsert de pontos).
    Princípios SOLID:
      - SRP: apenas lida com Qdrant
      - OCP: extensível para outros backends com uma interface semelhante
      - DIP: depende de abstrações (Chunk, SentenceEmbedder), não de detalhes
    """
    def __init__(self, cfg: QdrantConfig, embedder: SentenceEmbedder):
        self.cfg = cfg
        self.embedder = embedder
        self.client = QdrantClient(host=cfg.host, port=cfg.port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.cfg.collection not in collections:
            self.client.create_collection(
                collection_name=self.cfg.collection,
                vectors_config=VectorParams(
                    size=self.embedder.dim,
                    distance=Distance.COSINE
                )
            )

    def upsert_chunks(self, chunks: Iterable[Chunk], batch_size: int = 128) -> None:
        batch_texts = []
        batch_points = []
        ids = []
        payloads = []

        def flush():
            if not batch_texts:
                return
            embs = self.embedder.encode(batch_texts)  # [N, D]
            points = [
                PointStruct(
                    id=ids[i],
                    vector=embs[i].tolist(),
                    payload=payloads[i],
                ) for i in range(len(batch_texts))
            ]
            self.client.upsert(collection_name=self.cfg.collection, points=points)
            batch_texts.clear(); batch_points.clear(); ids.clear(); payloads.clear()

        for c in chunks:
            ids.append(c.id)
            batch_texts.append(c.text)
            payloads.append({
                "source": c.source,
                "chunk_index": c.chunk_index,
                "token_count": c.token_count,
                "date": c.date,
                "section": c.section,
                "start_sentence": c.start_sentence,
                "end_sentence": c.end_sentence
            })
            if len(batch_texts) >= batch_size:
                flush()

        flush()
