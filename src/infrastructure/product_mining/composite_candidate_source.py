from __future__ import annotations

from dataclasses import replace

from src.application.ports.product_candidate_source import ProductCandidateSourcePort
from src.domain.product_mining.entities import ProductCandidate


class CompositeProductCandidateSource:
    """
    Merges candidates from multiple sources by product_key.
    Later sources override missing/conflicting fields from earlier sources.
    """

    def __init__(self, *, sources: list[ProductCandidateSourcePort]):
        self._sources = sources

    def source_name(self) -> str:
        return "+".join(source.source_name() for source in self._sources) if self._sources else "empty-source"

    def fetch_candidates(self) -> list[ProductCandidate]:
        merged: dict[str, ProductCandidate] = {}
        order: list[str] = []
        for source in self._sources:
            for item in source.fetch_candidates():
                if item.product_key not in merged:
                    merged[item.product_key] = item
                    order.append(item.product_key)
                else:
                    merged[item.product_key] = _merge_candidate(merged[item.product_key], item)
        return [merged[key] for key in order]


def _merge_candidate(base: ProductCandidate, incoming: ProductCandidate) -> ProductCandidate:
    extras = dict(base.extras)
    extras.update(incoming.extras or {})
    patch = {
        "name": incoming.name or base.name,
        "platform": incoming.platform or base.platform,
        "category": incoming.category if incoming.category is not None else base.category,
        "sales_page_url": incoming.sales_page_url if incoming.sales_page_url is not None else base.sales_page_url,
        "landing_page_type": incoming.landing_page_type if incoming.landing_page_type is not None else base.landing_page_type,
        "description": incoming.description if incoming.description is not None else base.description,
        "price": incoming.price if incoming.price is not None else base.price,
        "commission_pct": incoming.commission_pct if incoming.commission_pct is not None else base.commission_pct,
        "gravity": incoming.gravity if incoming.gravity is not None else base.gravity,
        "ranking": incoming.ranking if incoming.ranking is not None else base.ranking,
        "refund_rate": incoming.refund_rate if incoming.refund_rate is not None else base.refund_rate,
        "product_age_days": incoming.product_age_days if incoming.product_age_days is not None else base.product_age_days,
        "keyword_volume": incoming.keyword_volume if incoming.keyword_volume is not None else base.keyword_volume,
        "trend_growth_30d": incoming.trend_growth_30d if incoming.trend_growth_30d is not None else base.trend_growth_30d,
        "social_engagement": incoming.social_engagement if incoming.social_engagement is not None else base.social_engagement,
        "ads_competition_index": (
            incoming.ads_competition_index if incoming.ads_competition_index is not None else base.ads_competition_index
        ),
    }
    return replace(base, extras=extras, **patch)

