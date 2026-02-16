from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeInput
from src.infrastructure.config import AppConfig
from src.infrastructure.persistence.postgres_chat_repository import PostgresChatRepository
from src.infrastructure.wiring import build_chat_use_case


def _campaign_label(item: dict) -> str:
    date_str = str(item.get("date_created", ""))[:10]
    return f"{item.get('campaign_name', 'campanha')}_{item.get('product_name', 'produto')}_{date_str}"


def _render_dashboard(metrics: dict | None) -> None:
    st.subheader("Dashboard da Campanha")
    if not metrics:
        st.info("Nenhuma métrica registrada para esta campanha ainda.")
        return

    st.markdown("### Desempenho")
    c1, c2, c3 = st.columns(3)
    c1.metric("Impressões", metrics.get("impressions", 0) or 0)
    c2.metric("Cliques", metrics.get("clicks", 0) or 0)
    c3.metric("CTR", metrics.get("ctr", 0.0) or 0.0)

    st.markdown("### Conversões")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", metrics.get("conversions", 0) or 0)
    c2.metric("Custo por conversão", metrics.get("cost_per_conversion", 0.0) or 0.0)
    c3.metric("Taxa de conversão", metrics.get("conversion_rate", 0.0) or 0.0)

    st.markdown("### Custos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Custo total", metrics.get("total_cost", 0.0) or 0.0)
    c2.metric("Orçamento diário", metrics.get("daily_budget", 0.0) or 0.0)
    c3.metric("CPC", metrics.get("cpc", 0.0) or 0.0)

    st.markdown("### Segmentação")
    col_a, col_b = st.columns(2)
    col_a.write("Demografia")
    col_a.write(metrics.get("demographic_data") or "Sem dados")
    col_b.write("Dispositivos")
    col_b.write(metrics.get("device_data") or "Sem dados")

    st.markdown("### Palavras-chave")
    keyword_data = metrics.get("keyword_data") or []
    if keyword_data:
        st.dataframe(keyword_data, use_container_width=True)
    else:
        st.write("Sem dados de palavras-chave.")

    st.markdown("### Anúncios")
    st.write(metrics.get("ad_performance") or "Sem dados")

    st.markdown("### Tendências")
    trends_value = metrics.get("trends")
    if isinstance(trends_value, str):
        try:
            parsed = json.loads(trends_value)
            if isinstance(parsed, list) and parsed:
                st.line_chart(parsed)
            else:
                st.write(trends_value)
        except Exception:
            st.write(trends_value)
    elif isinstance(trends_value, list) and trends_value:
        st.line_chart(trends_value)
    else:
        st.write("Sem tendências registradas.")


def main() -> None:
    st.set_page_config(page_title="Campaign Dashboard", page_icon="📊", layout="wide")
    st.title("Campaign Dashboard + Chat")

    cfg = AppConfig()
    repo = PostgresChatRepository()

    st.sidebar.header("Campanhas")
    campaigns = repo.list_campaigns()
    options = {_campaign_label(c): c for c in campaigns}

    if "show_new_campaign_form" not in st.session_state:
        st.session_state["show_new_campaign_form"] = False
    if "selected_campaign_id" not in st.session_state:
        st.session_state["selected_campaign_id"] = int(campaigns[0]["id"]) if campaigns else None

    if st.sidebar.button("Nova Campanha"):
        st.session_state["show_new_campaign_form"] = True

    if st.session_state["show_new_campaign_form"]:
        with st.sidebar.form("new_campaign_form"):
            campaign_name = st.text_input("Nome da campanha", value=f"Campanha_{datetime.now().strftime('%Y%m%d')}")
            product_name = st.text_input("Nome do produto", value="Produto")
            submitted = st.form_submit_button("Criar")
            if submitted:
                campaign_id = repo.create_campaign(campaign_name=campaign_name, product_name=product_name)
                st.session_state["campaign_id"] = campaign_id
                st.session_state["selected_campaign_id"] = campaign_id
                st.session_state["show_new_campaign_form"] = False
                st.success("Campanha criada com sucesso.")
                st.rerun()

    if not options:
        st.info("Nenhuma campanha cadastrada. Use o botão 'Nova Campanha' na sidebar.")
        st.stop()

    labels = list(options.keys())
    id_to_label = {int(v["id"]): k for k, v in options.items()}
    default_label = id_to_label.get(st.session_state["selected_campaign_id"], labels[0])
    default_index = labels.index(default_label) if default_label in labels else 0
    selected_label = st.sidebar.selectbox("Selecionar campanha", options=labels, index=default_index)

    selected_campaign = options[selected_label]
    campaign_id = int(selected_campaign["id"])
    st.session_state["campaign_id"] = campaign_id
    st.session_state["selected_campaign_id"] = campaign_id

    # Dashboard before chat.
    latest_metrics = repo.get_metrics(campaign_id)
    _render_dashboard(latest_metrics)

    st.markdown("---")
    st.subheader("Chat da Campanha")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    messages = repo.get_messages(campaign_id)
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    top_k = st.sidebar.slider("top_k", 3, 20, 8)
    temperature = st.sidebar.slider("temperatura", 0.0, 1.0, 0.7, 0.1)
    model = st.sidebar.selectbox("modelo", ["gpt-5", "gpt-4o-mini", "gpt-4-turbo"], index=1)

    prompt = st.chat_input("Pergunte sobre sua campanha...")
    if not prompt:
        return

    repo.save_message(campaign_id, "user", prompt)
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Gerando resposta..."):
            use_case = build_chat_use_case(cfg)
            result = use_case.execute(
                ChatWithKnowledgeInput(
                    query=prompt,
                    top_k=top_k,
                    model_name=model,
                    temperature=temperature,
                )
            )
            st.markdown(result.answer)
            repo.save_message(campaign_id, "assistant", result.answer)

            with st.expander("Contextos utilizados"):
                for i, ctx in enumerate(result.contexts, 1):
                    st.markdown(f"**Trecho {i}** - `{ctx.source_file}` [chunk {ctx.chunk_index}]")
                    st.markdown(f"> {ctx.text}")


if __name__ == "__main__":
    main()
