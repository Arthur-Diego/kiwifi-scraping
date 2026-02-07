import streamlit as st
import json
import re
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from service.rag_service import run_rag  # sua pipeline RAG

# --------------------------------------------------------------------
# 📂 Diretórios
# --------------------------------------------------------------------
HISTORY_DIR = Path("data/chat_history")
REPORT_DIR = Path("data/reports")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------
# ⚙️ Utilitários
# --------------------------------------------------------------------
def list_campaigns():
    return [f.stem for f in HISTORY_DIR.glob("*.json")]

def load_history(campaign_id):
    file = HISTORY_DIR / f"{campaign_id}.json"
    if not file.exists():
        return []
    return json.loads(file.read_text(encoding="utf-8"))

def save_message(campaign_id, sender, text):
    file = HISTORY_DIR / f"{campaign_id}.json"
    history = load_history(campaign_id)
    history.append({
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "text": text
    })
    file.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

# --------------------------------------------------------------------
# 📊 Funções de análise de métricas
# --------------------------------------------------------------------
def extract_metrics(history):
    """
    Extrai métricas cumulativas (impressões, cliques, checkouts, conversões)
    e calcula as diferenças em relação à atualização anterior.
    """
    metrics = []
    last_values = {"impressions": 0, "clicks": 0, "checkouts": 0, "conversions": 0}

    for msg in history:
        if msg["sender"] != "user":
            continue
        text = msg["text"].lower()
        timestamp = msg["timestamp"]

        imp = re.findall(r"(\d+)\s*impress", text)
        clk = re.findall(r"(\d+)\s*click|(\d+)\s*clique", text)
        chk = re.findall(r"(\d+)\s*checkout", text)
        conv = re.findall(r"(\d+)\s*convers", text)

        # Pega o valor mais recente da regex
        impressions = int(imp[-1]) if imp else last_values["impressions"]
        clicks = int(clk[-1][0] or clk[-1][1]) if clk else last_values["clicks"]
        checkouts = int(chk[-1]) if chk else last_values["checkouts"]
        conversions = int(conv[-1]) if conv else last_values["conversions"]

        # Calcula variação em relação ao último valor
        delta_imp = max(0, impressions - last_values["impressions"])
        delta_clk = max(0, clicks - last_values["clicks"])
        delta_chk = max(0, checkouts - last_values["checkouts"])
        delta_conv = max(0, conversions - last_values["conversions"])

        metrics.append({
            "timestamp": datetime.fromisoformat(timestamp),
            "impressions": delta_imp,
            "clicks": delta_clk,
            "checkouts": delta_chk,
            "conversions": delta_conv,
        })

        # Atualiza o total armazenado
        last_values.update({
            "impressions": impressions,
            "clicks": clicks,
            "checkouts": checkouts,
            "conversions": conversions
        })

    df = pd.DataFrame(metrics)
    if not df.empty:
        df = df.fillna(0).sort_values("timestamp")
    return df


def summarize_metrics(df):
    """Cria um resumo total das métricas"""
    if df.empty:
        return {"impressions": 0, "clicks": 0, "checkouts": 0, "conversions": 0}
    return {
        "impressions": int(df["impressions"].sum()),
        "clicks": int(df["clicks"].sum()),
        "checkouts": int(df["checkouts"].sum()),
        "conversions": int(df["conversions"].sum())
    }

# --------------------------------------------------------------------
# 🚀 App principal
# --------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Painel de Campanhas", page_icon="📈", layout="wide")
    st.title("📊 Painel Inteligente de Campanhas com RAG e Métricas")

    # ==================== SIDEBAR ====================
    st.sidebar.header("🎯 Seleção de Campanha")

    existing_campaigns = list_campaigns()
    selected_campaign = st.sidebar.selectbox(
        "Escolha uma campanha existente:",
        options=["(Nova campanha)"] + existing_campaigns
    )

    if selected_campaign == "(Nova campanha)":
        campaign_id = st.sidebar.text_input("🧾 Nome da nova campanha:", value=f"Campanha_{datetime.now().strftime('%Y%m%d')}")
        if st.sidebar.button("➕ Criar nova campanha"):
            (HISTORY_DIR / f"{campaign_id}.json").write_text("[]", encoding="utf-8")
            st.sidebar.success(f"✅ Campanha '{campaign_id}' criada!")
            st.experimental_rerun()
    else:
        campaign_id = selected_campaign

    st.sidebar.markdown("---")
    with st.sidebar.expander("⚙️ Parâmetros do Modelo", expanded=False):
        temperature = st.slider("Temperatura do LLM", 0.0, 1.5, 0.7, step=0.1)
        top_k = st.slider("Top-K (contextos do Qdrant)", 1, 10, 5)

    # ==================== CORPO PRINCIPAL ====================
    if not campaign_id:
        st.warning("Selecione ou crie uma campanha para começar.")
        return

    st.subheader(f"💬 Chat da campanha: `{campaign_id}`")

    history = load_history(campaign_id)
    df_metrics = extract_metrics(history)
    summary = summarize_metrics(df_metrics)

    # ==================== PAINEL DE KPIs ====================
    st.markdown("### 📈 Indicadores de Desempenho")
    cols = st.columns(4)
    cols[0].metric("Impressões", summary["impressions"])
    cols[1].metric("Cliques", summary["clicks"])
    cols[2].metric("Checkouts", summary["checkouts"])
    cols[3].metric("Conversões", summary["conversions"])

    # ==================== GRÁFICOS ====================
    if not df_metrics.empty:
        st.markdown("### 📊 Evolução da campanha")
        df_melted = df_metrics.melt(id_vars="timestamp", var_name="Métrica", value_name="Valor")
        fig = px.line(df_melted, x="timestamp", y="Valor", color="Métrica",
                      markers=True, title="Evolução diária das métricas")
        st.plotly_chart(fig, use_container_width=True)

    # ==================== HISTÓRICO DE CHAT ====================
    st.markdown("---")
    for msg in history:
        role = "🧑‍💼 Você" if msg["sender"] == "user" else "🤖 LLM"
        st.chat_message(msg["sender"]).markdown(f"**{role}:** {msg['text']}")

    query = st.chat_input("Envie uma atualização ou pergunta sobre a campanha...")
    if query:
        save_message(campaign_id, "user", query)
        st.chat_message("user").markdown(f"🧑‍💼 Você: {query}")

        with st.spinner("🔍 Consultando contexto e gerando resposta..."):
            answer = run_rag(query, top_k=top_k, temperature=temperature)

        save_message(campaign_id, "assistant", answer)
        st.chat_message("assistant").markdown(f"🤖 {answer}")

    # ==================== RELATÓRIO FINAL ====================
    st.markdown("---")
    if st.button("📄 Gerar relatório final"):
        with st.spinner("Gerando relatório..."):
            full_history = "\n".join([f"{m['sender']}: {m['text']}" for m in history])
            prompt = (
                f"Gere um relatório analítico da campanha '{campaign_id}', "
                "incluindo métricas, aprendizados e recomendações:\n\n"
                f"{full_history}"
            )
            report = run_rag(prompt, top_k=top_k, temperature=0.5)

            report_file = REPORT_DIR / f"{campaign_id}_{datetime.now().date()}.txt"
            report_file.write_text(report, encoding="utf-8")
            st.success(f"✅ Relatório salvo em: {report_file}")

    # ==================== RESET ====================
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Apagar histórico desta campanha"):
        file = HISTORY_DIR / f"{campaign_id}.json"
        if file.exists():
            file.unlink()
            st.sidebar.success(f"🧹 Histórico de '{campaign_id}' apagado!")
            st.experimental_rerun()

# --------------------------------------------------------------------
if __name__ == "__main__":
    main()
