# Review: Task 1.0 - Higiene de repositorio via quarentena e confirmacao estrutural do backend

**Revisor**: AI Backend Task Reviewer
**Data**: 2026-06-01
**Arquivo da task**: 1_task.md
**Status**: APROVADO COM OBSERVACOES

## Resumo

A task de higiene de repositorio foi executada no modelo de quarentena, sem mudanca de comportamento
funcional. Venvs redundantes, caches, artefatos de IDE, `exports/`, `logs/`, arquivos criados por
engano e a documentacao sobreposta `context/` foram movidos para `_quarantine/` (ignorado pelo git);
ADRs e guidelines foram migrados para a fonte canonica `context_llm/`; `.gitignore` foi consolidado;
`requeriments.txt` foi renomeado para `requirements.txt` (e re-encodado de UTF-16 para UTF-8); e a
estrutura de camadas (Clean Architecture) foi documentada com evidencia e inconsistencias apontadas.
Os dados de runtime ativos permaneceram na raiz para preservar os mounts do compose. A suite manteve
o mesmo resultado do baseline (17 passados, 2 falhas pre-existentes), sem regressao introduzida.

## Contexto

- PRD: `tasks/prd-refactor_project_spec-driven/prd.md`
- Tech Spec: `tasks/prd-refactor_project_spec-driven/techspec.md`
- Arquitetura: Clean Architecture
- Stack: Python 3.11.9 (FastAPI + Streamlit + Qdrant + PostgreSQL + LangChain/OpenAI)
- Rules aplicadas: `backend-only`, `backend-architecture`, `clean-architecture`, `language-selection`,
  `data-persistence`, `security-compliance`, `testing-observability`, `api-contracts`
- Skills aplicadas: `python-backend`, `backend-architecture-patterns`, `backend-repo-structure`,
  `backend-code-standards`, `backend-testing`, `backend-security`, `backend-data-persistence`,
  `backend-observability`

## Arquivos revisados

| Arquivo | Status | Observacoes |
| --- | --- | --- |
| `.gitignore` | OK | Cobre venvs, caches, builds, `.idea/`, `*.Zone.Identifier`, `logs/`, `exports/`, dados de runtime, `data/*.db`, `.env`, `_quarantine/`; exceção `!.env.example`. |
| `requirements.txt` (novo) | OK | UTF-8 limpo; `requeriments.txt` removido; parseavel por pip. |
| `context_llm/docs/adr/*` | OK | Migrado via `git mv` (historico preservado). |
| `context_llm/guidelines.md` | OK | Migrado via `git mv`. |
| `context_llm/00_INDEX.md` | OK | Secao "Documentos adicionais" referencia adr/ e guidelines. |
| `context_llm/FOLDER_STRUCTURE.md` | OK | Reescrito para a arvore real + evidencia + inconsistencias. |
| `_quarantine/MANIFEST.md` (novo) | OK | Trilha de auditoria: origem->destino->motivo + gate de backup. |
| `.env.example` | OK | Agora versionavel (estava ignorado por engano); apenas placeholders. |
| `src/**` | OK (intocado) | Nenhuma alteracao funcional; imports validados. |

## Problemas encontrados

### CRITICO

Nenhum problema critico encontrado. Nenhum dado real foi apagado (modelo de quarentena preserva tudo
no disco); `.env` intocado e confirmado como ignorado; nenhum segredo exposto.

### MAJOR

Nenhum problema major bloqueante encontrado. Registrados como desvios documentados e aprovados:

- **Desvio do venv (decisao do usuario "recriar do zero")**: `.venv` foi promovido a partir de
  `.venv-wsl` (ja 3.11.9 com dependencias) em vez de recriado via `pip install`, por causa do peso de
  `torch`+CUDA/sentence-transformers. End-state equivalente (um unico `.venv` em 3.11.9). Documentado
  no MANIFEST com o comando de recriacao limpa.
- **`backup_legacy/` retido contra a premissa do PRD**: a auditoria revelou que
  `tests/regression/test_legacy_vs_new_regression.py` importa de `backup_legacy`; remove-lo quebraria
  a coleta de testes. Mantido na raiz (ignorado, como antes) — preserva RF13/RF14.

### MINOR

- **2 falhas de teste pre-existentes** (`test_campaign_metrics_extractor::test_extract_metrics_from_free_text_prompt`
  e `test_scraping_enriched_candidate_source::test_extract_first_price_handles_formats`) existiam no
  baseline (ligadas a modificacoes nao commitadas anteriores) e estao fora do escopo desta task. Nao
  foram corrigidas; recomenda-se tratamento em task propria.
- **Smoke vivo de `run_app.sh` nao executado** ponta a ponta (sobe Docker/servidores). Validado por
  `bash -n` (sintaxe), existencia dos apps Streamlit referenciados e imports de `main`/`app`.

## Destaques positivos

- Modelo de quarentena reversivel elimina risco de perda irreversivel e mantem trilha de auditoria
  (MANIFEST + `git mv`/`git rm --cached`).
- Auditoria pegou a dependencia oculta `backup_legacy` antes de causar regressao — corrigido em ciclo.
- Correcao de bug latente: `.env.example` estava sendo ignorado por engano e agora pode ser versionado.
- Re-encode do `requirements.txt` (UTF-16 -> UTF-8) alem da renomeacao, alinhando com ferramentas.
- Dados de runtime preservados na raiz, respeitando os mounts do `docker-compose.yml`.

## Conformidade

| Area | Status | Observacoes |
| --- | --- | --- |
| PRD | OK | RF1-RF15 atendidos; desvio de docs (quarentena vs consolidacao total) aprovado pelo usuario. |
| Tech Spec | OK | Invariantes I1-I4 mantidas; dados na raiz; `.venv` 3.11.9. |
| Task | OK | 10 subtarefas concluidas. |
| Arquitetura | OK | Clean Architecture preservada; nenhum modulo movido entre camadas. |
| API/Contratos | NA | Nenhuma alteracao de contrato HTTP/evento. |
| Dados/Persistencia | OK | Sem mudanca de schema; dados reais preservados; gate de backup definido. |
| Seguranca | OK | `.env` ignorado e intocado; `.env.example` sem segredos; nada hardcoded/logado. |
| Observabilidade | OK | Trilha de auditoria via MANIFEST e index de docs atualizado. |
| Testes | OK | Sem regressao: 17 passados / 2 falhas pre-existentes, igual ao baseline. |

## Testes e comandos

| Comando | Resultado | Observacoes |
| --- | --- | --- |
| `.venv/bin/python -m pytest tests -q` | PASSOU (com ressalva) | 17 passed, 2 failed (pre-existentes, fora de escopo). |
| `python -c "import main; from src.interface.api.main import app"` | PASSOU | RF15 (imports OK). |
| `bash -n run_app.sh` | PASSOU | Sintaxe OK; apps Streamlit referenciados existem. |
| `git check-ignore .env` | PASSOU | `.env` ignorado (RF7). |
| `pip install --dry-run -r requirements.txt` | PASSOU | requirements parseavel (RF11). |
| grep `requeriments` em scripts/docker/docs | PASSOU | Nenhuma referencia ativa (RF11). |
| `run_app.sh` smoke vivo (Docker + servidores) | NAO EXECUTADO | Requer subir Docker/servicos; validado por sintaxe + imports. |

## Recomendacoes

1. Tratar as 2 falhas de teste pre-existentes em task dedicada (nao introduzidas por esta task).
2. Antes de esvaziar `_quarantine/`, seguir o gate de backup do MANIFEST (`pg_dump` + snapshot Qdrant).
3. Opcional: executar um smoke vivo de `run_app.sh --skip-ingest --skip-db-init` em ambiente com Docker
   para validacao ponta a ponta da inicializacao.
4. Avaliar versionar `backup_legacy/` (ou refatorar o teste de regressao) para que a suite passe em
   clone limpo.

## Veredito

APROVADO COM OBSERVACOES. A task cumpre os objetivos do PRD e da Tech Spec sem regressao funcional e
sem risco de perda de dados (quarentena reversivel). Os desvios (reuso do venv e retencao de
`backup_legacy`) sao justificados, documentados e nao bloqueantes. Proximo passo sugerido: revisar o
`git status` final e decidir sobre os commits (separados das mudancas pre-existentes nao relacionadas)
antes de seguir para QA.
