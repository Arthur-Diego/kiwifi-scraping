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
