from __future__ import annotations

from typing import Protocol

from src.domain.knowledge.entities import RetrievedContext


class LLMPort(Protocol):
    def generate_answer(
        self,
        *,
        query: str,
        contexts: list[RetrievedContext],
        model_name: str,
        temperature: float,
    ) -> str:
        ...
