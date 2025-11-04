from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ChunkingConfig:
    # Tamanhos típicos para RAG
    target_tokens_per_chunk: int = 350        # alvo
    max_tokens_per_chunk: int = 500           # teto duro por chunk
    overlap_tokens: int = 60                  # sobreposição para contexto
    max_tokens_per_file: int = 10_000         # requisito do usuário
    similarity_break_threshold: float = 0.40  # quebra quando similaridade cair abaixo

@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"  # livre e eficaz
    batch_size: int = 64

@dataclass(frozen=True)
class QdrantConfig:
    host: str = "localhost"
    port: int = 6333
    collection: str = "transcricoes"
    distance: str = "Cosine"  # Cosine é padrão para ST embeddings

@dataclass(frozen=True)
class Paths:
    export_dir: Path = Path("./exports")  # para JSONL de chunks

