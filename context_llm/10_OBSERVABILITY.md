# Observabilidade (Logs, Métricas, Auditoria)

## Objetivo
Você precisa saber:
- que pergunta foi feita
- quais chunks foram recuperados
- qual resposta foi dada
- que ações foram sugeridas
- qual campanha/timeline estava ativa

## Logs recomendados (estrutura)
- `trace_id` por interação
- `campaign_id` (se houver)
- query do usuário
- top-k resultados (ids + scores + source_file)
- prompt final (ou hash)
- resposta final (ou hash)
- duração por etapa

## Onde armazenar (local-first)
- arquivo `.jsonl` em `./runs/logs/`
- opcional: PostgreSQL

## Métricas úteis
- latência total
- tempo de retrieval
- tempo de geração
- taxa de “sem fontes”
- tamanho médio do contexto
- custos (se usar API): tokens in/out (estimado)

## UI
- botão “ver fontes” (já)
- botão “abrir log da última resposta”
- export de conversa/campanha

## Debug
Modo debug mostra:
- query rewrite (se existir)
- filtros aplicados no retriever
- chunks e scores
