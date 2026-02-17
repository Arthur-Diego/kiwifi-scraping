from __future__ import annotations

import json
from pathlib import Path

from src.domain.product_mining.entities import ProductCandidate


class LocalProductCandidateSource:
    """
    Reads product candidates from a local JSON file.

    This keeps the MVP independent from external APIs/scraping while preserving
    the same flow and storage model for future connectors (Google Trends, ClickBank, etc.).
    """

    def __init__(self, *, source_file: Path):
        self._source_file = source_file

    def source_name(self) -> str:
        return f"local-json:{self._source_file}"

    def fetch_candidates(self) -> list[ProductCandidate]:
        if not self._source_file.exists():
            return []
        raw = json.loads(self._source_file.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []

        candidates: list[ProductCandidate] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            product_key = str(item.get("product_key") or item.get("id") or "").strip()
            name = str(item.get("name") or "").strip()
            platform = str(item.get("platform") or "").strip()
            if not product_key or not name or not platform:
                continue
            candidates.append(
                ProductCandidate(
                    product_key=product_key,
                    name=name,
                    platform=platform,
                    category=_text(item.get("category")),
                    sales_page_url=_text(item.get("sales_page_url")),
                    landing_page_type=_text(item.get("landing_page_type")),
                    description=_text(item.get("description")),
                    price=_to_float(item.get("price")),
                    commission_pct=_to_float(item.get("commission_pct")),
                    gravity=_to_float(item.get("gravity")),
                    ranking=_to_int(item.get("ranking")),
                    refund_rate=_to_float(item.get("refund_rate")),
                    product_age_days=_to_int(item.get("product_age_days")),
                    keyword_volume=_to_int(item.get("keyword_volume")),
                    trend_growth_30d=_to_float(item.get("trend_growth_30d")),
                    social_engagement=_to_float(item.get("social_engagement")),
                    ads_competition_index=_to_float(item.get("ads_competition_index")),
                    extras=item.get("extras") if isinstance(item.get("extras"), dict) else {},
                )
            )
        return candidates


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None

