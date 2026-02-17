from __future__ import annotations

from typing import Protocol

from src.domain.product_mining.entities import ProductMiningResult, ProductMiningRunSummary


class ProductMiningRepositoryPort(Protocol):
    def ensure_schema(self) -> None:
        ...

    def create_run(self, *, source_name: str, candidates_count: int) -> int:
        ...

    def save_result(self, *, run_id: int, result: ProductMiningResult) -> None:
        ...

    def list_latest_results(
        self,
        *,
        limit: int = 100,
        classification: str | None = None,
        platform: str | None = None,
    ) -> list[dict]:
        ...

    def list_recent_runs(self, *, limit: int = 20) -> list[ProductMiningRunSummary]:
        ...

