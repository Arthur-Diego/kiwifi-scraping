from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.application.use_cases.list_product_mining_results import ListProductMiningResultsInput
from src.infrastructure.config import AppConfig
from src.infrastructure.persistence.postgres_product_mining_repository import PostgresProductMiningRepository
from src.infrastructure.wiring import build_list_product_mining_results_use_case, build_run_product_mining_batch_use_case


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


def main() -> None:
    st.set_page_config(page_title="Garimpagem de Produtos", page_icon="🧭", layout="wide")
    st.title("Garimpagem de Produtos - MVP")

    cfg = AppConfig()
    repo = PostgresProductMiningRepository()
    repo.ensure_schema()
    run_use_case = build_run_product_mining_batch_use_case(cfg)
    list_use_case = build_list_product_mining_results_use_case(cfg)

    st.sidebar.header("Controles")
    if st.sidebar.button("Rodar Batch Agora"):
        with st.spinner("Executando batch de garimpagem..."):
            output = run_use_case.execute()
        st.sidebar.success(
            f"Run #{output.run_summary.run_id} concluido com {output.run_summary.stored_count} produtos processados."
        )

    classification = st.sidebar.selectbox(
        "Classificacao",
        options=["TODOS", "ALTA_PRIORIDADE", "TESTAR", "BAIXA_PRIORIDADE"],
        index=0,
    )
    platform_filter = st.sidebar.text_input("Plataforma (opcional)", value="")
    limit = st.sidebar.slider("Limite", min_value=10, max_value=500, value=100, step=10)

    rows = list_use_case.execute(
        ListProductMiningResultsInput(
            limit=limit,
            classification=None if classification == "TODOS" else classification,
            platform=platform_filter or None,
        )
    )

    runs = repo.list_recent_runs(limit=10)
    if runs:
        latest = runs[0]
        st.caption(
            f"Ultimo batch: run #{latest.run_id} em {latest.started_at} | "
            f"candidatos={latest.candidates_count} armazenados={latest.stored_count}"
        )
    else:
        st.info("Nenhum batch executado ainda. Use 'Rodar Batch Agora'.")

    if not rows:
        st.warning("Nao ha produtos para os filtros selecionados.")
        return

    df = pd.DataFrame(rows)
    cols = [
        "product_name",
        "platform",
        "classification",
        "final_score",
        "buy_intent_score",
        "trend_score",
        "offer_score",
        "gravity",
        "commission_pct",
        "refund_rate",
        "keyword_volume",
        "trend_growth_30d",
        "run_created_at",
    ]
    available_cols = [c for c in cols if c in df.columns]
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Detalhes do Produto")
    options = {f"{item['product_name']} ({item['platform']}) [{item['classification']}]": item for item in rows}
    selected = st.selectbox("Selecione um produto", options=list(options.keys()))
    item = options[selected]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score Final", _fmt(item.get("final_score")))
    c2.metric("Fundo de Funil", _fmt(item.get("buy_intent_score")))
    c3.metric("Trend Score", _fmt(item.get("trend_score")))
    c4.metric("Offer Score", _fmt(item.get("offer_score")))

    st.write(f"**Produto:** {_fmt(item.get('product_name'))}")
    st.write(f"**Plataforma:** {_fmt(item.get('platform'))}")
    st.write(f"**Categoria:** {_fmt(item.get('category'))}")
    st.write(f"**Classificacao:** {_fmt(item.get('classification'))}")
    st.write(f"**URL de vendas:** {_fmt(item.get('sales_page_url'))}")
    st.write(
        f"**Price / Commission / Gravity:** {_fmt(item.get('price'))} / "
        f"{_fmt(item.get('commission_pct'))} / {_fmt(item.get('gravity'))}"
    )
    st.write(
        f"**Volume / Trend30d / Refund:** {_fmt(item.get('keyword_volume'))} / "
        f"{_fmt(item.get('trend_growth_30d'))} / {_fmt(item.get('refund_rate'))}"
    )

    st.markdown("**Rationale (json):**")
    st.code(json.dumps(item.get("rationale", {}), ensure_ascii=True, indent=2), language="json")

    st.markdown("**Raw Payload (json):**")
    st.code(json.dumps(item.get("raw_payload", {}), ensure_ascii=True, indent=2), language="json")


if __name__ == "__main__":
    main()

