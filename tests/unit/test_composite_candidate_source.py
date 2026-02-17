from __future__ import annotations

from src.domain.product_mining.entities import ProductCandidate
from src.infrastructure.product_mining.composite_candidate_source import CompositeProductCandidateSource


class _SourceA:
    def source_name(self) -> str:
        return "a"

    def fetch_candidates(self) -> list[ProductCandidate]:
        return [
            ProductCandidate(
                product_key="p1",
                name="Prod",
                platform="ClickBank",
                price=47.0,
                extras={"a": 1},
            )
        ]


class _SourceB:
    def source_name(self) -> str:
        return "b"

    def fetch_candidates(self) -> list[ProductCandidate]:
        return [
            ProductCandidate(
                product_key="p1",
                name="Prod",
                platform="ClickBank",
                commission_pct=70.0,
                extras={"b": 2},
            )
        ]


def test_composite_merges_fields_and_extras() -> None:
    source = CompositeProductCandidateSource(sources=[_SourceA(), _SourceB()])
    items = source.fetch_candidates()
    assert len(items) == 1
    assert items[0].price == 47.0
    assert items[0].commission_pct == 70.0
    assert items[0].extras["a"] == 1
    assert items[0].extras["b"] == 2

