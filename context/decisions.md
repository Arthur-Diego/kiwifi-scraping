# decisions.md

- decisao inferida do codigo: usar Qdrant como banco vetorial local (host `localhost:6333`) para colecao `transcricoes`.
- decisao inferida do codigo: usar SentenceTransformers `all-MiniLM-L6-v2` para embeddings.
- decisao inferida do codigo: aplicar chunking semantico com limite de tokens e quebra por similaridade.
- decisao inferida do codigo: usar LangChain + OpenAI (`ChatOpenAI`) com modelo padrao `gpt-4o-mini`.
- decisao inferida do codigo: usar Selenium + selenium-wire para capturar URLs de video via requests de rede.
- decisao inferida do codigo: usar Whisper local para transcricao de audio.
- decisao inferida do codigo: expor API via FastAPI e UI via Streamlit.
