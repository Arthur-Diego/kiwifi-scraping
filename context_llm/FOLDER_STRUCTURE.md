```text
src/
├── domain/
│   ├── campaigns/
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   ├── exceptions.py
│   │   └── services.py
│   └── knowledge/
│       ├── entities.py
│       ├── policies.py
│       └── exceptions.py
│
├── application/
│   ├── use_cases/
│   │   ├── ingest_transcripts.py
│   │   ├── chat_with_knowledge.py
│   │   ├── record_campaign_event.py
│   │   ├── list_campaigns.py
│   │   └── summarize_campaign.py
│   │
│   ├── ports/
│   │   ├── vector_store.py
│   │   ├── llm.py
│   │   ├── transcript_repo.py
│   │   ├── campaign_repo.py
│   │   ├── clock.py
│   │   └── logger_port.py
│   └── errors.py
│
├── infrastructure/
│   ├── vectorstores/
│   │   └── qdrant_store.py
│   │
│   ├── llm/
│   │   ├── openai_client.py
│   │   └── local_model.py
│   │
│   ├── fs/
│   │   └── windows_transcript_repo.py
│   │
│   ├── persistence/
│   │   ├── postgres_campaign_repo.py
│   │   └── json_campaign_repo.py
│   │
│   ├── transcription/
│   │   ├── whisper_transcriber.py
│   │   └── transcribe_utils.py
│   │
│   ├── logger/
│   │   └── json_logger.py
│   │
│   └── config.py
│
├── interface/
│   ├── streamlit_app/
│   │   ├── app.py
│   │   ├── ui_components.py
│   │   ├── session_state.py
│   │   └── ui_utils.py
│   │
│   └── api/
│       ├── main.py
│       └── schemas.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   └── reindex.py
│
└── requirements.txt
