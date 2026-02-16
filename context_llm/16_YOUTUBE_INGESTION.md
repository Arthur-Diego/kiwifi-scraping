# Ingestão YouTube (Futuro)

## Objetivo
Adicionar conhecimento mais atual para complementar o acervo de mentoria.

## Diretrizes
- Preferir APIs oficiais quando possível
- Definir curadoria:
  - canais confiáveis
  - temas (Google Ads policy changes, bidding updates, tracking)
  - recência (últimos 6–12 meses)

## Pipeline
1) Buscar vídeos (query/canais)
2) Baixar legenda/transcrição (quando permitido)
3) Normalizar e indexar em coleção separada:
   - `youtube_YYYY_MM` ou `youtube_v1`
4) Respostas devem distinguir claramente:
   - “fonte interna (mentoria)” vs “fonte externa (YouTube)”

## Riscos
- Ruído alto (conteúdo genérico)
- Conteúdo conflitante com a mentoria
- Mudanças frequentes de políticas e algoritmos

## Critérios de qualidade
- métricas de suporte (fontes relevantes)
- checagem de recência
- evitar “achismos”
