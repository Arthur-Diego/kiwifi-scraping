from __future__ import annotations

import concurrent.futures
import html
import re
from dataclasses import replace
from typing import Iterable
from urllib.parse import quote_plus

import requests
try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore[assignment]

from src.application.ports.product_candidate_source import ProductCandidateSourcePort
from src.domain.product_mining.entities import ProductCandidate

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


class ScrapingEnrichedProductCandidateSource:
    """
    Wraps a base candidate source and enriches products with scraped signals.

    Enrichments:
    - sales page scraping (title/description/cta/price hints + landing page type)
    - trend proxy from Google Trends daily RSS
    - Google suggest proxy (query breadth / demand intent)
    """

    def __init__(
        self,
        *,
        base_source: ProductCandidateSourcePort,
        timeout_seconds: float = 12.0,
        max_workers: int = 6,
    ):
        self._base_source = base_source
        self._timeout_seconds = timeout_seconds
        self._max_workers = max_workers

    def source_name(self) -> str:
        return f"{self._base_source.source_name()}+scraping"

    def fetch_candidates(self) -> list[ProductCandidate]:
        base_candidates = self._base_source.fetch_candidates()
        if not base_candidates:
            return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {pool.submit(self._enrich_candidate, item): item for item in base_candidates}
            enriched: list[ProductCandidate] = []
            for fut in concurrent.futures.as_completed(futures.keys()):
                original = futures[fut]
                try:
                    enriched.append(fut.result())
                except Exception:
                    # Keep pipeline resilient: if enrichment fails, fallback to base item.
                    enriched.append(original)

        # Preserve original order as much as possible by product key.
        enriched_by_key = {item.product_key: item for item in enriched}
        output: list[ProductCandidate] = []
        for item in base_candidates:
            output.append(enriched_by_key.get(item.product_key, item))
        return output

    def _enrich_candidate(self, candidate: ProductCandidate) -> ProductCandidate:
        merged = candidate
        sales_page_data = self._scrape_sales_page(candidate.sales_page_url)
        if sales_page_data:
            merged = self._merge_candidate(merged, sales_page_data)

        trend_data = self._scrape_google_trend_signal(candidate.name)
        if trend_data:
            merged = self._merge_candidate(merged, trend_data)
        suggest_data = self._scrape_google_suggest_signal(candidate.name)
        if suggest_data:
            merged = self._merge_candidate(merged, suggest_data)
        return merged

    def _merge_candidate(self, original: ProductCandidate, patch: dict) -> ProductCandidate:
        extras = dict(original.extras)
        extras_patch = patch.pop("extras", None)
        if isinstance(extras_patch, dict):
            extras.update(extras_patch)
        updated = replace(original, extras=extras, **{k: v for k, v in patch.items() if hasattr(original, k)})
        return updated

    def _scrape_sales_page(self, sales_page_url: str | None) -> dict:
        if not sales_page_url:
            return {}
        try:
            response = requests.get(
                sales_page_url,
                timeout=self._timeout_seconds,
                headers=_DEFAULT_HEADERS,
                allow_redirects=True,
            )
            response.raise_for_status()
        except Exception as exc:
            return {"extras": {"scrape_sales_page_error": str(exc)[:300]}}

        title, meta_desc, body_text = _extract_html_fields(response.text)
        body_text_l = body_text.lower()
        cta_hits = _count_occurrences(
            body_text_l,
            (
                "compre agora",
                "buy now",
                "checkout",
                "garantia",
                "inscreva-se",
                "adquirir",
                "matricule-se",
            ),
        )
        extracted_price = _extract_first_price(body_text)
        inferred_type = _infer_landing_page_type(body_text_l, cta_hits)

        patch: dict = {
            "description": meta_desc or title,
            "landing_page_type": inferred_type,
            "price": extracted_price,
            "extras": {
                "scraped_title": title,
                "scraped_cta_hits": cta_hits,
                "scraped_url": sales_page_url,
            },
        }
        return {k: v for k, v in patch.items() if v is not None}

    def _scrape_google_trend_signal(self, product_name: str) -> dict:
        # Public RSS endpoint with daily trends; used as low-cost trend signal proxy.
        # https://trends.google.com/trending?geo=US
        rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        try:
            response = requests.get(rss_url, timeout=self._timeout_seconds, headers=_DEFAULT_HEADERS)
            response.raise_for_status()
        except Exception as exc:
            return {"extras": {"scrape_trends_error": str(exc)[:300]}}

        entries = _extract_rss_items_text(response.text)
        product_tokens = [tok for tok in re.findall(r"[a-zA-Z0-9]{3,}", product_name.lower()) if len(tok) >= 4]
        if not entries or not product_tokens:
            return {}

        matches = 0
        for entry in entries:
            if any(tok in entry for tok in product_tokens):
                matches += 1

        # Proxy: each match in daily trend feed increases trend growth signal.
        proxy_growth = float(matches * 6.0)
        return {
            "trend_growth_30d": proxy_growth,
            "extras": {
                "trend_matches_daily_rss": matches,
                "trend_tokens": product_tokens,
                "trend_source_url": rss_url,
                "trend_probe": f"https://www.google.com/search?q={quote_plus(product_name)}",
            },
        }

    def _scrape_google_suggest_signal(self, product_name: str) -> dict:
        suggest_url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "firefox", "q": product_name, "hl": "en"}
        try:
            response = requests.get(
                suggest_url,
                params=params,
                timeout=self._timeout_seconds,
                headers=_DEFAULT_HEADERS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            return {"extras": {"scrape_suggest_error": str(exc)[:300]}}

        suggestions: list[str] = []
        if isinstance(payload, list) and len(payload) >= 2 and isinstance(payload[1], list):
            suggestions = [str(x).strip() for x in payload[1] if str(x).strip()]
        suggestion_count = len(suggestions)
        if suggestion_count == 0:
            return {}

        keyword_volume_proxy = max(500, suggestion_count * 1200)
        competition_proxy = min(100.0, suggestion_count * 11.5)
        return {
            "keyword_volume": keyword_volume_proxy,
            "ads_competition_index": competition_proxy,
            "extras": {
                "suggestions_count": suggestion_count,
                "suggestions_sample": suggestions[:8],
                "suggest_source_url": suggest_url,
            },
        }


def _count_occurrences(text: str, terms: Iterable[str]) -> int:
    hits = 0
    for term in terms:
        if term in text:
            hits += 1
    return hits


def _extract_first_price(text: str) -> float | None:
    # Matches $97, 97.00, R$ 197,00 etc.
    patterns = [
        r"(?:r\$\s*|\$\s*)(\d{1,4}(?:[\.,]\d{2})?)",
        r"\b(\d{1,4}(?:[\.,]\d{2}))\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        raw = match.group(1).replace(".", "").replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            continue
        if 5.0 <= value <= 5000.0:
            return value
    return None


def _infer_landing_page_type(text_l: str, cta_hits: int) -> str:
    if "webinar" in text_l:
        return "webinar"
    if "vsl" in text_l or "video sales letter" in text_l:
        return "direct-sales-vsl"
    if cta_hits >= 2 or "checkout" in text_l:
        return "direct-sales-page"
    return "content-page"


def _extract_html_fields(html_text: str) -> tuple[str | None, str | None, str]:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html_text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title and soup.title.string else None
        meta_desc = None
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            meta_desc = str(meta.get("content")).strip()
        body_text = " ".join(part.strip() for part in soup.get_text(" ").split() if part.strip())
        return title, meta_desc, body_text

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    title = html.unescape(title_match.group(1).strip()) if title_match else None
    meta_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    meta_desc = html.unescape(meta_match.group(1).strip()) if meta_match else None
    text = re.sub(r"<script[\s\S]*?</script>", " ", html_text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    body_text = " ".join(html.unescape(text).split())
    return title, meta_desc, body_text


def _extract_rss_items_text(xml_text: str) -> list[str]:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(xml_text, "xml")
        return [item.get_text(" ", strip=True).lower() for item in soup.find_all("item")]
    matches = re.findall(r"<item>([\s\S]*?)</item>", xml_text, flags=re.IGNORECASE)
    items: list[str] = []
    for chunk in matches:
        text = re.sub(r"<[^>]+>", " ", chunk)
        items.append(" ".join(html.unescape(text).split()).lower())
    return items
