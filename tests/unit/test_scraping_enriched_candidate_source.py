from __future__ import annotations

from src.domain.product_mining.entities import ProductCandidate
from src.infrastructure.product_mining.scraping_enriched_candidate_source import (
    ScrapingEnrichedProductCandidateSource,
    _extract_first_price,
    _infer_landing_page_type,
)


class _FakeSource:
    def source_name(self) -> str:
        return "fake"

    def fetch_candidates(self) -> list[ProductCandidate]:
        return [
            ProductCandidate(
                product_key="p1",
                name="Alpha Product",
                platform="ClickBank",
                sales_page_url=None,
            )
        ]


def test_extract_first_price_handles_formats() -> None:
    assert _extract_first_price("Oferta R$ 197,00 no checkout") == 197.0
    assert _extract_first_price("Buy now for $49.99") == 49.99
    assert _extract_first_price("Sem preco") is None


def test_infer_landing_page_type() -> None:
    assert _infer_landing_page_type("pagina com webinar ao vivo", 0) == "webinar"
    assert _infer_landing_page_type("video sales letter vsl", 0) == "direct-sales-vsl"
    assert _infer_landing_page_type("checkout comprar agora", 2) == "direct-sales-page"
    assert _infer_landing_page_type("artigo educacional", 0) == "content-page"


def test_enrichment_pipeline_fallback_without_url() -> None:
    source = ScrapingEnrichedProductCandidateSource(base_source=_FakeSource())
    items = source.fetch_candidates()
    assert len(items) == 1
    assert items[0].product_key == "p1"

