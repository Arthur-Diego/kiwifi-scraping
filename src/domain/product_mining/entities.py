from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ProductCandidate:
    product_key: str
    name: str
    platform: str
    category: str | None = None
    sales_page_url: str | None = None
    landing_page_type: str | None = None
    description: str | None = None
    price: float | None = None
    commission_pct: float | None = None
    gravity: float | None = None
    ranking: int | None = None
    refund_rate: float | None = None
    product_age_days: int | None = None
    keyword_volume: int | None = None
    trend_growth_30d: float | None = None
    social_engagement: float | None = None
    ads_competition_index: float | None = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductMiningResult:
    product_key: str
    product_name: str
    platform: str
    category: str | None
    sales_page_url: str | None
    price: float | None
    commission_pct: float | None
    gravity: float | None
    ranking: int | None
    refund_rate: float | None
    product_age_days: int | None
    keyword_volume: int | None
    trend_growth_30d: float | None
    social_engagement: float | None
    ads_competition_index: float | None
    buy_intent_score: float
    trend_score: float
    offer_score: float
    final_score: float
    classification: str
    rationale: dict[str, Any]
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class ProductMiningRunSummary:
    run_id: int
    source_name: str
    started_at: datetime
    candidates_count: int
    stored_count: int

