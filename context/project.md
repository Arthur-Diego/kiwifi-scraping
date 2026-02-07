# project.md

- Dominio do sistema inferido: captura de aulas na Kiwify, processamento de video/audio, transcricao e consulta por RAG para analise de campanhas.
- Responsabilidades do sistema:
- Autenticacao e navegacao automatizada na Kiwify.
- Captura de URLs de video e download via ffmpeg.
- Extracao de audio e transcricao com Whisper.
- Ingestao, chunking e indexacao vetorial em Qdrant.
- Consulta via LLM com contexto recuperado.
- Interfaces FastAPI e Streamlit para operacao.

- Principais modulos:
- `controller/`: endpoints e entrada de execucao.
- `facade/`: orquestracao do fluxo de extracao.
- `service/`: scraping, processamento e RAG.
- `repository/`: acesso ao Qdrant.
- `rag_qdrant/`: pipeline de ingestao e indexacao.
- `llm/`: cliente LLM.
- `ui/`: interfaces Streamlit.
- `utils/` e `diversos/`: utilitarios e scripts avulsos.
