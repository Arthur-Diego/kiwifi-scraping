# Personas e Jornadas

## Persona principal
**Você (Dev + Operador de Google Ads)**:
- conhece código e consegue rodar local
- quer orientação confiável e rápida
- precisa manter histórico de decisões e métricas
- quer evoluir o produto usando Codex como copiloto

## Jornada 1 — “Preciso tirar uma dúvida agora”
1) Abre o app (Streamlit)
2) Pergunta: “Para oferta X, o que fazer quando o CPC sobe e o CTR cai?”
3) Sistema:
   - recupera trechos relevantes (dúvidas/mentoria)
   - responde com passos acionáveis
   - mostra citações + contexto
4) Você decide e registra ação na campanha

## Jornada 2 — “Acompanhar campanha e orientar próximos passos”
1) Seleciona campanha “CB - Produto Y”
2) Cola métricas (ex.: últimos 3 dias: spend, clicks, CTR, CPC, conv, CPA, ROAS)
3) Sistema:
   - salva evento na timeline
   - compara com histórico
   - sugere hipóteses e ações (ajuste de keyword, anúncio, LP, segmentação)
   - referencia trechos do acervo
4) Você aplica mudanças e registra decisão

## Jornada 3 — “Descobrir o que tem dentro dos vídeos de dúvida”
1) Você ainda não sabe o assunto real do vídeo
2) Quer buscar por tema (“narrow targeting”, “negativar termos”, “policy”)
3) Sistema:
   - permite busca semântica
   - mostra “cartões” com trecho + origem (arquivo/pasta) + relevância
4) Você encontra o vídeo/trecho e usa como base

## UX (Streamlit) — Padrões desejados
- Chat em coluna central (estilo ChatGPT)
- Painel lateral:
  - seleção de campanha
  - filtros de acervo (seção/subseção)
  - botões: “Reindexar”, “Ver fontes”, “Exportar resumo”
- Mensagens do assistente:
  - resposta
  - “Ações sugeridas”
  - “Fontes” (citações)
  - “Perguntas para esclarecer” (se faltarem métricas/contexto)
