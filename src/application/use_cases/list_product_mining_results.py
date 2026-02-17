from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.product_mining_repository import ProductMiningRepositoryPort


@dataclass(frozen=True)
class ListProductMiningResultsInput:
    limit: int = 100
    classification: str | None = None
    platform: str | None = None


class ListProductMiningResultsUseCase:
    def __init__(self, *, repository: ProductMiningRepositoryPort):
        self._repository = repository

    def execute(self, data: ListProductMiningResultsInput) -> list[dict]:
        self._repository.ensure_schema()
        return self._repository.list_latest_results(
            limit=data.limit,
            classification=data.classification,
            platform=data.platform,
        )

