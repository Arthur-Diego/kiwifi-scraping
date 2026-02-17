from __future__ import annotations

from src.application.services.product_mining_scorer import score_product_candidate
from src.domain.product_mining.entities import ProductCandidate


def test_product_mining_scorer_high_priority() -> None:
    candidate = ProductCandidate(
        product_key="p1",
        name="Metodo Comprar Melhor",
        platform="ClickBank",
        category="Health",
        landing_page_type="direct-sales-vsl",
        description="Compre agora com garantia e checkout.",
        price=97.0,
        commission_pct=75.0,
        gravity=70.0,
        refund_rate=8.0,
        keyword_volume=12000,
        trend_growth_30d=15.0,
        social_engagement=60.0,
        ads_competition_index=55.0,
        product_age_days=180,
    )
    result = score_product_candidate(candidate)
    assert result.classification in {"ALTA_PRIORIDADE", "TESTAR"}
    assert result.final_score > 60


def test_product_mining_scorer_low_priority() -> None:
    candidate = ProductCandidate(
        product_key="p2",
        name="Curso Generico",
        platform="ClickBank",
        category="General",
        landing_page_type="blog-post",
        description="Conteudo geral sem oferta direta.",
        price=19.0,
        commission_pct=20.0,
        gravity=10.0,
        refund_rate=25.0,
        keyword_volume=800,
        trend_growth_30d=-1.0,
        social_engagement=8.0,
        ads_competition_index=70.0,
        product_age_days=10,
    )
    result = score_product_candidate(candidate)
    assert result.classification == "BAIXA_PRIORIDADE"
    assert result.final_score < 55

