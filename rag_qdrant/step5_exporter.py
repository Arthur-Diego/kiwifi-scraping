from pathlib import Path
from typing import Iterable
import json
import datetime
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
                data = c.model_dump()
                # Converte datetime para string (se existir)
                if isinstance(data.get("date"), (datetime.datetime, datetime.date)):
                    data["date"] = data["date"].isoformat()

                f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")
        return str(out_path)
