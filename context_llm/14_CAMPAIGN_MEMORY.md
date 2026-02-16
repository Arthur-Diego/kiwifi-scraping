# Memória de Campanhas (Timeline)

## Objetivo
Guardar o histórico cronológico para:
- entender o que foi feito
- correlacionar mudanças com resultados
- evitar repetir erros
- formar um “playbook” para campanhas futuras

## Entidades
### Campaign
- id, name, offer/platform (ClickBank etc.), geo, language, network, created_at

### CampaignEvent (timeline)
- id, campaign_id
- timestamp
- kind: METRICS | DECISION | NOTE | RESULT
- payload: dict (estruturado)
- tags: ["ctr","cpc","lp","bidding","policy"]

## Estrutura de payload (sugestão)
### METRICS
- date_range
- spend, impressions, clicks, ctr, cpc
- conversions, cpa, revenue, roas
- notes (opcional)

### DECISION
- change: (ex.: "Added negatives", "Changed bid strategy")
- reason/hypothesis
- expected_effect
- what_to_measure

### RESULT
- observed_effect
- comparison_window
- conclusion

## Como o chat usa a memória
- Sempre que o usuário cola métricas → registrar evento
- O assistente deve:
  - buscar eventos relacionados (últimos N dias + últimas decisões)
  - relacionar com trechos de transcrições (RAG)
  - sugerir próximos passos e checks

## Persistência (local-first)
- PostgreSQL (recomendado) OU JSONL por campanha
- Indexação opcional da timeline no Qdrant para busca semântica

## Export
- Export de campanha para Markdown (ótimo para revisar e treinar você mesmo)
