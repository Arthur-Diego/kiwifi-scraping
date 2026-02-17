from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "transcricoes")
    embedder_model: str = os.getenv("QDRANT_EMBEDDER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    history_dir: Path = Path(os.getenv("CHAT_HISTORY_DIR", "data/chat_history"))
    product_mining_source_file: Path = Path(
        os.getenv("PRODUCT_MINING_SOURCE_FILE", "context_llm/product_mining_candidates.seed.json")
    )
    product_mining_enable_scraping: bool = os.getenv("PRODUCT_MINING_ENABLE_SCRAPING", "1").strip() in {"1", "true", "TRUE", "yes", "YES"}
    product_mining_scraping_timeout_seconds: float = float(os.getenv("PRODUCT_MINING_SCRAPING_TIMEOUT_SECONDS", "12"))
    product_mining_scraping_max_workers: int = int(os.getenv("PRODUCT_MINING_SCRAPING_MAX_WORKERS", "6"))
    product_mining_use_local_source: bool = os.getenv("PRODUCT_MINING_USE_LOCAL_SOURCE", "1").strip() in {"1", "true", "TRUE", "yes", "YES"}
