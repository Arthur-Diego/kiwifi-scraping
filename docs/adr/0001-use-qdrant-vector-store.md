# ADR 0001 - Usar Qdrant como vector store

Status: sugerido

Contexto:
- O repo possui `docker-compose.yml` para Qdrant e repositorios que consultam `localhost:6333`.
- O pipeline RAG grava e consulta embeddings na colecao `transcricoes`.

Decisao:
- Manter Qdrant como banco vetorial principal para busca semantica.

Consequencias:
- Requer servico Qdrant rodando localmente (ou configuracao equivalente).
- Dados vetoriais ficam persistidos em `qdrant_storage/` e snapshots em `qdrant_snapshots/`.
