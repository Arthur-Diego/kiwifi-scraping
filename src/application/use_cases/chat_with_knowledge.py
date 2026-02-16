from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.llm import LLMPort
from src.application.ports.logger_port import LoggerPort
from src.application.ports.vector_store import VectorStorePort
from src.domain.knowledge.entities import ChatAnswer


@dataclass(frozen=True)
class ChatWithKnowledgeInput:
    query: str
    collection: str = "transcricoes"
    top_k: int = 8
    section: str | None = None
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7


class ChatWithKnowledgeUseCase:
    def __init__(
        self,
        *,
        vector_store: VectorStorePort,
        llm: LLMPort,
        logger: LoggerPort,
    ):
        self._vector_store = vector_store
        self._llm = llm
        self._logger = logger

    def execute(self, data: ChatWithKnowledgeInput) -> ChatAnswer:
        contexts = self._vector_store.search(
            data.query,
            collection=data.collection,
            top_k=data.top_k,
            section=data.section,
        )

        if not contexts:
            self._logger.warning("No supporting contexts found for query.")
            return ChatAnswer(
                answer=(
                    "Nao encontrei base nas transcricoes para afirmar isso com seguranca. "
                    "Envie mais detalhes ou refine sua pergunta."
                ),
                contexts=[],
            )

        answer = self._llm.generate_answer(
            query=data.query,
            contexts=contexts,
            model_name=data.model_name,
            temperature=data.temperature,
        )

        self._logger.info(f"Generated answer using {len(contexts)} retrieved context(s).")
        return ChatAnswer(answer=answer, contexts=contexts)
