import os
from dataclasses import dataclass
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class QdrantRetrieverConfig:
    url: str = "http://localhost:6333"
    collection: str = "transcricoes"
    embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"


class QdrantRetriever:
    """
    Responsável por:
    - Gerar embedding do query
    - Consultar o Qdrant
    - Retornar a lista de textos (payload["text"])
    """

    def __init__(
        self,
        config: Optional[QdrantRetrieverConfig] = None,
        *,
        client: Optional[QdrantClient] = None,
        embedder: Optional[SentenceTransformer] = None,
    ):
        env_cfg = QdrantRetrieverConfig(
            url=os.getenv("QDRANT_URL", QdrantRetrieverConfig.url),
            collection=os.getenv("QDRANT_COLLECTION", QdrantRetrieverConfig.collection),
            embedder_model=os.getenv("QDRANT_EMBEDDER_MODEL", QdrantRetrieverConfig.embedder_model),
        )
        self.config = config or env_cfg
        self.client = client or QdrantClient(self.config.url)
        self.embedder = embedder or SentenceTransformer(self.config.embedder_model)

    def search(self, query: str, *, top_k: int = 20, section: str | None = None) -> list[str]:
        vector = self.embedder.encode(query).tolist()
        query_filter = self._section_filter(section) if section else None

        hits = self.client.search(
            collection_name=self.config.collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=top_k,
        )

        results: list[str] = []
        for hit in hits:
            payload = getattr(hit, "payload", None)
            if not payload:
                continue
            text = payload.get("text")
            if text:
                results.append(text)

        print(f"✅ {len(results)} contextos retornados do Qdrant.\n")
        return results

    def get_all_sections(self) -> list[str]:
        sections: set[str] = set()
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=self.config.collection,
                limit=200,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for p in points:
                payload = getattr(p, "payload", None)
                if payload and payload.get("section"):
                    sections.add(payload["section"])
            if offset is None:
                break
        return sorted(sections)

    def delete_collection(self) -> None:
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.config.collection in collections:
                self.client.delete_collection(self.config.collection)
                print(f"✅ Coleção '{self.config.collection}' deletada com sucesso!")
            else:
                print(f"⚠️ Coleção '{self.config.collection}' não existe no Qdrant.")
        except Exception as e:
            print(f"❌ Erro ao tentar deletar coleção '{self.config.collection}': {e}")

    @staticmethod
    def _section_filter(section: str) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key="section",
                    match=MatchValue(value=section),
                )
            ]
        )


if __name__ == "__main__":
    QdrantRetriever().delete_collection()

