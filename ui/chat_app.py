import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from service.rag_service import run_rag
from repository.qdrant_repository import QdrantRetriever

st.set_page_config(page_title="Analise de métricas", page_icon="🤖", layout="wide")

# ======================
# CONFIGURAÇÕES INICIAIS
# ======================
st.title("🤖 RAG Context Chat")
st.markdown("Converse com o **seu contexto vetorial (Qdrant)** usando o poder do GPT!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "model" not in st.session_state:
    st.session_state.model = "gpt-4o-mini"

# ======================
# SIDEBAR DE CONFIGURAÇÃO
# ======================
st.sidebar.header("⚙️ Configurações")

st.sidebar.markdown("### 🔍 Busca Vetorial")
top_k = st.sidebar.slider("Quantidade de contextos (top_k):", 3, 20, 8)

st.sidebar.markdown("### 🧠 Modelo LLM")
model = st.sidebar.selectbox(
    "Selecione o modelo:",
    ["gpt-5", "gpt-4o-mini", "gpt-4-turbo"],
    index=["gpt-4o-mini", "gpt-5", "gpt-4-turbo"].index(st.session_state.model) if st.session_state.model else 0
)
st.session_state.model = model

temperature = st.sidebar.slider("Temperatura:", 0.0, 1.0, 0.7, 0.1)

if st.sidebar.button("🧹 Limpar histórico"):
    st.session_state.chat_history = []
    st.rerun()

# ======================
# INTERFACE PRINCIPAL
# ======================

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Digite sua pergunta...")

if prompt:
    # Exibe a mensagem do usuário
    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Busca contextos + gera resposta
    with st.chat_message("assistant"):
        with st.spinner("🔎 Buscando contextos e gerando resposta..."):
            try:
                retriever = QdrantRetriever()
                contexts = retriever.search(prompt, top_k=top_k)
                answer = run_rag(prompt)

                st.markdown(answer)
                with st.expander("📚 Contextos utilizados"):
                    for i, ctx in enumerate(contexts, 1):
                        st.markdown(f"**Trecho {i}:**")
                        st.markdown(f"> {ctx}")

                st.session_state.chat_history.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"❌ Erro ao processar consulta: {e}")

# ======================
# RODAPÉ
# ======================
st.markdown("---")
st.caption("Desenvolvido com ❤️ usando Streamlit + Qdrant + LangChain + OpenAI")
