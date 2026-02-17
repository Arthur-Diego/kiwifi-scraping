from __future__ import annotations

from src.application.use_cases.chat_with_knowledge import ChatWithKnowledgeUseCase
from src.application.use_cases.ingest_transcripts import IngestTranscriptsUseCase
from src.application.use_cases.list_product_mining_results import ListProductMiningResultsUseCase
from src.application.use_cases.run_product_mining_batch import RunProductMiningBatchUseCase
from sentence_transformers import SentenceTransformer

from src.infrastructure.config import AppConfig
from src.infrastructure.chunking.semantic_chunker import SemanticChunker
from src.infrastructure.fs.local_transcript_repository import LocalTranscriptRepository
from src.infrastructure.logger.std_logger import StdLogger
from src.infrastructure.persistence.postgres_product_mining_repository import PostgresProductMiningRepository
from src.infrastructure.product_mining.composite_candidate_source import CompositeProductCandidateSource
from src.infrastructure.product_mining.local_candidate_source import LocalProductCandidateSource
from src.infrastructure.product_mining.scraping_enriched_candidate_source import ScrapingEnrichedProductCandidateSource
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


def build_run_product_mining_batch_use_case(config: AppConfig | None = None) -> RunProductMiningBatchUseCase:
    cfg = config or AppConfig()
    sources = []
    if cfg.product_mining_use_local_source:
        sources.append(LocalProductCandidateSource(source_file=cfg.product_mining_source_file))

    base_source = CompositeProductCandidateSource(sources=sources) if sources else CompositeProductCandidateSource(sources=[])
    source = (
        ScrapingEnrichedProductCandidateSource(
            base_source=base_source,
            timeout_seconds=cfg.product_mining_scraping_timeout_seconds,
            max_workers=max(1, cfg.product_mining_scraping_max_workers),
        )
        if cfg.product_mining_enable_scraping
        else base_source
    )
    return RunProductMiningBatchUseCase(
        source=source,
        repository=PostgresProductMiningRepository(),
        logger=StdLogger("product_mining.batch"),
    )


def build_list_product_mining_results_use_case(config: AppConfig | None = None) -> ListProductMiningResultsUseCase:
    _ = config or AppConfig()
    return ListProductMiningResultsUseCase(repository=PostgresProductMiningRepository())
