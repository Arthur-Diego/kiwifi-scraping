from repository.qdrant_repository import QdrantRetriever


class QdrantSectionRepository:
    """
    Wrapper para manter a API atual, delegando a implementação para QdrantRetriever.
    """

    def __init__(self):
        self.retriever = QdrantRetriever()

    def get_all_sections(self) -> list[str]:
        return self.retriever.get_all_sections()

    def search_by_section(self, query: str, section: str, top_k: int = 20) -> list[str]:
        results = self.retriever.search(query, top_k=top_k, section=section)
        print(f"🎯 {len(results)} contextos retornados da section '{section}'.")
        return results

