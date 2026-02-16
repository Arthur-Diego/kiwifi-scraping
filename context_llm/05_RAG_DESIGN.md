# Desenho do RAG (LangChain + Qdrant)

## Objetivo do RAG
Responder perguntas e orientar decisões usando:
1) **Trechos das transcrições** (base principal)
2) **Memória da campanha** (timeline local)
3) (Futuro) YouTube / produtos / notícias

## Pipeline (alto nível)
1. Loader → lê transcrições do filesystem
2. Splitter → chunking
3. Embedder → gera embeddings
4. Vector store → Qdrant
5. Retriever → top-k (com filtros por metadata)
6. (Opcional) Reranker → melhora precisão
7. Generator → LLM responde com base nos trechos
8. Post-process → citações, ações sugeridas, checklist

## Chunking (recomendação inicial)
- chunk_size: 800–1500 caracteres (ou 300–600 tokens, dependendo do modelo)
- overlap: 80–150 caracteres
- Se houver timestamps: alinhar chunk por segmentos naturais (frases/legendas)

## Metadados no Qdrant (mínimo)
- section
- subsection
- source_file
- source_path
- transcript_version
- chunk_id (uuid)
- chunk_index
- (opcional) start_time, end_time
- (opcional) content_type (dúvida/aula)

## Estratégias para “vídeos de dúvida sem assunto”
1) Indexar normalmente (sem confiar no nome do arquivo)
2) Criar um job opcional de **enriquecimento**:
   - gerar “título provável” e “tags” para cada transcript
   - armazenar como metadata e/ou coleção auxiliar
3) UI: permitir buscar por tema e listar os chunks mais representativos

## Anti-alucinação (essencial)
- Responder com base nos trechos recuperados
- Se não houver evidência suficiente, dizer:
  - “Não encontrei base nas transcrições para afirmar X”
  - sugerir o que procurar / quais métricas faltam
- Sempre mostrar “Fontes” com:
  - trecho (curto)
  - arquivo e seção
  - timestamp se houver

## Coleções sugeridas no Qdrant
- `transcripts_v1` (principal)
- `transcripts_v2` (quando reprocessar)
- `campaign_memory` (se decidir indexar a timeline também)
- `product_notes` (futuro)

## Avaliação do retrieval (mínimo)
- dataset de perguntas reais
- verificar se os top-k trazem trechos corretos
- medir recall@k e “support rate” (resposta com fontes úteis)

## Reindexamento
- Detectar mudanças por hash do arquivo/transcript
- Reindexar somente o que mudou
- Manter “manifest” do índice (ver `06_ARCHITECTURE.md`)
