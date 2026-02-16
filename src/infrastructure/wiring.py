from __future__ import annotations

from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeUseCase
from src.application.use_cases.ingest_transcripts import IngestTranscriptsUseCase
from sentence_transformers import SentenceTransformer

from src.infrastructure.config import AppConfig
from src.infrastructure.chunking.semantic_chunker import SemanticChunker
from src.infrastructure.fs.local_transcript_repository import LocalTranscriptRepository
from src.infrastructure.logger.std_logger import StdLogger
from src.infrastructure.vectorstores.qdrant_store import QdrantVectorStore


def build_chat_use_case(config: AppConfig | None = None) -> ChatWithKnowledgeUseCase:
    # Lazy import to avoid requiring LLM deps when only ingestion/reindex is used.
    from src.infrastructure.llm.langchain_openai_client import LangChainOpenAIClient

    cfg = config or AppConfig()
    logger = StdLogger("rag.chat")
    return ChatWithKnowledgeUseCase(
        vector_store=QdrantVectorStore(qdrant_url=cfg.qdrant_url, embedder_model=cfg.embedder_model),
        llm=LangChainOpenAIClient(),
        logger=logger,
    )


def build_ingest_use_case(config: AppConfig | None = None) -> IngestTranscriptsUseCase:
    cfg = config or AppConfig()
    logger = StdLogger("rag.ingest")
    shared_embedder = SentenceTransformer(cfg.embedder_model)
    return IngestTranscriptsUseCase(
        transcript_repo=LocalTranscriptRepository(),
        vector_store=QdrantVectorStore(qdrant_url=cfg.qdrant_url, embedder=shared_embedder),
        logger=logger,
        chunker=SemanticChunker(embedder=shared_embedder),
    )
