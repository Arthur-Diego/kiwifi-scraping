from __future__ import annotations

from fastapi import FastAPI

from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeInput
from src.application.use_cases.ingest_transcripts import IngestTranscriptsInput
from src.infrastructure.config import AppConfig
from src.infrastructure.wiring import build_chat_use_case, build_ingest_use_case
from src.interface.api.schemas import ChatRequest, IngestRequest

app = FastAPI(title="Kiwifi RAG API", version="2.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(payload: ChatRequest) -> dict:
    use_case = build_chat_use_case(AppConfig())
    result = use_case.execute(
        ChatWithKnowledgeInput(
            query=payload.query,
            top_k=payload.top_k,
            section=payload.section,
            model_name=payload.model_name,
            temperature=payload.temperature,
        )
    )
    return {
        "answer": result.answer,
        "contexts": [ctx.__dict__ for ctx in result.contexts],
    }


@app.post("/ingest")
def ingest(payload: IngestRequest) -> dict:
    use_case = build_ingest_use_case(AppConfig())
    result = use_case.execute(
        IngestTranscriptsInput(
            input_paths=payload.input_paths,
            collection=payload.collection,
            chunk_size_chars=payload.chunk_size_chars,
            chunk_overlap_chars=payload.chunk_overlap_chars,
        )
    )
    return {
        "files_indexed": result.files_indexed,
        "chunks_indexed": result.chunks_indexed,
    }
