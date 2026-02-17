from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.ports.logger_port import LoggerPort
from src.application.ports.product_candidate_source import ProductCandidateSourcePort
from src.application.ports.product_mining_repository import ProductMiningRepositoryPort
from src.application.services.product_mining_scorer import score_product_candidate
from src.domain.product_mining.entities import ProductMiningRunSummary


@dataclass(frozen=True)
class RunProductMiningBatchOutput:
    run_summary: ProductMiningRunSummary
    top_results: list[dict]


class RunProductMiningBatchUseCase:
    def __init__(
        self,
        *,
        source: ProductCandidateSourcePort,
        repository: ProductMiningRepositoryPort,
        logger: LoggerPort,
    ):
        self._source = source
        self._repository = repository
        self._logger = logger

    def execute(self) -> RunProductMiningBatchOutput:
        self._repository.ensure_schema()
        candidates = self._source.fetch_candidates()
        run_id = self._repository.create_run(source_name=self._source.source_name(), candidates_count=len(candidates))
        self._logger.info(f"Product mining source={self._source.source_name()} candidates={len(candidates)}")

        for candidate in candidates:
            result = score_product_candidate(candidate)
            self._repository.save_result(run_id=run_id, result=result)

        self._logger.info(f"Product mining batch run={run_id} processed={len(candidates)}")
        runs = self._repository.list_recent_runs(limit=1)
        summary = runs[0] if runs else ProductMiningRunSummary(
            run_id=run_id,
            source_name=self._source.source_name(),
            started_at=datetime.now(timezone.utc),
            candidates_count=len(candidates),
            stored_count=len(candidates),
        )
        return RunProductMiningBatchOutput(
            run_summary=summary,
            top_results=self._repository.list_latest_results(limit=10),
        )
