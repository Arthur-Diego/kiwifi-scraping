from __future__ import annotations

from typing import Protocol

from src.domain.product_mining.entities import ProductCandidate


class ProductCandidateSourcePort(Protocol):
    def source_name(self) -> str:
        ...

    def fetch_candidates(self) -> list[ProductCandidate]:
        ...

