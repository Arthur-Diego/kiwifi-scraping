# kiwifi-scraping

```bash
meu_projeto_rag/
│
├── data/
│   ├── secao1/
│   │   ├── transcricao_01.txt
│   │   └── transcricao_02.txt
│   ├── secao2/
│   │   └── transcricao_03.txt
│   └── ...
│
├── src/
│   ├── ingestion.py         # Lê e prepara os arquivos
│   ├── embeddings.py        # Cria embeddings
│   ├── vectorstore.py       # Cria e carrega o banco vetorial
│   ├── retriever.py         # Recupera contexto relevante
│   ├── rag_pipeline.py      # Orquestra o fluxo RAG
│   └── app.py               # Interface (CLI, API, ou Streamlit)
│
├── requirements.txt
└── README.md
