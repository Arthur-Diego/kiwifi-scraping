# Regression Report - Legacy vs Refactored

Date: 2026-02-14

## Scope
Objective: verify functional equivalence (behavioral) between legacy implementation in `backup_legacy/` and refactored implementation in `src/`.

## Legacy Backup
All legacy code was moved (not deleted) to:

- `backup_legacy/controller`
- `backup_legacy/facade`
- `backup_legacy/diversos`
- `backup_legacy/llm`
- `backup_legacy/rag_qdrant`
- `backup_legacy/repository`
- `backup_legacy/service`
- `backup_legacy/ui`
- `backup_legacy/utils`

## Expected Behaviors (from legacy analysis)
1. Ingestion reads `.txt` files recursively and extracts folder-based metadata (`section`, `topic_hint`).
2. Chunking/indexing produces non-empty chunks for non-empty transcripts.
3. Embedding layer uses `SentenceTransformer` with normalized embeddings (`normalize_embeddings=True`).
4. Retrieval supports top-k behavior.
5. Chat with context returns non-empty answer.
6. Chat without context returns fallback message (`Nao encontrei base ...`).

## Regression Test Suite
Test file:

- `tests/regression/test_legacy_vs_new_regression.py`

Execution command:

```bash
python3 -m unittest discover -s tests/regression -v
```

## Results
Passed:
- `test_ingestion_loader_equivalence`
- `test_ingestion_generates_chunks`
- `test_embedding_contract_source_based`
- `test_retrieval_top_k_and_chat_non_empty`
- `test_chat_fallback_legacy_vs_new`
- `test_chat_context_usage_contract_source_and_runtime`

Failed:
- None

## Old vs New Comparison Notes
- Ingestion (runtime): legacy loader and new repository returned equivalent file/text/metadata for same input fixture.
- Chat fallback (contract + runtime): both preserve fallback semantics when no context exists.
- Retrieval/chat (runtime on new + legacy contract): top-k slicing and context-dependent response behavior validated.
- Embeddings (source contract): legacy and refactored adapters keep the same core embedding strategy contract (SentenceTransformer + normalized vectors).

## Relevant Differences
1. Refactored ingestion now uses semantic chunking by default (adapter in `src/infrastructure/chunking/semantic_chunker.py`) with char-window fallback for safety.
2. Some comparisons are source-contract based (not full runtime legacy execution) due missing runtime dependencies in environment (`dotenv`, `numpy`, `pytest`).

## Risks Detected
1. Full runtime parity of legacy embedding/retrieval against real providers (Qdrant, HF models, OpenAI/LangChain) was not executed in this environment.
2. Legacy service modules moved to backup are no longer active entrypoints; operational commands should target `src/interface/*` and `scripts/`.
3. Deprecation warning observed for `datetime.utcnow()` path in chunk creation.

## Recommendation
Run an integration pass in a fully provisioned environment (Qdrant + sentence-transformers + langchain-openai + pytest) to close the remaining parity risk on external dependencies.
