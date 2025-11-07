# rag_qdrant/rag_query.py
from repository.qdrant_repository import QdrantRetriever
from llm.llm_client import LLMClient

def run_rag(query: str):
    retriever = QdrantRetriever()
    results = retriever.search(query, top_k=20)

    # 🔧 Corrige: extrai só o texto se vier em dicionário
    contexts = []
    for r in results:
        if isinstance(r, dict) and "text" in r:
            contexts.append(r["text"])
        elif isinstance(r, str):
            contexts.append(r)
        else:
            print(f"⚠️ Formato inesperado do resultado: {type(r)}")

    print(f"✅ {len(contexts)} contextos extraídos com sucesso.\n")

    llm = LLMClient()
    return llm.generate(query, contexts)



if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ Uso: python -m service.rag_service \"Me traga um overview da analise de métrica\"")
        exit(1)

    query = " ".join(sys.argv[1:])
    print(f"\n🔍 Pergunta: {query}\n")

    answer = run_rag(query)
    print("💡 Resposta:\n")
    print(answer)
