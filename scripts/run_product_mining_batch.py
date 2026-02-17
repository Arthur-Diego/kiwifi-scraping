from __future__ import annotations

import argparse
import time

from src.infrastructure.config import AppConfig
from src.infrastructure.wiring import build_run_product_mining_batch_use_case


def _run_once() -> None:
    use_case = build_run_product_mining_batch_use_case(AppConfig())
    output = use_case.execute()
    summary = output.run_summary
    print(
        f"[product-mining] run_id={summary.run_id} source={summary.source_name} "
        f"candidates={summary.candidates_count} stored={summary.stored_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run product mining batch pipeline.")
    parser.add_argument("--loop", action="store_true", help="Run forever using the provided interval.")
    parser.add_argument("--interval-hours", type=float, default=24.0, help="Interval between runs when --loop is enabled.")
    args = parser.parse_args()

    if not args.loop:
        _run_once()
        return

    sleep_seconds = max(60.0, args.interval_hours * 3600.0)
    while True:
        _run_once()
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()

