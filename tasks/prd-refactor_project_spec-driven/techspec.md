# Especificacao tecnica

> Feature: `refactor_project_spec-driven`
> PRD de entrada: `tasks/prd-refactor_project_spec-driven/prd.md`

## Resumo executivo

Esta feature e um esforco de **higiene de repositorio + confirmacao estrutural do backend**, sem
qualquer mudanca de comportamento funcional. A abordagem central, refinada em relacao ao PRD, e o
**modelo de quarentena**: em vez de apagar itens classificados como REMOVER, todo item nao essencial
e movido para um diretorio `_quarantine/` (ignorado pelo git, organizado por categoria), permitindo
expurgo gradual e auditavel pelo mantenedor. Nada de runtime e destruido na execucao; o backup so e
exigido como gate do expurgo final da quarentena.

As decisoes principais sao: (1) padronizar um unico ambiente virtual `.venv` em Python 3.11.9,
mantendo `.pyenv` apenas como gerenciador de versao fora do versionamento; (2) manter os dados de
runtime ativos (`postgres_data/`, `qdrant_storage/`, `qdrant_snapshots/`) no lugar para nao quebrar os
mounts do `docker-compose.yml`, garantindo apenas que estejam no `.gitignore`; (3) consolidar
documentacao migrando ADRs e guidelines de `context/` para `context_llm/` (fonte canonica) e
quarentenar o restante; (4) renomear `requeriments.txt` para `requirements.txt` atualizando
referencias; (5) confirmar e documentar a Clean Architecture ja existente em `src/`. A integridade e
validada por `pytest`, pelo import de `main.py` e pela inicializacao via `run_app.sh`.

## Contexto tecnico do projeto

- **Linguagem e versao alvo**: Python 3.11.9 (pinned em `.python-version`; `.venv-wsl` confirma 3.11.9,
  enquanto `.venv-linux` diverge em 3.12.3).
- **Framework principal**: FastAPI na borda HTTP (`src/interface/api/main.py`, reexportado por
  `main.py`); Streamlit como interface consumidora (`src/interface/streamlit_app/`). Nenhum dos dois
  e alterado funcionalmente.
- **Build/dependencias**: instalacao via `pip` a partir do arquivo de requirements; nao ha Poetry,
  PDM ou Hatch. Nao ha referencia a `pip install -r` em `run_app.sh` nem no `docker-compose.yml`
  (eles assumem o ambiente ja provisionado), o que reduz o raio de impacto da renomeacao.
- **Padrao arquitetural ja usado**: Clean Architecture, evidenciado por
  `src/domain/`, `src/application/{ports,use_cases,services}/`, `src/infrastructure/` e
  `src/interface/`.
- **Persistencia e servicos externos**: PostgreSQL (historico de chat / eventos de campanha), Qdrant
  (vector store), OpenAI via LangChain (`src/infrastructure/llm/langchain_openai_client.py`),
  Whisper (transcricao), Selenium (mining). Orquestrados localmente via `docker-compose.yml`
  (servicos `qdrant` e `postgres`).

## Arquitetura do sistema

### Padrao arquitetural escolhido

**Clean Architecture** — confirmada, nao escolhida do zero.

- **Evidencia no projeto**: a arvore `src/` separa explicitamente `domain/` (entidades de
  `campaigns`, `knowledge`, `product_mining`, sem dependencia de framework), `application/` com
  `ports/` (interfaces: `llm.py`, `vector_store.py`, `campaign_repo.py`, `transcript_repo.py`,
  `chunker.py`, `logger_port.py`, `product_mining_repository.py`, `product_candidate_source.py`),
  `use_cases/` e `services/`, mais `infrastructure/` (adapters concretos: `persistence/`,
  `vectorstores/`, `llm/`, `chunking/`, `fs/`, `transcription/`, `product_mining/`,
  `logger/`) e `interface/` (`api/`, `streamlit_app/`). O wiring de dependencias esta centralizado
  em `src/infrastructure/wiring.py`. As dependencias apontam para dentro (use cases dependem de
  ports; adapters implementam ports).
- **Justificativa**: o PRD (Premissas) declara explicitamente que esse e o padrao predominante e deve
  ser **preservado**. A feature e de higiene/estrutura, entao a Tech Spec apenas confirma e documenta,
  sem reescrever.
- **Rules aplicaveis**: `backend-architecture.md` (declaracao obrigatoria do padrao) e
  `clean-architecture.md` (camadas e direcao de dependencia). `mvc-architecture.md` nao se aplica.
- **Impacto em pacotes, camadas e testes**: nenhum modulo muda de camada nesta entrega. Eventuais
  inconsistencias de posicionamento sao apenas **apontadas e documentadas** (RF12), nao
  movidas, para nao arriscar regressao (RF13). Testes permanecem em `tests/unit/` e
  `tests/regression/`.

### Visao dos componentes

Esta feature nao adiciona componentes de runtime. Os "componentes" sao artefatos de organizacao e o
fluxo de saneamento:

- **Diretorio de quarentena `_quarantine/`** (novo, fora do versionamento): destino de tudo que e
  nao essencial. Subpastas por categoria:
  - `venvs/` — `.venv-linux/`, `.venv-wsl/`, `venv-project-kiwifi/`.
  - `legacy/` — `backup_legacy/`.
  - `artifacts/` — `__pycache__/` (todos os niveis), `.pytest_cache/`, `.idea/`.
  - `runtime-regen/` — `exports/`, `logs/` (regeneraveis pela aplicacao).
  - `docs-extra/` — `context/` (apos migracao de ADRs/guidelines).
  - `mistakes/` — arquivo com caminho literal do Windows
    `C:\Users\arthu\.kiwifi-scraping\chat_history.db` e `context_llm/README.md:Zone.Identifier`.
- **`.gitignore` consolidado** (modificado): cobre venvs, caches, builds, `.idea/`,
  `*.Zone.Identifier`, `logs/`, `exports/`, dados de runtime, `data/*.db`, `.env` e `_quarantine/`.
- **`.venv` unico** (novo padrao): ambiente virtual em Python 3.11.9.
- **`requirements.txt`** (renomeado de `requeriments.txt`).
- **`context_llm/`** (fonte canonica de documentacao): recebe ADRs e guidelines migrados.
- **Relatorio de auditoria/MANIFEST**: registro do que foi movido, de onde e por que, servindo de
  trilha de auditoria (vide Observabilidade).

Fronteiras dominio/aplicacao/infra/transporte permanecem **inalteradas**.

### Decisoes de arquitetura

- **Quarentena em vez de delecao imediata (refinamento do PRD)**: o PRD descreve REMOVER como
  apagar do disco (RF9). A pedido do mantenedor, adota-se quarentena reversivel. Trade-off:
  ocupa disco temporariamente, mas elimina risco de perda irreversivel e torna o expurgo
  incremental e auditavel. Alternativa considerada e descartada: `git rm` + delecao direta (mais
  arriscado, menos reversivel).
- **Dados de runtime permanecem na raiz**: `docker-compose.yml` monta `./postgres_data`,
  `./qdrant_storage` e `./qdrant_snapshots` em caminhos relativos fixos. Move-los quebraria os mounts
  e faria a aplicacao recriar volumes vazios. Decisao: **manter no lugar**, apenas garantir
  `.gitignore`. Alternativas descartadas: (a) mover e reescrever paths do compose (mais complexo,
  risco operacional); (b) backup logico + recriar vazio (desnecessario para esta entrega).
- **`.venv` 3.11.9 como padrao unico**: alinha com `.python-version`. `.pyenv/` e mantido como
  gerenciador de versao (ferramenta), ignorado pelo git, nao quarentenado. Alternativa descartada:
  promover `.venv-wsl` por renomeacao — preterida em favor de recriar `.venv` limpo a partir de
  `requirements.txt`.
- **`context_llm/` como fonte canonica**: possui `00_INDEX.md`, `README.md` e 17 docs numerados, e ja
  e force-included no `.gitignore`. `context/` (parcialmente versionado apesar de ignorado) tem valor
  apenas nos ADRs e guidelines, que sao migrados; o restante e quarentenado.

## Design de implementacao

### Contratos principais

Nao ha novos contratos de API, eventos ou interfaces de servico. Os contratos existentes (rotas
FastAPI em `src/interface/api/`, ports em `src/application/ports/`) sao **preservados sem alteracao**.
O "contrato" desta feature e operacional e expresso como invariantes de aceite:

- I1: Nenhum arquivo de `src/`, `tests/`, `scripts/`, `main.py`, `docker-compose.yml`, `README.md`,
  `.env.example`, `.gitignore` e scripts de execucao e movido para quarentena ou apagado.
- I2: `.env` permanece intocado e confirmado como ignorado pelo git (RF7).
- I3: Apos a renomeacao, nenhuma referencia ativa a `requeriments.txt` permanece em scripts, Docker
  ou documentacao (RF11).
- I4: `import main` e `from src.interface.api.main import app` continuam funcionando (RF15).

### Modelos de dados

Sem alteracao de schema, sem migracoes, sem mudanca de dados de negocio (Fora do escopo do PRD:
"Migracoes de dados de PostgreSQL/Qdrant ou mudancas de schema").

- **Dados a preservar (intocados no disco)**: `postgres_data/` (volume PostgreSQL), `qdrant_storage/`
  e `qdrant_snapshots/` (Qdrant), `data/*.db` (bases locais), `exports/`. Estes permanecem
  acessiveis; `exports/` e `logs/` sao quarentenados por serem regeneraveis, mas seu conteudo nao e
  destruido (apenas relocado).
- **Backup como gate do expurgo final**: antes de **esvaziar** a quarentena (delecao definitiva), o
  processo exige backup confirmado dos dados reais. Estrategia recomendada para o momento do expurgo:
  `pg_dump` do PostgreSQL e snapshot via API do Qdrant, mais copia dos `data/*.db`. Mover para
  quarentena **nao** exige backup, pois o dado permanece no disco (RF8 atendida no ponto de risco
  real).
- **`data/*.db`**: cobertos pelo `.gitignore` (`*.db`); o arquivo de mau caminho
  `C:\Users\arthu\.kiwifi-scraping\chat_history.db` (criado por engano na raiz) vai para
  `_quarantine/mistakes/`.

### Endpoints, jobs ou eventos

Nenhum endpoint, job ou evento e criado, alterado ou removido. Os pontos de entrada existentes sao
apenas **validados**:

- `main.py` -> reexporta `app` de `src.interface.api.main`.
- `run_app.sh` -> sobe Qdrant/Postgres via compose, inicializa schema (`scripts.init_db`), opcional
  reindex (`scripts.reindex`), inicia API (uvicorn) e Streamlit.
- Scripts `stop_app.sh`, `kill_streamlit.sh`, `reset_qdrant.sh`, `scripts/*.py` -> preservados.

### Erros e resiliencia

- **Validacoes (pre-condicoes do processo)**: confirmar que cada item movido nao pertence a I1 antes
  de mover; confirmar `.env` ignorado antes de prosseguir; verificar ausencia de referencias a
  `requeriments.txt` apos renomear (grep deve retornar vazio em scripts/Docker; ocorrencias apenas em
  PRD/historico sao aceitaveis).
- **Reversibilidade**: por ser quarentena (mover, nao apagar), qualquer item pode ser restaurado do
  `_quarantine/` ao caminho de origem. Mudancas em lotes pequenos com commits descritivos permitem
  reversao granular (RNF Resiliencia do PRD).
- **Idempotencia**: reexecucao do saneamento deve ser segura — itens ja movidos nao falham o
  processo; `.gitignore` aplica regras sem duplicar entradas.
- **Sem timeouts/retries/circuit breakers**: nao ha chamada externa nova nesta feature.

## Pontos de integracao

- **Git**: `git rm --cached` para o unico artefato versionado indevidamente
  (`context_llm/README.md:Zone.Identifier`), sem apagar do disco (vai para quarentena). Demais venvs e
  dados de runtime ja sao untracked (128 arquivos versionados no total, majoritariamente
  `src/`/`tests/`/docs), entao para eles basta `mv` para a quarentena e cobertura no `.gitignore`.
- **Docker Compose**: nao alterado; apenas validado que os mounts de dados continuam resolvendo para
  os diretorios mantidos na raiz.
- **Dados sensiveis**: `.env` tratado como secret, nunca movido nem versionado; nao deve aparecer em
  logs do processo ou no MANIFEST.

## Abordagem de testes

### Testes unitarios

A suite existente em `tests/unit/` deve continuar passando sem alteracao
(`test_campaign_metrics_extractor.py`, `test_chat_with_knowledge.py`,
`test_composite_candidate_source.py`, `test_ingest_use_case.py`, `test_product_mining_scorer.py`,
`test_scraping_enriched_candidate_source.py`). Nenhum teste novo de dominio e necessario, pois nao ha
nova regra de negocio. Garantir que `.pytest_cache/` quarentenado nao quebre a coleta (recriado pelo
pytest).

### Testes de integracao

Validacao de integracao via execucao real controlada (smoke), nao novos testes automatizados:

- `pytest` completo (unit + regression) verde apos cada lote de mudanca (RF14).
- `python -c "import main"` e `python -c "from src.interface.api.main import app"` sem erro (RF15).
- `tests/regression/test_legacy_vs_new_regression.py` permanece como rede de seguranca contra
  regressao funcional.

### Testes de contrato ou E2E backend

- **Smoke de inicializacao** do `run_app.sh` em modo `--skip-ingest --skip-db-init` (ou
  `--without-postgres-container` quando aplicavel) para confirmar que API e Streamlit sobem com os
  paths e o `.venv` novo. Sem testes de UI (escopo backend).
- Verificacao de ausencia de referencias quebradas: grep por `requeriments` em
  `run_app.sh`, `stop_app.sh`, `kill_streamlit.sh`, `reset_qdrant.sh`, `docker-compose.yml`,
  `README.md`, `docker/` e `scripts/` deve retornar vazio.

## Sequenciamento do desenvolvimento

### Ordem de construcao

1. **Branch e baseline**: criar branch `chore/organizacao-projeto`; rodar `pytest` e o smoke de
   import para registrar o baseline verde antes de qualquer mudanca.
2. **Auditoria e MANIFEST**: gerar relatorio classificado (MANTER/IGNORAR/QUARENTENA) de todos os
   itens de raiz e subpastas, com justificativa de uma linha (RF1) e MANIFEST inicial.
3. **`.gitignore` consolidado**: cobrir venvs, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.idea/`,
   `*.Zone.Identifier`, `logs/`, `exports/`, `qdrant_storage/`, `qdrant_snapshots/`, `postgres_data/`,
   `data/*.db`, `.env` e `_quarantine/` (RF6).
4. **Saneamento de versionamento**: `git rm --cached context_llm/README.md:Zone.Identifier` (e
   qualquer outro tracked indevido que a auditoria revele), sem apagar do disco (RF5).
5. **Quarentena por lotes** (commits pequenos): mover para `_quarantine/<categoria>/` os venvs
   redundantes, `backup_legacy/`, caches/builds, `exports/`, `logs/`, arquivo de mau caminho do
   Windows e Zone.Identifier. Confirmar `.env` ignorado (RF7).
6. **Ambiente virtual unico**: recriar `.venv` (Python 3.11.9) e instalar dependencias; manter
   `.pyenv/` como tool ignorado.
7. **Documentacao**: migrar `context/docs/adr/*` e `context/guidelines.md` para `context_llm/`
   (atualizando indices/links em `00_INDEX.md` e `README.md`), depois mover o restante de `context/`
   para `_quarantine/docs-extra/`; validar ausencia de links quebrados (RF10).
8. **Renomeacao de dependencias**: `requeriments.txt` -> `requirements.txt` e atualizar todas as
   referencias ativas (RF11).
9. **Confirmacao estrutural do backend**: documentar a Clean Architecture observada com evidencia e
   apontar inconsistencias de posicionamento sem move-las (RF12/RF13).
10. **Verificacao de integridade**: `pytest` verde, imports OK, `run_app.sh` sobe (RF14/RF15);
    entregar `git status` limpo, nova arvore de pastas e resumo do que foi quarentenado, ignorado,
    consolidado e renomeado.

### Dependencias tecnicas

- Acesso ao git para `rm --cached` e commits.
- Python 3.11.9 disponivel (via `.pyenv`) para recriar `.venv`.
- Servicos PostgreSQL e Qdrant (via Docker) para o smoke de inicializacao do `run_app.sh`.
- Nenhuma credencial nova, feature flag ou migracao de infraestrutura.

## Monitoramento e observabilidade

Feature sem comportamento de runtime novo; a "observabilidade" e a **trilha de auditoria da mudanca**:

- **MANIFEST de quarentena** (`_quarantine/MANIFEST.md` ou relatorio na pasta da feature): caminho de
  origem, categoria, motivo e data de cada item movido.
- **Commits pequenos e descritivos** por lote, servindo de log de auditoria reversivel.
- **Evidencia de testes**: saida de `pytest` e do smoke de import/inicializacao anexada ao
  entregavel.
- **`git status` final** limpo de artefatos e dados como sinal de sucesso.
- Logs de runtime da aplicacao (`logs/api.log`, `logs/streamlit.log`) permanecem como antes; apenas
  saem do versionamento. Nenhum secret pode aparecer no MANIFEST ou nos logs do processo.

## Seguranca e compliance

- **Autenticacao/autorizacao**: sem superficie nova; nada a alterar.
- **Secrets**: `.env` nunca movido, nunca versionado, nunca logado (RF7, rule `security-compliance`).
  Confirmar `git check-ignore .env` antes de concluir.
- **Dados sensiveis e privacidade**: dados de runtime (Postgres/Qdrant/`data/*.db`/`exports/`) e
  bases locais saem do versionamento; conteudo real preservado no disco. Nenhum dado sensivel deve
  vazar para o historico monitorado a partir desta entrega.
- **Retencao e auditoria**: backup retido como gate do expurgo final; MANIFEST + commits como trilha.
- **Validacao de entrada e abuso**: nao aplicavel (sem nova entrada externa).
- **Limites/protecao**: trabalho em branch dedicado, sem push sem solicitacao explicita, sem execucao
  antes da aprovacao do plano.

## Conformidade com rules

- **`backend-only.md`**: escopo limitado a backend/estrutura; Streamlit tratado apenas como consumidor
  preservado, sem especificar telas ou componentes.
- **`backend-architecture.md`**: padrao declarado explicitamente — Clean Architecture, com evidencia.
- **`clean-architecture.md`**: camadas e direcao de dependencia confirmadas e preservadas; nenhuma
  violacao introduzida.
- **`language-selection.md`**: stack Python declarada; convencoes Python preservadas (type hints,
  pytest, framework FastAPI/Streamlit existente mantido).
- **`data-persistence.md`**: sem mudanca de schema/migracao; dados sensiveis classificados e mantidos
  fora do versionamento; backup definido para o ponto de risco (expurgo).
- **`security-compliance.md`**: secrets via ambiente (`.env`) intocados; nenhum secret logado;
  auditoria por MANIFEST/commits.
- **`testing-observability.md`**: testes existentes preservados como gate (RF14); trilha de auditoria
  como sinal operacional.
- **`api-contracts.md`**: nao ha alteracao de contrato HTTP/evento; compatibilidade retroativa total.
- **`mvc-architecture.md`** e **`spring-boot.md`**: nao aplicaveis (nao e MVC; nao e JVM).

## Conformidade com skills

- **`python-backend`**: stack Python confirmada; convencoes (type hints, pytest, layout de pacotes,
  framework existente) preservadas na confirmacao estrutural.
- **`backend-architecture-patterns`** e **`backend-repo-structure`**: usadas para confirmar Clean
  Architecture e o posicionamento de `domain/application/infrastructure/interface`, apontando
  inconsistencias sem move-las.
- **`backend-code-standards`**: nomes em ingles e fronteiras mantidos; nenhuma reescrita de codigo.
- **`backend-testing`**: estrategia de validacao por `pytest` + smoke de import/inicializacao.
- **`backend-security`** e **`backend-data-persistence`**: tratamento de `.env`, dados de runtime e
  backup como gate.
- **`backend-observability`**: trilha de auditoria (MANIFEST, commits, evidencia de testes).
- **`context7`**: nao requerida — decisoes dependem apenas de padroes locais ja presentes no repo.

## Arquivos relevantes e dependentes

- **Manter (essenciais, intocados)**: `src/**`, `tests/**`, `scripts/**`, `main.py`,
  `docker-compose.yml`, `docker/`, `README.md`, `.env.example`, `.gitignore` (sera editado),
  `run_app.sh`, `stop_app.sh`, `kill_streamlit.sh`, `reset_qdrant.sh`, `context_llm/**`,
  `.python-version`.
- **Dados de runtime mantidos na raiz (gitignored)**: `postgres_data/`, `qdrant_storage/`,
  `qdrant_snapshots/`, `data/`.
- **Editados/renomeados**: `.gitignore`; `requeriments.txt` -> `requirements.txt`;
  `context_llm/00_INDEX.md` e `context_llm/README.md` (links apos migracao de ADRs/guidelines).
- **Para quarentena (`_quarantine/`)**: `.venv-linux/`, `.venv-wsl/`, `venv-project-kiwifi/`,
  `backup_legacy/`, `__pycache__/` (todos os niveis), `.pytest_cache/`, `.idea/`, `exports/`,
  `logs/`, `context/` (apos migracao), `C:\Users\arthu\.kiwifi-scraping\chat_history.db`,
  `context_llm/README.md:Zone.Identifier`.
- **Recriado**: `.venv/` (Python 3.11.9). **Mantido como tool ignorado**: `.pyenv/`.
- **Referencias a checar na renomeacao**: `run_app.sh`, `stop_app.sh`, `reset_qdrant.sh`,
  `kill_streamlit.sh`, `docker-compose.yml`, `docker/`, `README.md`, `scripts/**`, `context_llm/**`.

## Riscos conhecidos

- **Quebra de mounts ao mover dados de runtime**: mitigado mantendo `postgres_data/`,
  `qdrant_storage/`, `qdrant_snapshots/` na raiz; nunca quarentena-los.
- **Renomeacao de dependencias quebrando scripts/Docker** (RF11): mitigado por grep de verificacao
  pos-renomeacao em todos os pontos de uso; `run_app.sh`/compose nao fazem `pip install -r`, o que
  reduz o risco.
- **Divergencia de versao do Python** (3.12 em `.venv-linux` vs 3.11.9 alvo): mitigado recriando
  `.venv` a partir de `.pyenv`/`.python-version` e validando dependencias por `pytest`.
- **Links quebrados na consolidacao de docs** (RF10): mitigado atualizando `00_INDEX.md`/`README.md` e
  validando referencias apos migrar ADRs/guidelines.
- **Erosao estrutural acidental**: mitigado limitando a reorganizacao a posicionamento e apenas
  **apontando** inconsistencias (RF12/RF13), sem mover modulos nesta entrega.
- **Crescimento de disco pela quarentena**: aceito como trade-off temporario; expurgo gradual com
  backup como gate resolve.
- **Perda de dados no expurgo final**: mitigado pelo gate de backup confirmado (`pg_dump` + snapshot
  Qdrant + copia de `data/*.db`) antes de esvaziar `_quarantine/`.
