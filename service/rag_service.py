from llm.llm_client import LLMClient
from repository.qdrant_repository import QdrantRetriever


def run_rag(
    query: str,
    *,
    top_k: int = 20,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.7,
    section: str | None = None,
    retriever: QdrantRetriever | None = None,
) -> str:
    """
    Executa RAG:
    - busca contextos no Qdrant
    - gera resposta via LLM
    """
    retriever = retriever or QdrantRetriever()
    contexts = retriever.search(query, top_k=top_k, section=section)
    return run_rag_with_context(query, contexts, model_name=model_name, temperature=temperature)


def run_rag_with_context(
    query: str,
    contexts: list[str],
    *,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> str:
    """
    Variante onde os contextos já vêm prontos (ex.: filtrados por section).
    """
    print(f"🎯 Rodando RAG com {len(contexts)} contextos.\n")
    llm = LLMClient(model_name=model_name, temperature=temperature)
    return llm.generate(query, contexts)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print('❌ Uso: python3 -m service.rag_service "Me traga um overview da analise de métrica"')
        raise SystemExit(1)

    q = " ".join(sys.argv[1:])
    print(f"\n🔍 Pergunta: {q}\n")
    print("💡 Resposta:\n")
    print(run_rag(q))

