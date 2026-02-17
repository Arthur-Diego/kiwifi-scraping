from __future__ import annotations

from src.application.services.campaign_metrics_extractor import extract_campaign_metrics_from_prompt


def test_extract_metrics_from_key_value_prompt() -> None:
    prompt = """
    impressions: 1200
    clicks: 73
    ctr: 6.08%
    conversions: 10
    cpc: 1,25
    """
    data = extract_campaign_metrics_from_prompt(prompt)
    assert data["impressions"] == 1200
    assert data["clicks"] == 73
    assert data["ctr"] == 6.08
    assert data["conversions"] == 10
    assert data["cpc"] == 1.25


def test_extract_metrics_from_free_text_prompt() -> None:
    prompt = "A campanha teve 2.345 impressoes, 87 cliques, CTR 3,71% e 9 conversoes."
    data = extract_campaign_metrics_from_prompt(prompt)
    assert data["impressions"] == 2345
    assert data["clicks"] == 87
    assert data["ctr"] == 3.71
    assert data["conversions"] == 9


def test_extract_textual_and_json_fields() -> None:
    prompt = 'demografia: mulheres 25-34; trends: [100, 200, 180]; keyword_data: [{"keyword":"sapato","clicks":12}]'
    data = extract_campaign_metrics_from_prompt(prompt)
    assert data["demographic_data"] == "mulheres 25-34"
    assert data["trends"] == [100, 200, 180]
    assert isinstance(data["keyword_data"], list)
    assert data["keyword_data"][0]["keyword"] == "sapato"


def test_extract_empty_when_no_metric_like_content() -> None:
    prompt = "Me explique a campanha e monte uma estrategia para aumentar o alcance."
    data = extract_campaign_metrics_from_prompt(prompt)
    assert data == {}

