# State.local.md

<!-- AUTO-UPDATE-START -->
- Atualizado em: 2026-02-07
- Arquivos alterados detectados: nao identificado (script ainda nao executado)
<!-- AUTO-UPDATE-END -->

- Snapshot atual do projeto:
- API FastAPI exposta em `main.py` com rotas em `controller/controller_fast_api.py`.
- Scraping Kiwify via Selenium/Selenium Wire em `service/scraping_service.py`.
- Processamento de video e audio via `ffmpeg` em `service/video_processor_service.py`.
- Pipeline RAG em `rag_qdrant/` com Qdrant e SentenceTransformers.
- UI Streamlit em `ui/` com chat e dashboards.
- Dados locais em `data/` e em `Análise da Campanha de Topo e Configuração de Pixel a nível de MCC/`.

- Areas mais ativas:
- nao identificado (sem historico de commits ou telemetria)

- Debitos tecnicos detectaveis:
- Credenciais hardcoded em `service/scraping_service.py`.
- Caminho absoluto hardcoded em `utils/transcript_processor_utils.py`.
- Ausencia de suite de testes automatizados.
- `ui/chat_history_dashboard.py` chama `run_rag` com parametros que nao existem na assinatura atual.
- `controller/controller.py` usa URL hardcoded.
- `service/scraping_service.py` possui imports duplicados e bloco `__main__` chama `KiwifyScraper()` sem argumento.

- TODOs inferiveis:
- Externalizar credenciais e URLs em `.env` ou configuracao.
- Parametrizar caminhos de entrada/saida e remover paths absolutos.
- Alinhar assinaturas entre UI e `service/rag_service.py`.
- Adicionar testes basicos de integracao/contrato.
