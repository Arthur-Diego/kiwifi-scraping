from pathlib import Path
from typing import Iterable
import json
from .domain import Chunk
from .config import Paths

class ChunkExporter:
    """
    SRP: exportar chunks de forma performática.
    JSONL é excelente para volumes grandes (streaming linha a linha).
    """
    def __init__(self, paths: Paths = Paths()):
        self.paths = paths
        self.paths.export_dir.mkdir(parents=True, exist_ok=True)

    def to_jsonl(self, chunks: Iterable[Chunk], outfile: str) -> str:
        out_path = self.paths.export_dir / outfile
        with out_path.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c.model_dump(), ensure_ascii=False) + "\n")
        return str(out_path)
