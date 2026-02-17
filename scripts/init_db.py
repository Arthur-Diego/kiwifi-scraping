from __future__ import annotations

import argparse
import os
import time

import psycopg2

from src.infrastructure.persistence.postgres_chat_repository import PostgresChatRepository
from src.infrastructure.persistence.postgres_product_mining_repository import PostgresProductMiningRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL schema for chat history.")
    parser.add_argument(
        "--db-dsn",
        default=os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/chat_history"),
    )
    args = parser.parse_args()

    retries = 10
    for i in range(retries):
        try:
            repo = PostgresChatRepository(dsn=args.db_dsn, ensure_schema=True)
            pm_repo = PostgresProductMiningRepository(dsn=args.db_dsn)
            pm_repo.ensure_schema()
            break
        except psycopg2.OperationalError:
            if i == retries - 1:
                raise
            time.sleep(0.5)
    print(f"PostgreSQL schema initialized using DSN: {repo.dsn}")


if __name__ == "__main__":
    main()
