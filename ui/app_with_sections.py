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

from service.rag_service import run_rag, run_rag_with_context
from repository.qdrant_sections_repository import QdrantSectionRepository

# --------------------------------------------------------------------
# 📂 Diretórios
# --------------------------------------------------------------------
HISTORY_DIR = Path("data/chat_history")
REPORT_DIR = Path("data/reports")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

repo = QdrantSectionRepository()

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

    # 🔹 Dropdown de Sections (Qdrant)
    sections = ["(Todas)"] + repo.get_all_sections()
    selected_section = st.sidebar.selectbox("Filtrar por Section:", sections)

    st.sidebar.markdown("---")

    with st.sidebar.expander("⚙️ Parâmetros do Modelo", expanded=False):
        temperature = st.slider("Temperatura do LLM", 0.0, 1.5, 0.7, step=0.1)
        top_k = st.slider("Top-K (contextos do Qdrant)", 1, 20, 5)

    # ==================== CORPO PRINCIPAL ====================
    if not campaign_id:
        st.warning("Selecione ou crie uma campanha para começar.")
        return

    st.subheader(f"💬 Chat da campanha: `{campaign_id}`")

    history = load_history(campaign_id)

    # ----- Chat Histórico -----
    st.markdown("---")
    for msg in history:
        role = "🧑‍💼 Você" if msg["sender"] == "user" else "🤖 LLM"
        st.chat_message(msg["sender"]).markdown(f"**{role}:** {msg['text']}")

    query = st.chat_input("Envie uma atualização ou pergunta sobre a campanha...")

    if query:
        save_message(campaign_id, "user", query)
        st.chat_message("user").markdown(f"🧑‍💼 Você: {query}")

        with st.spinner("🔍 Consultando contexto e gerando resposta..."):
            # ====================================
            # 🔥 COMPORTAMENTO B IMPLEMENTADO AQUI
            # ====================================
            if selected_section != "(Todas)":
                # Busca filtrada por section
                contexts = repo.search_by_section(query, selected_section, top_k=top_k)
                answer = run_rag_with_context(query, contexts, temperature=temperature)
            else:
                # Busca normal (sem filtro)
                answer = run_rag(query, top_k=top_k, temperature=temperature)

        save_message(campaign_id, "assistant", answer)
        st.chat_message("assistant").markdown(f"🤖 {answer}")

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Apagar histórico desta campanha"):
        file = HISTORY_DIR / f"{campaign_id}.json"
        if file.exists():
            file.unlink()
            st.sidebar.success(f"🧹 Histórico apagado!")
            st.experimental_rerun()


# --------------------------------------------------------------------
if __name__ == "__main__":
    main()
