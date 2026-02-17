# Product Mining MVP - Implementacao

## Objetivo
Rodar garimpagem de produtos diariamente, gravar classificacoes no Postgres e visualizar tudo em tela dedicada no Streamlit.

## Componentes criados
- `src/domain/product_mining/entities.py`
- `src/application/services/product_mining_scorer.py`
- `src/application/use_cases/run_product_mining_batch.py`
- `src/application/use_cases/list_product_mining_results.py`
- `src/application/ports/product_candidate_source.py`
- `src/application/ports/product_mining_repository.py`
- `src/infrastructure/persistence/postgres_product_mining_repository.py`
- `src/infrastructure/product_mining/local_candidate_source.py`
- `src/interface/streamlit_app/product_mining_dashboard.py`
- `scripts/run_product_mining_batch.py`
- `context_llm/product_mining_candidates.seed.json`
- `src/infrastructure/product_mining/scraping_enriched_candidate_source.py`

## Banco de dados
Tabelas:
- `product_mining_runs`
- `product_mining_results`

## Batch diario
Execucao unica:
```bash
python3 -m scripts.run_product_mining_batch
```

Loop continuo (24h):
```bash
python3 -m scripts.run_product_mining_batch --loop --interval-hours 24
```

### Scraping no batch
Ativado por padrao no MVP para enriquecer os candidatos antes do score.

Variaveis:
- `PRODUCT_MINING_ENABLE_SCRAPING=1` (default)
- `PRODUCT_MINING_SCRAPING_TIMEOUT_SECONDS=12`
- `PRODUCT_MINING_SCRAPING_MAX_WORKERS=6`

Enriquecimentos aplicados:
- scraping da pagina de vendas (`sales_page_url`): titulo, meta description, preco aproximado e tipo de landing.
- sinal de tendencia por scraping de feed diario do Google Trends (RSS).
- sinal de demanda por scraping de Google Suggest (autocomplete).

## Streamlit
Abrir tela nova:
```bash
./run_app.sh --ui-page product-mining
```

## API
- `POST /product-mining/run`
- `GET /product-mining/products?limit=100&classification=ALTA_PRIORIDADE&platform=ClickBank`

## Selenium session helper (manual login + reuse)
Script:
- `scripts/selenium_session_manager.py`

### Comandos prontos (Selenium)
Carregar variaveis do `.env`:
```bash
set -a; source .env; set +a
```

Bootstrap de sessao (primeira vez / renovar sessao):
```bash
python3 -m scripts.selenium_session_manager --mode bootstrap --auto-login
```

Executar scraping Top Offers (5 paginas):
```bash
python3 -m scripts.selenium_session_manager \
  --mode run \
  --open-affiliate-marketplace \
  --scrape-marketplace \
  --marketplace-pages 5 \
  --marketplace-wait-seconds 60
```

Executar scraping Top Offers (somente 1 pagina para teste rapido):
```bash
python3 -m scripts.selenium_session_manager \
  --mode run \
  --open-affiliate-marketplace \
  --scrape-marketplace \
  --marketplace-pages 1 \
  --marketplace-wait-seconds 60
```

Saida esperada:
```bash
data/reports/clickbank_marketplace_top_offers.json
```

Uso:
1) Bootstrap de sessao (login manual 1x):
```bash
python3 -m scripts.selenium_session_manager \
  --mode bootstrap \
  --login-url "$SELENIUM_LOGIN_URL" \
  --success-selector "$SELENIUM_SUCCESS_SELECTOR"
```

2) Reuso de sessao salva:
```bash
python3 -m scripts.selenium_session_manager \
  --mode run \
  --target-url "$SELENIUM_TARGET_URL" \
  --success-selector "$SELENIUM_SUCCESS_SELECTOR" \
  --headless
```

3) Bootstrap com auto-preenchimento (ClickBank HTML selectors):
```bash
python3 -m scripts.selenium_session_manager \
  --mode bootstrap \
  --login-url "$SELENIUM_LOGIN_URL" \
  --success-selector "$SELENIUM_SUCCESS_SELECTOR" \
  --success-url-contains "$SELENIUM_SUCCESS_URL_CONTAINS" \
  --auto-login
```

Observacoes:
- nao armazena usuario/senha no codigo.
- exige login manual inicial e pode expirar conforme politica da plataforma.

## Scrape do Affiliate Marketplace (Top Offers + paginação)
Com a sessao valida, o script navega para Affiliate Marketplace e coleta ofertas nas primeiras N paginas.

Campos coletados (quando disponíveis):
- `offer_id`, `title`, `offer_link`, `category`, `description`
- `cpa_available`, `direct_tracking_available`
- `affiliate_page_url`, `sales_page_url`, `image_url`
- `avg_per_conv_total`, `avg_per_conv_initial`, `avg_per_conv_future`
- `cvr`, `epc`, `gravity`, `rank`

Execucao:
```bash
python3 -m scripts.selenium_session_manager \
  --mode run \
  --target-url "$SELENIUM_TARGET_URL" \
  --success-selector "$SELENIUM_SUCCESS_SELECTOR" \
  --success-url-contains "$SELENIUM_SUCCESS_URL_CONTAINS" \
  --open-affiliate-marketplace \
  --scrape-marketplace \
  --marketplace-pages 5
```

Saida padrao:
- `data/reports/clickbank_marketplace_top_offers.json`

## request_FLOW_CLICKBANK_SELENIUM (arvore detalhada)
```text
ENTRYPOINT
└── python3 -m scripts.selenium_session_manager
    └── arquivo: scripts/selenium_session_manager.py
    ├── mode=bootstrap (preparar sessao)
    │   ├── _build_driver
    │   │   └── arquivo: scripts/selenium_session_manager.py
    │   │   ├── resolve Chrome binary (env/auto-detect)
    │   │   └── resolve ChromeDriver (env/auto-detect/fallback Selenium Manager)
    │   ├── driver.get(SELENIUM_LOGIN_URL)
    │   ├── [opcional] auto-login
    │   │   ├── preencher username/password selectors
    │   │   └── submit form#sign-in
    │   ├── aguarda sucesso
    │   │   ├── success_selector (ex: #profile-popover)
    │   │   └── success_url_contains (ex: /master/dashboard)
    │   └── persistencia
    │       └── arquivos:
    │           ├── data/reports/selenium_session_cookies.json
    │           └── data/reports/selenium_profile/
    │       ├── salvar cookies (SELENIUM_COOKIE_FILE)
    │       └── salvar profile dir (SELENIUM_PROFILE_DIR)
    │
    └── mode=run (reuso sessao + scrape)
        ├── arquivo: scripts/selenium_session_manager.py
        ├── _build_driver
        ├── _load_cookies
        ├── driver.get(SELENIUM_TARGET_URL)
        ├── valida sessao
        │   ├── success_selector
        │   └── success_url_contains
        ├── _open_affiliate_marketplace
        │   ├── encontra link por selector (a[title='Affiliate Marketplace'])
        │   ├── abre href em mesma aba (evita target=_blank)
        │   └── confirma URL com affiliate-marketplace/mktplace
        ├── _ensure_top_offers_view
        │   ├── força rota:
        │   │   └── #/results?sortField=rank&sortDescending=false
        │   ├── fallback: clique em [data-cy='Top Offers-category-nav']
        │   └── fallback final: busca por elemento textual "Top Offers"
        ├── _wait_marketplace_loaded
        │   ├── detecta UI pronta por:
        │   │   ├── links #/offer-details?offer=
        │   │   ├── [data-cy='sort-by-dropdown']
        │   │   ├── botões de paginação
        │   │   └── sinais textuais Top Offers/Sort results by
        │   └── em timeout:
        │       └── arquivos:
        │           ├── data/reports/selenium_marketplace_debug.html
        │           └── data/reports/selenium_marketplace_debug.png
        │       ├── salva HTML debug
        │       └── salva screenshot debug
        ├── _scrape_marketplace_pages (N paginas)
        │   ├── page=1..N
        │   │   ├── _goto_marketplace_page(page)
        │   │   │   ├── scrollIntoView no botão de paginação
        │   │   │   ├── click com retry
        │   │   │   └── fallback JS click (evita ElementClickIntercepted)
        │   │   ├── _extract_offers_from_current_page
        │   │   │   ├── identifica offer card/container
        │   │   │   ├── campos base:
        │   │   │   │   ├── offer_id, title, offer_link, category
        │   │   │   │   └── cpa_available, direct_tracking_available
        │   │   │   ├── campos de link:
        │   │   │   │   ├── affiliate_page_url (View Affiliate Page)
        │   │   │   │   └── sales_page_url (View Sales Page / clickUrl decoded)
        │   │   │   ├── campos visuais/textuais:
        │   │   │   │   ├── image_url, description
        │   │   │   │   └── avg_per_conv_total/initial/future
        │   │   │   └── campos de performance:
        │   │   │       ├── cvr, epc, gravity, rank
        │   │   │       └── fallback regex quando seletor direto falha
        │   │   └── deduplicação por offer_id/title
        │   └── monta payload final (offers_count + offers[])
        └── grava arquivo
            └── data/reports/clickbank_marketplace_top_offers.json

CONFIG
└── arquivos de variáveis
    ├── .env
    └── .env.example
```

## Variaveis Selenium usadas no fluxo ClickBank
- `SELENIUM_LOGIN_URL`
- `SELENIUM_TARGET_URL`
- `SELENIUM_SUCCESS_SELECTOR`
- `SELENIUM_SUCCESS_URL_CONTAINS`
- `SELENIUM_LOGIN_USERNAME`
- `SELENIUM_LOGIN_PASSWORD`
- `SELENIUM_USERNAME_SELECTOR`
- `SELENIUM_PASSWORD_SELECTOR`
- `SELENIUM_SUBMIT_SELECTOR`
- `SELENIUM_COOKIE_FILE`
- `SELENIUM_PROFILE_DIR`
- `SELENIUM_OPEN_AFFILIATE_MARKETPLACE`
- `SELENIUM_AFFILIATE_MARKETPLACE_SELECTOR`
- `SELENIUM_SCRAPE_MARKETPLACE`
- `SELENIUM_MARKETPLACE_PAGES`
- `SELENIUM_MARKETPLACE_WAIT_SECONDS`
- `SELENIUM_MARKETPLACE_OUTPUT_FILE`
- `SELENIUM_CHROME_BINARY` (opcional)
- `SELENIUM_CHROMEDRIVER_PATH` (opcional)

## request_FLOW (arvore)
```text
User / Scheduler
└── run_product_mining_batch (script ou API)
    ├── build_run_product_mining_batch_use_case
    │   ├── LocalProductCandidateSource.fetch_candidates (JSON local)
    │   ├── ScrapingEnrichedProductCandidateSource._scrape_sales_page
    │   ├── ScrapingEnrichedProductCandidateSource._scrape_google_trend_signal
    │   └── PostgresProductMiningRepository.ensure_schema
    ├── repository.create_run
    ├── for candidate in candidates
    │   ├── score_product_candidate
    │   │   ├── buy_intent_score
    │   │   ├── trend_score
    │   │   ├── offer_score
    │   │   └── final_score + classification
    │   └── repository.save_result
    └── output run_summary + top_results

Streamlit product_mining_dashboard
├── list_recent_runs
├── list_product_mining_results (filtros)
└── render tabela + detalhe (rationale/raw_payload)
```

## request_FLOW_ATUAL (detalhado)
```text
ENTRYPOINTS
├── CLI
│   └── python3 -m scripts.run_product_mining_batch [--loop --interval-hours 24]
├── API
│   ├── POST /product-mining/run
│   └── GET /product-mining/products
└── Streamlit
    └── ./run_app.sh --ui-page product-mining

BATCH EXECUTION FLOW
└── RunProductMiningBatchUseCase.execute
    ├── repository.ensure_schema
    │   ├── CREATE TABLE product_mining_runs
    │   └── CREATE TABLE product_mining_results
    ├── source.fetch_candidates
    │   └── ScrapingEnrichedProductCandidateSource
    │       ├── CompositeProductCandidateSource
    │       │   └── LocalProductCandidateSource.fetch_candidates (seed/base)
    │       └── for each candidate (parallel workers)
    │           ├── _scrape_sales_page(sales_page_url)
    │           │   ├── requests.get(HTML)
    │           │   ├── extract title/meta/body text
    │           │   ├── infer landing_page_type
    │           │   └── extract price/cta signals
    │           └── _scrape_google_trend_signal(product_name)
    │               ├── requests.get(Google Trends daily RSS)
    │               ├── token matching by product name
    │               └── trend_growth_30d proxy
    │           └── _scrape_google_suggest_signal(product_name)
    │               ├── requests.get(Google suggest endpoint)
    │               └── keyword_volume / competition proxy
    ├── repository.create_run
    ├── for each enriched candidate
    │   ├── score_product_candidate
    │   │   ├── buy_intent_score
    │   │   ├── trend_score
    │   │   ├── offer_score
    │   │   └── final_score + classification
    │   └── repository.save_result
    └── output
        ├── run_summary
        └── top_results

READ FLOW (UI/API)
├── ListProductMiningResultsUseCase.execute
│   └── repository.list_latest_results (latest per product_key + filters)
└── product_mining_dashboard
    ├── render runs summary
    ├── render products table
    └── render selected product details (scores + rationale + raw_payload)
```
