# kiwifi-scraping

Refatoracao para arquitetura hexagonal (ports and adapters) de um sistema RAG local-first para transcricoes de videos sobre Google Ads.

## Estrutura principal

```text
src/
  domain/
  application/
  infrastructure/
  interface/
tests/
scripts/
```

## Como rodar

1. Suba o Qdrant local:

```bash
docker compose up -d
```

2. Configure `.env` com pelo menos:

```bash
OPENAI_API_KEY=...
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=transcricoes
QDRANT_EMBEDDER_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

3. Reindexe transcricoes:

```bash
python -m scripts.reindex --inputs data
```

4. Rode a API:

```bash
uvicorn main:app --reload
```

5. Rode a interface Streamlit:

```bash
streamlit run ui/chat_app.py
```

## Compatibilidade legada

- `service/rag_service.py` continua disponivel, agora usando use cases.
- `repository/qdrant_repository.py` e `repository/qdrant_sections_repository.py` continuam com a mesma API externa.
- `rag_qdrant/main.py` continua com os mesmos argumentos CLI.

## Testes

```bash
pytest tests/unit -q
```
