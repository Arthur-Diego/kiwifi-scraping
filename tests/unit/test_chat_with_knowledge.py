from __future__ import annotations

from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeInput, ChatWithKnowledgeUseCase
from src.domain.knowledge.entities import RetrievedContext


class FakeVectorStore:
    def __init__(self, contexts: list[RetrievedContext]):
        self._contexts = contexts

    def upsert_chunks(self, chunks, *, collection: str):
        raise NotImplementedError

    def search(self, query: str, *, collection: str, top_k: int = 8, section: str | None = None):
        _ = query
        _ = collection
        _ = top_k
        _ = section
        return self._contexts

    def list_sections(self, *, collection: str):
        raise NotImplementedError

    def delete_collection(self, *, collection: str):
        raise NotImplementedError


class FakeLLM:
    def generate_answer(self, *, query: str, contexts, model_name: str, temperature: float) -> str:
        _ = query
        _ = model_name
        _ = temperature
        return f"ok:{len(contexts)}"


class FakeLogger:
    def info(self, message: str) -> None:
        _ = message

    def warning(self, message: str) -> None:
        _ = message

    def error(self, message: str) -> None:
        _ = message


def test_chat_returns_fallback_without_contexts() -> None:
    use_case = ChatWithKnowledgeUseCase(vector_store=FakeVectorStore([]), llm=FakeLLM(), logger=FakeLogger())
    result = use_case.execute(ChatWithKnowledgeInput(query="teste"))
    assert "Nao encontrei base" in result.answer


def test_chat_calls_llm_with_contexts() -> None:
    contexts = [RetrievedContext(text="ctx", source_file="a", source_path="a", chunk_index=0)]
    use_case = ChatWithKnowledgeUseCase(vector_store=FakeVectorStore(contexts), llm=FakeLLM(), logger=FakeLogger())
    result = use_case.execute(ChatWithKnowledgeInput(query="teste"))
    assert result.answer == "ok:1"
