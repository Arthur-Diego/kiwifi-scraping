# ADR 0002 - Embeddings e chunking semantico

Status: sugerido

Contexto:
- O pipeline usa SentenceTransformers `all-MiniLM-L6-v2` e chunking por similaridade.
- Configuracoes de tokens e overlap estao em `rag_qdrant/config.py`.

Decisao:
- Manter embeddings com SentenceTransformers e chunking semantico por similaridade.

Consequencias:
- Dependencias de NLP (sentence-transformers, sklearn, nltk, tiktoken).
- Custo de processamento maior do que chunking linear simples.
