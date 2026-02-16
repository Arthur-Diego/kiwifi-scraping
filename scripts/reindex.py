from __future__ import annotations

import argparse

from src.application.use_cases.ingest_transcripts import IngestTranscriptsInput
from src.infrastructure.config import AppConfig
from src.infrastructure.wiring import build_ingest_use_case


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex transcripts into Qdrant")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--collection", default="transcricoes")
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    args = parser.parse_args()

    use_case = build_ingest_use_case(AppConfig())
    result = use_case.execute(
        IngestTranscriptsInput(
            input_paths=args.inputs,
            collection=args.collection,
            chunk_size_chars=args.chunk_size,
            chunk_overlap_chars=args.chunk_overlap,
        )
    )
    print(f"Reindex done: {result.files_indexed} files, {result.chunks_indexed} chunks")


if __name__ == "__main__":
    main()
