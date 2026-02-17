from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from src.domain.product_mining.entities import ProductCandidate, ProductMiningResult

_BUY_INTENT_TERMS = (
    "comprar",
    "buy now",
    "inscreva-se",
    "adquira",
    "garantia",
    "checkout",
    "matricula",
    "matrícula",
    "desconto",
)

_DIRECT_SOLUTION_TERMS = (
    "passo a passo",
    "metodo",
    "método",
    "como",
    "resultado",
    "protocolo",
    "guia",
    "template",
)


def _safe_lower(value: str | None) -> str:
    return value.lower().strip() if value else ""


def _bounded(value: float, *, low: float = 0.0, high: float = 100.0) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def _count_keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    if not text:
        return 0
    hits = 0
    for keyword in keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE):
            hits += 1
    return hits


def score_product_candidate(candidate: ProductCandidate) -> ProductMiningResult:
    merged_text = " ".join(
        item for item in (candidate.name, candidate.description, candidate.landing_page_type, candidate.category) if item
    ).lower()

    intent_hits = _count_keyword_hits(merged_text, _BUY_INTENT_TERMS)
    solution_hits = _count_keyword_hits(merged_text, _DIRECT_SOLUTION_TERMS)
    is_direct_sales_page = 1.0 if "sales" in _safe_lower(candidate.landing_page_type) or "vsl" in _safe_lower(candidate.landing_page_type) else 0.0
    keyword_component = min(float(intent_hits) * 12.0, 30.0)
    solution_component = min(float(solution_hits) * 8.0, 20.0)
    buy_intent_score = _bounded(20.0 + keyword_component + solution_component + (30.0 * is_direct_sales_page))

    gravity_component = min((candidate.gravity or 0.0) / 2.0, 35.0)
    trend_component = min(max((candidate.trend_growth_30d or 0.0), 0.0) * 1.6, 35.0)
    keyword_volume_component = min((candidate.keyword_volume or 0) / 300.0, 20.0)
    social_component = min((candidate.social_engagement or 0.0) / 5.0, 10.0)
    trend_score = _bounded(gravity_component + trend_component + keyword_volume_component + social_component)

    commission_component = min((candidate.commission_pct or 0.0) * 0.5, 25.0)
    price_component = min((candidate.price or 0.0) / 8.0, 20.0)
    refund_penalty = min((candidate.refund_rate or 0.0) * 1.2, 30.0)
    competition_penalty = min((candidate.ads_competition_index or 0.0) * 0.25, 20.0)
    age_component = 8.0 if (candidate.product_age_days or 0) >= 30 else 3.0
    offer_score = _bounded(30.0 + commission_component + price_component + age_component - refund_penalty - competition_penalty)

    final_score = _bounded((buy_intent_score * 0.4) + (trend_score * 0.35) + (offer_score * 0.25))
    if final_score >= 75:
        classification = "ALTA_PRIORIDADE"
    elif final_score >= 55:
        classification = "TESTAR"
    else:
        classification = "BAIXA_PRIORIDADE"

    rationale: dict[str, Any] = {
        "buy_intent_hits": intent_hits,
        "solution_hits": solution_hits,
        "direct_sales_page": bool(is_direct_sales_page),
        "gravity_component": round(gravity_component, 2),
        "trend_component": round(trend_component, 2),
        "keyword_volume_component": round(keyword_volume_component, 2),
        "commission_component": round(commission_component, 2),
        "refund_penalty": round(refund_penalty, 2),
        "competition_penalty": round(competition_penalty, 2),
    }

    return ProductMiningResult(
        product_key=candidate.product_key,
        product_name=candidate.name,
        platform=candidate.platform,
        category=candidate.category,
        sales_page_url=candidate.sales_page_url,
        price=candidate.price,
        commission_pct=candidate.commission_pct,
        gravity=candidate.gravity,
        ranking=candidate.ranking,
        refund_rate=candidate.refund_rate,
        product_age_days=candidate.product_age_days,
        keyword_volume=candidate.keyword_volume,
        trend_growth_30d=candidate.trend_growth_30d,
        social_engagement=candidate.social_engagement,
        ads_competition_index=candidate.ads_competition_index,
        buy_intent_score=round(buy_intent_score, 2),
        trend_score=round(trend_score, 2),
        offer_score=round(offer_score, 2),
        final_score=round(final_score, 2),
        classification=classification,
        rationale=rationale,
        raw_payload=asdict(candidate),
    )

