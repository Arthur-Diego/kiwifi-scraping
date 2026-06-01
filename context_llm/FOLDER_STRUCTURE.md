# Estrutura de camadas do backend (confirmada)

Padrao arquitetural: **Clean Architecture**. Dependencias apontam para dentro
(`interface` -> `application` -> `domain`; `infrastructure` implementa as `ports`).
Wiring centralizado em `src/infrastructure/wiring.py`.

## Arvore real de `src/`

```text
src/
├── domain/                      # Entidades e regras de negocio (sem framework)
│   ├── campaigns/entities.py
│   ├── knowledge/entities.py
│   └── product_mining/entities.py
│
├── application/                 # Casos de uso + ports + services de aplicacao
│   ├── ports/                   # Interfaces (dependency inversion)
│   │   ├── campaign_repo.py
│   │   ├── chunker.py
│   │   ├── llm.py
│   │   ├── logger_port.py
│   │   ├── product_candidate_source.py
│   │   ├── product_mining_repository.py
│   │   ├── transcript_repo.py
│   │   └── vector_store.py
│   ├── services/
│   │   ├── campaign_metrics_extractor.py
│   │   └── product_mining_scorer.py
│   └── use_cases/
│       ├── chat_with_knowledge.py
│       ├── ingest_transcripts.py
│       ├── list_product_mining_results.py
│       ├── record_campaign_event.py
│       └── run_product_mining_batch.py
│
├── infrastructure/              # Adapters concretos das ports + config
│   ├── config.py
│   ├── wiring.py
│   ├── chunking/{semantic_chunker.py, token_tools.py}
│   ├── fs/local_transcript_repository.py
│   ├── llm/langchain_openai_client.py
│   ├── logger/std_logger.py
│   ├── persistence/{json_campaign_repo.py, postgres_chat_repository.py, postgres_product_mining_repository.py}
│   ├── product_mining/{composite_candidate_source.py, local_candidate_source.py, scraping_enriched_candidate_source.py}
│   ├── transcription/whisper_transcriber.py
│   └── vectorstores/qdrant_store.py
│
└── interface/                   # Transporte (borda)
    ├── api/{main.py, schemas.py}                 # FastAPI (backend HTTP)
    └── streamlit_app/                            # UI consumidora (fora do escopo backend)
        ├── app.py
        ├── campaign_dashboard.py
        ├── campaign_dashboard_constants.py
        ├── campaign_dashboard_metrics.py
        ├── campaign_dashboard_rag.py
        ├── campaign_dashboard_views.py
        └── product_mining_dashboard.py
```

`tests/`, `scripts/`, `main.py`, `requirements.txt` e `docker-compose.yml` ficam na **raiz do
repositorio** (nao dentro de `src/`).

## Evidencia da Clean Architecture (RF12)

- `domain/` nao importa framework, banco, HTTP ou SDK externo.
- `application/ports/` define interfaces; `application/use_cases/` orquestra dependendo apenas de
  ports; `application/services/` concentra regras de aplicacao puras.
- `infrastructure/` implementa as ports (ex.: `qdrant_store.py` -> `vector_store`,
  `langchain_openai_client.py` -> `llm`, `postgres_*` -> repositorios) e e montado em `wiring.py`.
- `interface/api/` (FastAPI) chama use cases; `interface/streamlit_app/` e consumidor de UI.

## Inconsistencias de posicionamento apontadas (RF13 — nao movidas nesta entrega)

- `domain/` esta "fino": cada subdominio tem apenas `entities.py`; nao ha separacao de
  `value_objects`/`services`/`exceptions` de dominio (aceitavel para o tamanho atual).
- `campaign_metrics_extractor.py` vive em `application/services/`; confirmar se a extracao por
  regex/parse e regra de aplicacao ou utilitario de infraestrutura.
- A UI Streamlit foi dividida em varios modulos `campaign_dashboard_*` — fora do escopo backend,
  apenas preservada como consumidor.
- Este arquivo divergia da realidade (listava `value_objects.py`, `summarize_campaign.py`,
  `openai_client.py`, `windows_transcript_repo.py`, etc., inexistentes); agora reflete a arvore atual.

> Nota de auditoria: `backup_legacy/` permanece na raiz (ignorado pelo git) porque
> `tests/regression/test_legacy_vs_new_regression.py` importa dele; nao e codigo morto.
