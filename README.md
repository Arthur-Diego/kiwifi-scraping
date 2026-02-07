# kiwifi-scraping

**Resumo**
- Projeto em Python para scraping de aulas na Kiwify, captura de URLs de video, download e extracao de audio, transcricao e pipeline RAG com Qdrant.
- Inclui API FastAPI e apps Streamlit para consulta e dashboards.

**Como rodar**
- Qdrant: ha `docker-compose.yml` com servico `qdrant` e portas 6333/6334.
- API: app FastAPI em `main.py` com rotas em `controller/controller_fast_api.py`.
- Streamlit: apps em `ui/` (ex.: `ui/chat_app.py`, `ui/app_with_sections.py`).
- Pipeline RAG: CLI em `rag_qdrant/main.py` com argumentos `--inputs`, `--export`, `--collection`, `--date`, `--section`.
- Scraping local: `controller/controller.py` e `service/scraping_service.py` possuem bloco `__main__`.
- Variaveis de ambiente (scraping Kiwify):
  - `KIWIFY_EMAIL`
  - `KIWIFY_PASSWORD`
  - `KIWIFY_URL_INICIAL` (opcional; se nao definido, `controller/controller.py` usa um default)
- Comandos sugeridos (nao identificados no repo; assumindo comandos padrao):
- Qdrant:
```bash
docker compose up -d
```
- API:
```bash
uvicorn main:app --reload
```
- Streamlit (exemplo):
```bash
streamlit run ui/chat_app.py
```
- Pipeline RAG (exemplo):
```bash
python -m rag_qdrant.main --inputs data
```

**Stack detectada**
- Python 3.x (inferido pelos arquivos .py e libs modernas)
- FastAPI, Uvicorn
- Selenium, selenium-wire, webdriver-manager
- Qdrant + sentence-transformers
- LangChain + OpenAI
- Whisper + Torch
- Streamlit, Plotly, Pandas
- NLTK, tiktoken
- ffmpeg (invocado via subprocess)

**Estrutura de pastas**
- `controller/`: entrada de API e controller local.
- `service/`: scraping, processamento de video/voz, RAG.
- `facade/`: orquestracao (fachada) do fluxo de extracao.
- `repository/`: acesso ao Qdrant.
- `rag_qdrant/`: pipeline de ingestao e indexacao.
- `llm/`: cliente LLM via LangChain/OpenAI.
- `ui/`: apps Streamlit.
- `utils/`: utilitarios de transcricao.
- `diversos/`: scripts avulsos (transcricao, audio).
- `data/`: historico e relatorios.
- `exports/`: exportacoes JSONL de chunks.
- `qdrant_storage/` e `qdrant_snapshots/`: persistencia Qdrant.
- `Análise da Campanha de Topo e Configuração de Pixel a nível de MCC/`: midias de entrada/saida de processamento.

**Contexto adicional**
- `State.local.md`
- `context/`
- `docs/adr/`
