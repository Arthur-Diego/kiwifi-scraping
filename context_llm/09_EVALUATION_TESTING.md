# Avaliação e Testes

## Por que isso é crítico
RAG “quebra” silenciosamente quando você muda:
- chunking
- embeddings
- prompt
- top-k / filtros
Sem avaliação, você perde qualidade sem perceber.

---

## Avaliação (RAG)
### Dataset mínimo
Criar `tests/eval/questions.jsonl` com:
- pergunta
- intenção (ex.: keywords, LP, bidding, policy, tracking)
- “resposta esperada” (breve) OU “fontes esperadas” (arquivo/tema)

Exemplo (jsonl):
- {"q": "...", "tags":["ctr","cpc"], "expected_sources":["duvidas/.../video12"]}

### Métricas práticas
- **Recall@k**: a fonte correta aparece nos top-k?
- **Support rate**: % respostas com ao menos 1 fonte claramente relevante
- **Faithfulness (manual)**: resposta contradiz fontes?
- **Latency**: tempo total e por etapa (retrieval vs geração)

---

## Testes (pirâmide)
### Unit tests
- Splitter: não gerar chunks vazios
- Normalização: limpeza, metadados
- Parser de métricas: entradas variadas → saída consistente
- Regras de guardrails: sem fontes → resposta com incerteza

### Integration tests
- Indexar 2–3 transcrições pequenas “fake”
- Consultar Qdrant (top-k) e validar retorno com metadata

### E2E tests (smoke)
- Rodar app em modo headless (quando possível) ou testar use case:
  - “chat_with_knowledge” com mocks de LLM (para não gastar tokens)

---

## Estratégia de mocks (essencial)
- LLM: mockar geração e embeddings em testes
- Vector store: usar Qdrant local de teste OU fake in-memory
- Filesystem: fixtures em `tests/fixtures/`

---

## Critérios de aceite do MVP
- Top-k recupera trechos coerentes em perguntas comuns
- Respostas mostram fontes
- Memória de campanha registra e recupera eventos
- Suite de testes roda em < 2 min (ideal)
