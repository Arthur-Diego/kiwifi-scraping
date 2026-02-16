# QDRANT_DOC.md

## Objetivo
Documentar a lógica **atual** de ingestão para Qdrant no projeto, do ponto de entrada CLI até o upsert final dos vetores.

---

## 1) Fluxo de execução (visão geral)

### Ponto de entrada
- Arquivo: `scripts/reindex.py`
- Comando típico:
  - `python -m scripts.reindex --inputs <caminhos> --collection transcricoes`

### Sequência
1. `scripts/reindex.py` parseia argumentos (`--inputs`, `--collection`, `--chunk-size`, `--chunk-overlap`).
2. Chama `build_ingest_use_case(AppConfig())` em `src/infrastructure/wiring.py`.
3. O `wiring` monta dependências da ingestão:
   - `LocalTranscriptRepository`
   - `QdrantVectorStore`
   - `SemanticChunker`
   - `StdLogger`
4. O caso de uso `IngestTranscriptsUseCase.execute(...)` orquestra:
   - leitura recursiva dos `.txt`
   - chunking semântico (com fallback)
   - criação dos objetos `KnowledgeChunk`
   - upsert em lote no Qdrant
5. Retorna `IngestTranscriptsOutput(files_indexed, chunks_indexed)`.

---

## 2) Arquivos e responsabilidades

## `scripts/reindex.py`
- Responsável somente por CLI e chamada do use case.
- Não contém regra de negócio de chunking/indexação.

## `src/infrastructure/wiring.py`
- Monta a ingestão com **embedder único compartilhado**:
  - `shared_embedder = SentenceTransformer(cfg.embedder_model)`
  - `SemanticChunker(embedder=shared_embedder)`
  - `QdrantVectorStore(embedder=shared_embedder, qdrant_url=...)`
- Esse compartilhamento evita carregar modelo duas vezes no mesmo pipeline.

## `src/infrastructure/fs/local_transcript_repository.py`
- Lê arquivos `.txt` de forma recursiva.
- Aceita:
  - caminho de arquivo único
  - caminho de diretório
- Extrai metadata de pasta:
  - `section` = primeiro nível relativo
  - `topic_hint` = segundo nível relativo

## `src/application/use_cases/ingest_transcripts.py`
- Orquestra ingestão com regras principais:
  - percorre `iter_transcripts(...)`
  - chunkifica cada documento
  - gera `chunk_id` determinístico por:
    - `source_path`
    - `chunk_index`
    - hash (`sha1`) do texto do chunk
  - envia tudo para `vector_store.upsert_chunks(...)`
- Fallback de chunking:
  - tenta chunker semântico primeiro
  - se falhar, usa janela de caracteres (`chunk_size_chars`, `chunk_overlap_chars`)

## `src/infrastructure/chunking/token_tools.py`
- Utilitários de tokens e segmentação de sentenças.
- Usa `tiktoken` quando disponível.
- Se `tiktoken` não existir, cai para contagem aproximada por `split()`.

## `src/infrastructure/chunking/semantic_chunker.py`
- Chunking semântico estilo legado:
  - split em sentenças
  - conta tokens por sentença
  - embeddings por sentença
  - quebra quando:
    - ultrapassa `max_tokens_per_chunk`, ou
    - similaridade entre sentenças consecutivas cai abaixo de `similarity_break_threshold` e já atingiu tamanho-alvo
  - aplica overlap por tokens
  - para arquivos grandes (`max_tokens_per_file`), cria macro-janelas e reaplica chunking fino

### Config padrão (`SemanticChunkerConfig`)
- `target_tokens_per_chunk = 350`
- `max_tokens_per_chunk = 500`
- `overlap_tokens = 60`
- `max_tokens_per_file = 10000`
- `similarity_break_threshold = 0.40`

## `src/infrastructure/vectorstores/qdrant_store.py`
- Cria cliente Qdrant e faz upsert/busca.
- `upsert_chunks(...)`:
  - garante coleção (`_ensure_collection`)
  - gera embeddings dos chunks em lote
  - faz `upsert` em batches (`batch_size=128`) para evitar payload HTTP grande
- Coleção é criada com:
  - `distance = COSINE`
  - dimensão inferida do embedder (`get_sentence_embedding_dimension()`)

---

## 3) Payload salvo no Qdrant

Cada ponto inclui:
- `id` (chunk id determinístico)
- `vector` (embedding do chunk)
- `payload`:
  - `text`
  - `source_file`
  - `source_path`
  - `chunk_index`
  - `section`
  - `topic_hint`
  - `transcript_version`

---

## 4) Compatibilidade com versões do `qdrant-client`

Na busca (`search`):
- se existir `client.search(...)`, usa esse método
- se não existir, usa `client.query_points(...)` com `NearestQuery`

Se ocorrer erro interno do Qdrant (`OutputTooSmall`/500):
- fallback para busca via `scroll + cosine local` (`_search_points_fallback_by_scroll`)

---

## 5) Persistência de dados

A persistência do Qdrant está no `docker-compose.yml`:
- `./qdrant_storage:/qdrant/storage`
- `./qdrant_snapshots:/qdrant/snapshots`

Isso mantém os dados entre reinicializações, desde que não seja usado `docker compose down -v`.

---

## 6) Pontos de atenção (estado atual)

1. `scripts/reindex.py` importa `wiring`; por isso depende do ambiente de runtime ter libs de ingestão instaladas.
2. Existe TODO no use case para manifesto incremental:
   - `.index_manifest.json` (hash/versionamento) ainda não implementado.
3. Fallback por janela de caracteres permanece ativo como proteção operacional.

---

## 7) Comandos úteis

## Reindex
```bash
python -m scripts.reindex --inputs "<CAMINHO_TRANSCRICOES>" --collection transcricoes
```

## Reset + reindex (script auxiliar)
```bash
./reset_qdrant.sh --with-reindex --transcripts "<CAMINHO_TRANSCRICOES>"
```

## Subir app sem reindex
```bash
./run_app.sh --skip-ingest
```

