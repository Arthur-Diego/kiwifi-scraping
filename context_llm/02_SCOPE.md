# Escopo

## V1 (MVP robusto)
### Funcionalidades
1. **Ingestão local**:
   - Ler transcrições do Windows (pastas por seções/subseções)
   - Indexar no Qdrant com metadados
2. **Chat com RAG**:
   - Interface Streamlit estilo chat
   - Resposta com **citações** (trechos + arquivo + timestamp se disponível)
   - Filtros por seção/subseção (quando fizer sentido)
3. **Memória de campanha (local)**:
   - Criar “Campanha” (nome/ID)
   - Registrar eventos cronológicos:
     - métricas (diárias/semanais)
     - decisões (o que mudou)
     - hipóteses (por que mudou)
     - resultados (antes/depois)
   - Consultar o histórico dentro do chat
4. **Avaliação mínima**:
   - dataset pequeno de perguntas (20–50) para medir regressão
   - testes automatizados de pipeline (smoke + integração)

### Requisitos não-funcionais
- Rodar local em PC gamer
- Baixa fricção: instalar e rodar com um comando
- Reprodutível: mesmas entradas geram o mesmo índice (com versionamento)
- Seguro: não vazar chaves/API no repo

## Fora de escopo (V1)
- Multi-usuário/tenant
- Auth complexa
- Painel avançado com gráficos sofisticados (pode vir depois)
- Ações automáticas na conta do Google Ads (sem “autopilot”)

## V2 (próximas iterações)
- Reprocessamento de transcrição com modelo melhor / diarização / timestamps melhores
- Reranking e melhores embeddings
- Cache e otimização de latência
- Modo “consultor”: checklists e playbooks por situação
- Export de relatórios (PDF/markdown)

## V3 (futuro)
- Ingestão YouTube (conteúdo atualizado)
- Garimpagem de produtos (sinais de tendência)
- Deploy externo (PWA / API + frontend) para acesso de qualquer lugar
