from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

_INT_FIELDS = {"impressions", "clicks", "conversions"}
_PERCENT_FIELDS = {"ctr", "conversion_rate"}
_NUMERIC_FIELDS = {
    "impressions",
    "clicks",
    "ctr",
    "conversions",
    "cost_per_conversion",
    "conversion_rate",
    "total_cost",
    "daily_budget",
    "cpc",
}
_TEXT_FIELDS = {"demographic_data", "device_data", "ad_performance", "trends", "keyword_data"}

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "impressions": ("impressions", "impressao", "impressoes", "impressões"),
    "clicks": ("clicks", "cliques", "clique"),
    "ctr": ("ctr",),
    "conversions": ("conversions", "conversao", "conversoes", "conversão", "conversões"),
    "cost_per_conversion": ("cost_per_conversion", "cost per conversion", "custo por conversao", "custo por conversão", "cpa"),
    "conversion_rate": ("conversion_rate", "conversion rate", "taxa de conversao", "taxa de conversão"),
    "total_cost": ("total_cost", "total cost", "custo total", "gasto total", "investimento"),
    "daily_budget": ("daily_budget", "daily budget", "orcamento diario", "orçamento diário"),
    "cpc": ("cpc", "custo por clique"),
    "keyword_data": ("keyword_data", "keywords", "palavras chave", "palavras-chave"),
    "demographic_data": ("demographic_data", "demografia", "dados demograficos", "dados demográficos"),
    "device_data": ("device_data", "dispositivos", "dados de dispositivos"),
    "ad_performance": ("ad_performance", "ad performance", "performance dos anuncios", "performance dos anúncios"),
    "trends": ("trends", "tendencias", "tendências"),
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _parse_number(raw: str, *, is_percent_field: bool) -> float | None:
    match = re.search(r"[-+]?\d[\d\.,]*", raw)
    if not match:
        return None
    token = match.group(0)

    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        token = token.replace(",", ".")

    try:
        value = float(token)
    except ValueError:
        return None

    if "%" in raw and is_percent_field:
        return value
    return value


def _value_from_label_value_pairs(prompt: str) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    key_to_field: dict[str, str] = {}
    for field, aliases in _FIELD_ALIASES.items():
        for alias in aliases:
            key_to_field[_normalize(alias)] = field

    parts = re.split(r"[\n;|]+", prompt)
    for raw_part in parts:
        part = raw_part.strip()
        if not part or (":" not in part and "=" not in part):
            continue

        sep = ":" if ":" in part else "="
        key, value = part.split(sep, 1)
        key_norm = _normalize(key)
        field = key_to_field.get(key_norm)
        if not field:
            continue

        clean_value = value.strip()
        if not clean_value:
            continue

        if field in _NUMERIC_FIELDS:
            number = _parse_number(clean_value, is_percent_field=field in _PERCENT_FIELDS)
            if number is None:
                continue
            extracted[field] = int(number) if field in _INT_FIELDS else float(number)
            continue

        if field == "keyword_data":
            if clean_value.startswith("[") or clean_value.startswith("{"):
                try:
                    extracted[field] = json.loads(clean_value)
                except json.JSONDecodeError:
                    extracted[field] = clean_value
            else:
                extracted[field] = clean_value
            continue

        if field == "trends":
            if clean_value.startswith("["):
                try:
                    extracted[field] = json.loads(clean_value)
                except json.JSONDecodeError:
                    extracted[field] = clean_value
            else:
                extracted[field] = clean_value
            continue

        if field in _TEXT_FIELDS:
            extracted[field] = clean_value

    return extracted


def _extract_number_from_text(prompt: str, aliases: tuple[str, ...], *, is_percent_field: bool) -> float | None:
    for alias in aliases:
        alias_re = re.escape(alias)
        after_alias = re.search(rf"{alias_re}\D{{0,24}}([-+]?\d[\d\.,]*%?)", prompt, flags=re.IGNORECASE)
        if after_alias:
            value = _parse_number(after_alias.group(1), is_percent_field=is_percent_field)
            if value is not None:
                return value

        before_alias = re.search(rf"([-+]?\d[\d\.,]*%?)\D{{0,24}}{alias_re}", prompt, flags=re.IGNORECASE)
        if before_alias:
            value = _parse_number(before_alias.group(1), is_percent_field=is_percent_field)
            if value is not None:
                return value
    return None


def extract_campaign_metrics_from_prompt(prompt: str) -> dict[str, Any]:
    """
    Extracts metrics-like fields from a free-form prompt and maps them to PostgreSQL columns.
    """
    if not prompt or not prompt.strip():
        return {}

    metrics = _value_from_label_value_pairs(prompt)
    normalized_prompt = _normalize(prompt)

    for field in _NUMERIC_FIELDS:
        if field in metrics:
            continue
        aliases = _FIELD_ALIASES[field]
        value = _extract_number_from_text(
            normalized_prompt,
            tuple(_normalize(alias) for alias in aliases),
            is_percent_field=field in _PERCENT_FIELDS,
        )
        if value is None:
            continue
        metrics[field] = int(value) if field in _INT_FIELDS else float(value)

    return metrics

