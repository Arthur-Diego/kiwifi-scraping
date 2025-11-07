from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class QdrantRetriever:
    def __init__(self):
        self.client = QdrantClient("http://localhost:6333")
        self.collection = "transcricoes"
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def search(self, query: str, top_k: int = 20):
        # 🔹 Cria embedding da consulta
        vector = self.embedder.encode(query).tolist()

        # 🔹 Faz busca vetorial no Qdrant
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k
        )

        results = []
        for hit in hits:
            payload = getattr(hit, "payload", None)
            if payload:
                text = payload.get("text", None)
                if text:
                    results.append(text)
                else:
                    print(f"⚠️ Payload sem campo 'text': {payload.keys()}")
            else:
                print(f"⚠️ Resultado sem payload: {hit}")

        print(f"✅ {len(results)} contextos retornados do Qdrant.\n")
        return results

    def delete_collection(self):
        """Remove completamente a coleção do Qdrant"""
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection in collections:
                self.client.delete_collection(self.collection)
                print(f"✅ Coleção '{self.collection}' deletada com sucesso!")
            else:
                print(f"⚠️ Coleção '{self.collection}' não existe no Qdrant.")
        except Exception as e:
            print(f"❌ Erro ao tentar deletar coleção '{self.collection}': {e}")

if __name__ == "__main__":
    retriever = QdrantRetriever()
    retriever.delete_collection()


