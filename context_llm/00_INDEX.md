# Context Index (Engenharia de Contexto)

Data: 2026-02-13

Este diretório contém a “engenharia de contexto” do projeto: visão, escopo, arquitetura, decisões e guias de implementação.
A ideia é manter estes arquivos **curtos, versionados e vivos**.

## Como usar
- Leia `01_VISION.md` e `02_SCOPE.md` para alinhar objetivos e limites.
- Use `06_ARCHITECTURE.md` como referência para refatoração e organização do código.
- Registre decisões importantes em `07_ADR_DECISIONS.md`.
- Use `09_EVALUATION_TESTING.md` para guiar métricas, testes e regressão.
- `12_DEPLOYMENT_SCALING.md` orienta o caminho “local → externo (smartphone)”.

## Arquivos
1. `01_VISION.md` — propósito, valor e definição do produto
2. `02_SCOPE.md` — escopo v1, fora de escopo e requisitos
3. `03_PERSONAS_JOURNEYS.md` — usuários, fluxos e UX (ChatGPT-like)
4. `04_DATA_SOURCES.md` — dados locais (vídeos/transcrições), organização e qualidade
5. `05_RAG_DESIGN.md` — desenho do RAG (chunking, embeddings, Qdrant, fontes)
6. `06_ARCHITECTURE.md` — arquitetura (camadas, SOLID, Clean Code, módulos)
7. `07_ADR_DECISIONS.md` — registro de decisões (template ADR)
8. `08_PROMPTS_GUARDRAILS.md` — prompting, citações, anti-alucinação, políticas
9. `09_EVALUATION_TESTING.md` — avaliação RAG + testes (unit/integration/e2e)
10. `10_OBSERVABILITY.md` — logs, métricas, rastreabilidade e auditoria
11. `11_ROADMAP.md` — roadmap por fases
12. `12_DEPLOYMENT_SCALING.md` — rodar local, expor externamente, PWA, segurança
13. `13_SECURITY_PRIVACY.md` — privacidade, chaves, dados sensíveis, compliance
14. `14_CAMPAIGN_MEMORY.md` — memória cronológica de campanhas + conhecimento
15. `15_PRODUCT_MINING.md` — garimpagem de produtos (futuro)
16. `16_YOUTUBE_INGESTION.md` — ingestão de conteúdos atuais (futuro)
