# ADR — Architecture Decision Records

> Registre decisões importantes aqui.  
> Evita repetir discussões e ajuda seu “eu do futuro”.

---

## Template ADR
### ADR-XXX — Título
**Data:** YYYY-MM-DD

**Contexto:**  
Qual problema/decisão apareceu?

**Decisão:**  
O que foi escolhido?

**Alternativas consideradas:**  
- A
- B
- C

**Consequências:**  
- (+) ganhos
- (-) trade-offs
- riscos e ações

---

## ADR-001 — Qdrant como Vector Store
**Data:** 2026-02-13

**Contexto:**  
Precisa de banco vetorial local com boa performance e suporte a metadata/filtros.

**Decisão:**  
Usar Qdrant como vector store.

**Alternativas consideradas:**  
- Chroma
- FAISS (sem metadata/filtros tão bons)
- Pinecone (SaaS, custo, menos “local-first”)

**Consequências:**  
- (+) bom suporte a filtros e coleções
- (+) roda local
- (-) dependência de serviço/daemon (docker ou binário)

---

## ADR-002 — Streamlit para UI inicial
**Data:** 2026-02-13

**Contexto:**  
Precisa de UI rápida estilo chat e fácil de iterar.

**Decisão:**  
Streamlit no MVP.

**Consequências:**  
- (+) entrega rápida
- (-) para PWA/produção talvez migrar para API + frontend
