from __future__ import annotations

import os
import re

import numpy as np
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeInput
from src.domain.knowledge.entities import RetrievedContext
from src.infrastructure.config import AppConfig
from src.infrastructure.llm.langchain_openai_client import LangChainOpenAIClient
from src.infrastructure.vectorstores.qdrant_store import QdrantVectorStore
from src.infrastructure.wiring import build_chat_use_case


def _build_query_variants(query: str, passes: int) -> list[str]:
    variants = [
        query,
        f"{query} detalhes e excecoes",
        f"{query} exemplo pratico e diagnostico",
        f"{query} melhores praticas e erros comuns",
        f"{query} sinais, metricas e evidencia",
    ]
    return variants[:passes]


def _merge_contexts(context_lists: list[list[RetrievedContext]], limit: int) -> list[RetrievedContext]:
    merged: dict[tuple[str, int, str], RetrievedContext] = {}
    for contexts in context_lists:
        for ctx in contexts:
            key = (ctx.source_path, ctx.chunk_index, ctx.text)
            current = merged.get(key)
            if current is None:
                merged[key] = ctx
                continue
            current_score = current.score if current.score is not None else -1.0
            new_score = ctx.score if ctx.score is not None else -1.0
            if new_score > current_score:
                merged[key] = ctx

    ranked = sorted(merged.values(), key=lambda item: (item.score if item.score is not None else -1.0), reverse=True)
    return ranked[:limit]


def _run_power_search(
    *,
    query: str,
    cfg: AppConfig,
    top_k: int,
    passes: int,
    model: str,
    temperature: float,
) -> tuple[str, list[RetrievedContext]]:
    store = QdrantVectorStore(qdrant_url=cfg.qdrant_url, embedder_model=cfg.embedder_model)
    llm = LangChainOpenAIClient()

    queries = _build_query_variants(query, passes)
    all_results: list[list[RetrievedContext]] = []
    for candidate_query in queries:
        all_results.append(
            store.search(
                candidate_query,
                collection=cfg.qdrant_collection,
                top_k=top_k,
            )
        )

    final_contexts = _merge_contexts(all_results, limit=max(top_k, top_k * passes))
    if not final_contexts:
        return (
            "Nao encontrei base nas transcricoes para afirmar isso com seguranca. "
            "Tente reformular sua pergunta com mais detalhes.",
            [],
        )

    answer = llm.generate_answer(
        query=query,
        contexts=final_contexts,
        model_name=model,
        temperature=temperature,
    )
    return answer, final_contexts


def _expand_query_with_llm(query: str, *, model_name: str, temperature: float, n: int) -> list[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or n <= 0:
        return []

    llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)
    messages = [
        SystemMessage(
            content=(
                "Gere variações curtas de busca para RAG em Google Ads. "
                "Sem explicações. Retorne uma linha por variação."
            )
        ),
        HumanMessage(
            content=(
                f"Pergunta original: {query}\n"
                f"Gere {n} variações objetivas para recuperar trechos relevantes."
            )
        ),
    ]
    response = llm.invoke(messages)
    raw = str(response.content)
    lines = [re.sub(r"^[\\-\\d\\.\\)\\s]+", "", line).strip() for line in raw.splitlines()]
    cleaned = [line for line in lines if len(line) > 5]
    return cleaned[:n]


def _rerank_contexts_by_query_similarity(
    contexts: list[RetrievedContext],
    *,
    query: str,
    embedder_model: str,
    final_limit: int,
) -> list[RetrievedContext]:
    if not contexts:
        return []

    embedder = SentenceTransformer(embedder_model)
    query_vec = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    ctx_texts = [ctx.text for ctx in contexts]
    ctx_vecs = embedder.encode(ctx_texts, convert_to_numpy=True, normalize_embeddings=True)

    ranked_pairs: list[tuple[float, RetrievedContext]] = []
    for idx, ctx in enumerate(contexts):
        sim = float(np.dot(query_vec, ctx_vecs[idx]))
        ranked_pairs.append((sim, ctx))

    ranked_pairs.sort(key=lambda item: item[0], reverse=True)
    output: list[RetrievedContext] = []
    for sim, ctx in ranked_pairs[:final_limit]:
        output.append(
            RetrievedContext(
                text=ctx.text,
                source_file=ctx.source_file,
                source_path=ctx.source_path,
                chunk_index=ctx.chunk_index,
                section=ctx.section,
                topic_hint=ctx.topic_hint,
                score=sim,
            )
        )
    return output


def _run_advanced_retrieval(
    *,
    query: str,
    cfg: AppConfig,
    top_k: int,
    passes: int,
    model: str,
    temperature: float,
    use_query_expansion: bool,
    expansion_count: int,
    use_high_recall_rerank: bool,
    recall_multiplier: int,
) -> tuple[str, list[RetrievedContext]]:
    store = QdrantVectorStore(qdrant_url=cfg.qdrant_url, embedder_model=cfg.embedder_model)
    llm = LangChainOpenAIClient()

    queries = _build_query_variants(query, passes)
    if use_query_expansion:
        queries.extend(
            _expand_query_with_llm(
                query,
                model_name=model,
                temperature=min(temperature, 0.5),
                n=expansion_count,
            )
        )

    # Remove duplicadas preservando ordem.
    seen: set[str] = set()
    deduped_queries: list[str] = []
    for item in queries:
        norm = item.strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        deduped_queries.append(item.strip())

    retrieval_top_k = top_k * recall_multiplier if use_high_recall_rerank else top_k
    all_results: list[list[RetrievedContext]] = []
    for candidate_query in deduped_queries:
        all_results.append(
            store.search(
                candidate_query,
                collection=cfg.qdrant_collection,
                top_k=retrieval_top_k,
            )
        )

    merged = _merge_contexts(all_results, limit=max(top_k, retrieval_top_k * max(1, len(deduped_queries))))
    if use_high_recall_rerank:
        final_contexts = _rerank_contexts_by_query_similarity(
            merged,
            query=query,
            embedder_model=cfg.embedder_model,
            final_limit=top_k,
        )
    else:
        final_contexts = merged[:top_k]

    if not final_contexts:
        return (
            "Nao encontrei base nas transcricoes para afirmar isso com seguranca. "
            "Tente reformular sua pergunta com mais detalhes.",
            [],
        )

    answer = llm.generate_answer(
        query=query,
        contexts=final_contexts,
        model_name=model,
        temperature=temperature,
    )
    return answer, final_contexts


def _plan_audit_queries_with_llm(
    *,
    user_query: str,
    previous_queries: list[str],
    iteration: int,
    count: int,
    model_name: str,
    temperature: float,
) -> list[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or count <= 0:
        return []

    llm = ChatOpenAI(model=model_name, temperature=min(temperature, 0.4), api_key=api_key)
    messages = [
        SystemMessage(
            content=(
                "Voce e um planejador de retrieval para auditoria de campanhas Google Ads. "
                "Retorne apenas consultas curtas e objetivas, uma por linha, sem explicacoes."
            )
        ),
        HumanMessage(
            content=(
                f"Pergunta principal: {user_query}\n"
                f"Iteracao atual: {iteration}\n"
                f"Consultas ja usadas: {previous_queries[-12:] if previous_queries else 'nenhuma'}\n"
                f"Gere {count} novas consultas complementares para buscar evidencia faltante."
            )
        ),
    ]
    response = llm.invoke(messages)
    raw = str(response.content)
    lines = [re.sub(r"^[\\-\\d\\.\\)\\s]+", "", line).strip() for line in raw.splitlines()]
    cleaned = [line for line in lines if len(line) > 5]
    return cleaned[:count]


def _run_iterative_audit(
    *,
    query: str,
    cfg: AppConfig,
    top_k: int,
    model: str,
    temperature: float,
    iterations: int,
    queries_per_iteration: int,
    recall_multiplier: int,
) -> tuple[str, list[RetrievedContext]]:
    store = QdrantVectorStore(qdrant_url=cfg.qdrant_url, embedder_model=cfg.embedder_model)
    llm = LangChainOpenAIClient()

    used_queries: list[str] = [query]
    all_results: list[list[RetrievedContext]] = []

    # Iteracao 1 sempre inclui pergunta original + variacao curta.
    seed_queries = _build_query_variants(query, min(2, queries_per_iteration + 1))
    for seed in seed_queries:
        used_queries.append(seed)
        all_results.append(
            store.search(seed, collection=cfg.qdrant_collection, top_k=top_k * recall_multiplier)
        )

    for iteration in range(2, iterations + 1):
        planned = _plan_audit_queries_with_llm(
            user_query=query,
            previous_queries=used_queries,
            iteration=iteration,
            count=queries_per_iteration,
            model_name=model,
            temperature=temperature,
        )
        if not planned:
            break

        for candidate in planned:
            normalized = candidate.strip().lower()
            if not normalized or normalized in {item.lower() for item in used_queries}:
                continue
            used_queries.append(candidate)
            all_results.append(
                store.search(candidate, collection=cfg.qdrant_collection, top_k=top_k * recall_multiplier)
            )

    merged = _merge_contexts(all_results, limit=max(top_k * recall_multiplier * 2, top_k))
    final_contexts = _rerank_contexts_by_query_similarity(
        merged,
        query=query,
        embedder_model=cfg.embedder_model,
        final_limit=top_k,
    )

    if not final_contexts:
        return (
            "Nao encontrei base nas transcricoes para afirmar isso com seguranca. "
            "Tente reformular sua pergunta com mais detalhes.",
            [],
        )

    answer = llm.generate_answer(
        query=query,
        contexts=final_contexts,
        model_name=model,
        temperature=temperature,
    )
    return answer, final_contexts


def main() -> None:
    st.set_page_config(page_title="RAG Context Chat", page_icon="🤖", layout="wide")
    st.title("RAG Context Chat")
    st.markdown("Converse com o seu contexto vetorial (Qdrant).")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "model" not in st.session_state:
        st.session_state.model = "gpt-4o-mini"

    st.sidebar.header("Configuracoes")
    top_k = st.sidebar.slider("Quantidade de contextos (top_k)", 3, 20, 8)
    powerful_search_passes = st.sidebar.slider("Busca poderosa (passadas)", 1, 5, 1)
    st.sidebar.markdown("### Retrieval avancado")
    use_iterative_audit = st.sidebar.checkbox("Auditoria iterativa (LLM+Qdrant)", value=False)
    iterative_iterations = st.sidebar.slider("Iteracoes da auditoria", 2, 5, 3) if use_iterative_audit else 0
    iterative_queries_per_iter = st.sidebar.slider("Consultas por iteracao", 1, 4, 2) if use_iterative_audit else 0
    use_high_recall_rerank = st.sidebar.checkbox("High-Recall Retrieval + Reranking", value=False)
    recall_multiplier = st.sidebar.slider("High-recall multiplicador", 2, 6, 3) if use_high_recall_rerank else 2
    use_query_expansion = st.sidebar.checkbox("Query Expansion com LLM", value=False)
    expansion_count = st.sidebar.slider("Qtde de expansoes", 1, 5, 2) if use_query_expansion else 0
    temperature = st.sidebar.slider("Temperatura", 0.0, 1.0, 0.7, 0.1)
    model = st.sidebar.selectbox("Modelo", ["gpt-5", "gpt-4o-mini", "gpt-4-turbo"], index=1)
    st.session_state.model = model

    if st.sidebar.button("Limpar historico"):
        st.session_state.chat_history = []
        st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Digite sua pergunta...")
    if not prompt:
        return

    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Buscando contextos e gerando resposta..."):
            cfg = AppConfig()
            use_advanced_mode = powerful_search_passes > 1 or use_high_recall_rerank or use_query_expansion
            if use_iterative_audit:
                answer, contexts = _run_iterative_audit(
                    query=prompt,
                    cfg=cfg,
                    top_k=top_k,
                    model=model,
                    temperature=temperature,
                    iterations=iterative_iterations,
                    queries_per_iteration=iterative_queries_per_iter,
                    recall_multiplier=recall_multiplier if use_high_recall_rerank else 2,
                )
            elif use_advanced_mode:
                answer, contexts = _run_advanced_retrieval(
                    query=prompt,
                    cfg=cfg,
                    top_k=top_k,
                    passes=powerful_search_passes,
                    model=model,
                    temperature=temperature,
                    use_query_expansion=use_query_expansion,
                    expansion_count=expansion_count,
                    use_high_recall_rerank=use_high_recall_rerank,
                    recall_multiplier=recall_multiplier,
                )
            else:
                use_case = build_chat_use_case(cfg)
                result = use_case.execute(
                    ChatWithKnowledgeInput(
                        query=prompt,
                        top_k=top_k,
                        model_name=model,
                        temperature=temperature,
                    )
                )
                answer = result.answer
                contexts = result.contexts

            st.markdown(answer)
            with st.expander("Contextos utilizados"):
                for idx, ctx in enumerate(contexts, start=1):
                    st.markdown(f"**Trecho {idx}** - `{ctx.source_file}` [chunk {ctx.chunk_index}]")
                    st.markdown(f"> {ctx.text}")

            st.session_state.chat_history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
