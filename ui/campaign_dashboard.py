import streamlit as st
import json

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from pathlib import Path
from service.rag_service import run_rag  # usa sua pipeline atual

HISTORY_DIR = Path("data/chat_history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

def load_history(campaign_id):
    file = HISTORY_DIR / f"{campaign_id}.json"
    if not file.exists():
        return []
    return json.loads(file.read_text())

def save_message(campaign_id, sender, text):
    file = HISTORY_DIR / f"{campaign_id}.json"
    history = load_history(campaign_id)
    history.append({
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "text": text
    })
    file.write_text(json.dumps(history, indent=2))

def main():
    st.title("📈 Painel de Campanha com LLM")

    campaign_id = st.text_input("ID da campanha:", value="Campanha_Exemplo")

    history = load_history(campaign_id)
    for msg in history:
        role = "🧑‍💼 Você" if msg["sender"] == "user" else "🤖 LLM"
        st.chat_message(msg["sender"]).markdown(f"**{role}:** {msg['text']}")

    query = st.chat_input("Envie uma atualização ou pergunta...")
    if query:
        save_message(campaign_id, "user", query)

        with st.spinner("Consultando modelo..."):
            answer = run_rag(query)
        save_message(campaign_id, "assistant", answer)

        st.chat_message("assistant").markdown(answer)

    if st.button("📊 Gerar relatório final"):
        with st.spinner("Gerando resumo..."):
            full_history = "\n".join([f"{m['sender']}: {m['text']}" for m in history])
            report = run_rag(f"Gere um relatório detalhado da campanha com base nisso:\n{full_history}")
            report_file = Path(f"data/reports/{campaign_id}_{datetime.now().date()}.txt")
            report_file.parent.mkdir(exist_ok=True, parents=True)
            report_file.write_text(report)
            st.success(f"✅ Relatório salvo em: {report_file}")

if __name__ == "__main__":
    main()
