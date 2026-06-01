# Tarefa 1.0: Higiene de repositorio via quarentena e confirmacao estrutural do backend

## Visao geral

Entrega unica de higiene de repositorio + confirmacao estrutural do backend, sem qualquer mudanca de
comportamento funcional. Adota o **modelo de quarentena**: todo item nao essencial e movido para
`_quarantine/` (ignorado pelo git, organizado por categoria) para expurgo gradual e reversivel pelo
mantenedor, em vez de delecao imediata. Inclui consolidacao do `.gitignore`, saneamento de
versionamento, padronizacao de um unico `.venv` (Python 3.11.9), consolidacao de documentacao,
renomeacao de `requeriments.txt` para `requirements.txt`, documentacao da Clean Architecture existente
e verificacao de integridade (`pytest`, imports e `run_app.sh`). Dados de runtime ativos permanecem na
raiz para nao quebrar os mounts do `docker-compose.yml`.

## Conformidade com rules

- `backend-only.md`: escopo limitado a backend/estrutura; Streamlit apenas preservado como consumidor.
- `backend-architecture.md`: padrao declarado explicitamente — Clean Architecture, com evidencia.
- `clean-architecture.md`: camadas e direcao de dependencia confirmadas e preservadas; sem violacao.
- `language-selection.md`: stack Python; convencoes preservadas (type hints, pytest, FastAPI/Streamlit).
- `data-persistence.md`: sem mudanca de schema/migracao; dados sensiveis fora do versionamento; backup
  como gate do expurgo final.
- `security-compliance.md`: `.env` intocado e ignorado; nenhum secret logado; auditoria por
  MANIFEST/commits.
- `testing-observability.md`: testes existentes preservados como gate; trilha de auditoria como sinal
  operacional.
- `api-contracts.md`: nenhuma alteracao de contrato HTTP/evento; compatibilidade retroativa total.
- Nao aplicaveis: `mvc-architecture.md`, `spring-boot.md`.

## Conformidade com skills

- `python-backend`: convencoes Python e layout de pacotes preservados na confirmacao estrutural.
- `backend-architecture-patterns` e `backend-repo-structure`: confirmar Clean Architecture e
  posicionamento `domain/application/infrastructure/interface`, apontando inconsistencias sem mover.
- `backend-code-standards`: nomes e fronteiras mantidos; sem reescrita de codigo.
- `backend-testing`: validacao por `pytest` + smoke de import/inicializacao.
- `backend-security` e `backend-data-persistence`: tratamento de `.env`, dados de runtime e backup.
- `backend-observability`: trilha de auditoria (MANIFEST, commits, evidencia de testes).
- `context7`: nao requerida — decisoes dependem de padroes locais ja presentes no repo.

## Requisitos

- RF1: produzir lista classificada (MANTER/IGNORAR/QUARENTENA) de todos os itens antes de qualquer
  movimentacao ou alteracao de versionamento.
- RF5: artefatos/dados versionados indevidamente saem do versionamento sem apagar o conteudo real
  (`git rm --cached`), sendo relocados para a quarentena.
- RF6: `.gitignore` cobre venvs, caches, builds, `.idea/`, `*.Zone.Identifier`, `logs/`, `exports/`,
  dados de runtime, `data/*.db`, `.env` e `_quarantine/`.
- RF7: `.env` permanece intocado e confirmado como ignorado.
- RF8: backup confirmado como **gate do expurgo final** da quarentena (mover nao exige backup).
- RF3/RF4: manter exatamente um padrao de ambiente virtual (`.venv`, Python 3.11.9); demais venvs para
  quarentena; `.pyenv/` mantido como tool ignorado.
- RF9: apenas itens aprovados como QUARENTENA sao movidos; nada essencial e tocado.
- RF10: documentacao consolidada sem links quebrados (ADRs/guidelines migrados para `context_llm/`).
- RF11: apos renomear `requeriments.txt` -> `requirements.txt`, nenhuma referencia ao nome antigo
  permanece ativa em scripts/Docker/docs.
- RF12/RF13: estrutura de camadas documentada com evidencia, preservando o comportamento (sem mover
  modulos).
- RF14/RF15: testes existentes passam; `main.py` e `run_app.sh` continuam importando e iniciando.
- Invariantes (Tech Spec): nao mover/apagar `src/`, `tests/`, `scripts/`, `main.py`,
  `docker-compose.yml`, `README.md`, `.env.example`, `.gitignore`, scripts de execucao; manter
  `postgres_data/`, `qdrant_storage/`, `qdrant_snapshots/` na raiz.

## Subtarefas

- [x] 1.1 Criar branch `chore/organizacao-projeto`; registrar baseline verde: `pytest` e
  `python -c "import main"` / `from src.interface.api.main import app`.
- [x] 1.2 Gerar relatorio de auditoria classificado (MANTER/IGNORAR/QUARENTENA) de raiz e subpastas,
  com justificativa de uma linha (RF1); criar `_quarantine/MANIFEST.md` inicial e documentar a
  politica de backup como gate do expurgo final (RF8).
- [x] 1.3 Consolidar `.gitignore` cobrindo venvs, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.idea/`,
  `*.Zone.Identifier`, `logs/`, `exports/`, `qdrant_storage/`, `qdrant_snapshots/`, `postgres_data/`,
  `data/*.db`, `.env` e `_quarantine/` (RF6); confirmar `.env` ignorado via `git check-ignore` (RF7).
- [x] 1.4 Sanear versionamento: `git rm --cached context_llm/README.md:Zone.Identifier` (e outros
  tracked indevidos revelados pela auditoria), sem apagar do disco (RF5).
- [x] 1.5 Criar `_quarantine/` com subpastas `venvs/`, `legacy/`, `artifacts/`, `runtime-regen/`,
  `docs-extra/`, `mistakes/`; mover por lotes (commits pequenos): `.venv-linux/`, `.venv-wsl/`,
  `venv-project-kiwifi/` -> `venvs/`; `backup_legacy/` -> `legacy/`; `__pycache__/`, `.pytest_cache/`,
  `.idea/` -> `artifacts/`; `exports/`, `logs/` -> `runtime-regen/`;
  `C:\Users\arthu\.kiwifi-scraping\chat_history.db` e o `*.Zone.Identifier` -> `mistakes/`. Confirmar
  que `postgres_data/`, `qdrant_storage/`, `qdrant_snapshots/` **permanecem na raiz** (RF9).
- [x] 1.6 Padronizar ambiente virtual unico: recriar `.venv` em Python 3.11.9 (via `.pyenv`) e
  instalar dependencias; manter `.pyenv/` como tool ignorado (RF3/RF4).
- [x] 1.7 Consolidar documentacao: migrar `context/docs/adr/*` e `context/guidelines.md` para
  `context_llm/`, atualizar `context_llm/00_INDEX.md` e `context_llm/README.md`, mover o restante de
  `context/` para `_quarantine/docs-extra/`; validar ausencia de links quebrados (RF10).
- [x] 1.8 Renomear `requeriments.txt` -> `requirements.txt` e atualizar todas as referencias ativas;
  verificar por grep que `requeriments` nao aparece em `run_app.sh`, `stop_app.sh`, `kill_streamlit.sh`,
  `reset_qdrant.sh`, `docker-compose.yml`, `docker/`, `README.md`, `scripts/**`, `context_llm/**`
  (RF11).
- [x] 1.9 Documentar a Clean Architecture observada com evidencia (`domain`/`application`/
  `infrastructure`/`interface`, ports e wiring) e apontar inconsistencias de posicionamento sem mover
  modulos (RF12/RF13).
- [x] 1.10 Verificacao de integridade pos-mudanca: `pytest` verde; imports OK; smoke de `run_app.sh`
  (ex.: `--skip-ingest --skip-db-init`); entregar `git status` limpo, nova arvore de pastas e resumo do
  que foi quarentenado, ignorado, consolidado e renomeado (RF14/RF15).

## Referencias tecnicas

- Tech Spec: `tasks/prd-refactor_project_spec-driven/techspec.md`
  - "Visao dos componentes" (estrutura de `_quarantine/`), "Decisoes de arquitetura" (quarentena, dados
    na raiz, `.venv` 3.11.9, `context_llm` canonico).
  - "Design de implementacao" -> invariantes I1-I4; "Modelos de dados" -> backup como gate.
  - "Sequenciamento do desenvolvimento" -> ordem de construcao em 10 passos.
  - "Seguranca e compliance" -> `.env`, dados sensiveis, auditoria.
- PRD: `tasks/prd-refactor_project_spec-driven/prd.md` (RF1-RF15).

## Padrao arquitetural

Clean Architecture (confirmada por evidencia em `src/`). Esta tarefa **nao altera** fronteiras nem
move modulos entre camadas: apenas confirma e documenta o padrao (`domain` -> `application/{ports,
use_cases,services}` -> `infrastructure` -> `interface`), com dependencias apontando para dentro, e
aponta inconsistencias para tratamento futuro (RF12/RF13).

## Criterios de sucesso

- Relatorio classificado produzido antes de qualquer mudanca (RF1).
- `.gitignore` cobre todos os itens exigidos e `_quarantine/`; `git check-ignore .env` confirma `.env`
  ignorado (RF6/RF7).
- `git status` limpo de artefatos e dados de runtime; `README.md:Zone.Identifier` fora do versionamento
  sem ter sido apagado do disco (RF5).
- Exatamente um ambiente virtual padrao (`.venv`, 3.11.9); venvs redundantes na quarentena; `.pyenv/`
  preservado (RF3/RF4).
- Itens nao essenciais movidos para `_quarantine/<categoria>/`; nenhum item essencial tocado; dados de
  runtime na raiz com mounts intactos (RF9).
- ADRs/guidelines migrados para `context_llm/` sem links quebrados; restante de `context/` quarentenado
  (RF10).
- Nenhuma referencia ativa a `requeriments.txt` (grep vazio nos pontos de uso) (RF11).
- Estrutura de camadas documentada com evidencia; comportamento preservado (RF12/RF13).
- `pytest` verde; `main.py` e `run_app.sh` importam e iniciam (RF14/RF15).
- MANIFEST + commits pequenos como trilha de auditoria; `.env` nunca exposto em logs/MANIFEST.

## Testes da tarefa

- [ ] Testes unitarios: suite `tests/unit/` continua verde sem alteracao (validacao de nao-regressao,
  RF14).
- [ ] Testes de integracao: `tests/regression/test_legacy_vs_new_regression.py` verde; smoke de
  inicializacao via `run_app.sh` (API uvicorn + Streamlit sobem com o `.venv` novo e os paths
  mantidos).
- [ ] Testes de contrato ou E2E backend: smoke de import (`python -c "import main"` e
  `from src.interface.api.main import app`); verificacao por grep de ausencia de referencias a
  `requeriments`; `git check-ignore` para `.env` e `_quarantine/`. Sem testes de UI.

## Arquivos relevantes

- Manter (intocados): `src/**`, `tests/**`, `scripts/**`, `main.py`, `docker-compose.yml`, `docker/`,
  `README.md`, `.env.example`, scripts de execucao (`run_app.sh`, `stop_app.sh`, `kill_streamlit.sh`,
  `reset_qdrant.sh`), `context_llm/**`, `.python-version`.
- Dados de runtime mantidos na raiz (gitignored): `postgres_data/`, `qdrant_storage/`,
  `qdrant_snapshots/`, `data/`.
- Editados/renomeados: `.gitignore`; `requeriments.txt` -> `requirements.txt`;
  `context_llm/00_INDEX.md`, `context_llm/README.md` (links pos-migracao).
- Para `_quarantine/`: `.venv-linux/`, `.venv-wsl/`, `venv-project-kiwifi/`, `backup_legacy/`,
  `__pycache__/` (todos os niveis), `.pytest_cache/`, `.idea/`, `exports/`, `logs/`, `context/`
  (apos migracao), `C:\Users\arthu\.kiwifi-scraping\chat_history.db`,
  `context_llm/README.md:Zone.Identifier`.
- Recriado: `.venv/` (3.11.9). Mantido como tool ignorado: `.pyenv/`.
- Novos: `_quarantine/` e `_quarantine/MANIFEST.md`.
