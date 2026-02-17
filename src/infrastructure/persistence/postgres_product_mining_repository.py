from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from src.domain.product_mining.entities import ProductMiningResult, ProductMiningRunSummary


class PostgresProductMiningRepository:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/chat_history")

    def _connect(self):
        return psycopg2.connect(self.dsn, connect_timeout=15)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS product_mining_runs (
                        id SERIAL PRIMARY KEY,
                        source_name TEXT NOT NULL,
                        candidates_count INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS product_mining_results (
                        id SERIAL PRIMARY KEY,
                        run_id INTEGER NOT NULL REFERENCES product_mining_runs(id) ON DELETE CASCADE,
                        product_key TEXT NOT NULL,
                        product_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        category TEXT,
                        sales_page_url TEXT,
                        price DOUBLE PRECISION,
                        commission_pct DOUBLE PRECISION,
                        gravity DOUBLE PRECISION,
                        ranking INTEGER,
                        refund_rate DOUBLE PRECISION,
                        product_age_days INTEGER,
                        keyword_volume INTEGER,
                        trend_growth_30d DOUBLE PRECISION,
                        social_engagement DOUBLE PRECISION,
                        ads_competition_index DOUBLE PRECISION,
                        buy_intent_score DOUBLE PRECISION NOT NULL,
                        trend_score DOUBLE PRECISION NOT NULL,
                        offer_score DOUBLE PRECISION NOT NULL,
                        final_score DOUBLE PRECISION NOT NULL,
                        classification TEXT NOT NULL,
                        rationale JSONB NOT NULL,
                        raw_payload JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_product_mining_runs_created_at ON product_mining_runs(created_at DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_product_mining_results_run_id ON product_mining_results(run_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_product_mining_results_key ON product_mining_results(product_key)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_product_mining_results_final_score ON product_mining_results(final_score DESC)")
            conn.commit()

    def create_run(self, *, source_name: str, candidates_count: int) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO product_mining_runs (source_name, candidates_count, created_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (source_name, candidates_count, datetime.now(timezone.utc)),
                )
                run_id = int(cur.fetchone()[0])
            conn.commit()
            return run_id

    def save_result(self, *, run_id: int, result: ProductMiningResult) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO product_mining_results (
                        run_id, product_key, product_name, platform, category, sales_page_url,
                        price, commission_pct, gravity, ranking, refund_rate, product_age_days,
                        keyword_volume, trend_growth_30d, social_engagement, ads_competition_index,
                        buy_intent_score, trend_score, offer_score, final_score, classification,
                        rationale, raw_payload, created_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    (
                        run_id,
                        result.product_key,
                        result.product_name,
                        result.platform,
                        result.category,
                        result.sales_page_url,
                        result.price,
                        result.commission_pct,
                        result.gravity,
                        result.ranking,
                        result.refund_rate,
                        result.product_age_days,
                        result.keyword_volume,
                        result.trend_growth_30d,
                        result.social_engagement,
                        result.ads_competition_index,
                        result.buy_intent_score,
                        result.trend_score,
                        result.offer_score,
                        result.final_score,
                        result.classification,
                        Json(result.rationale),
                        Json(result.raw_payload),
                        datetime.now(timezone.utc),
                    ),
                )
            conn.commit()

    def list_latest_results(
        self,
        *,
        limit: int = 100,
        classification: str | None = None,
        platform: str | None = None,
    ) -> list[dict[str, Any]]:
        filters = []
        params: list[Any] = []
        if classification:
            filters.append("l.classification = %s")
            params.append(classification)
        if platform:
            filters.append("LOWER(l.platform) = LOWER(%s)")
            params.append(platform)
        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""

        query = f"""
            WITH latest AS (
                SELECT DISTINCT ON (product_key)
                    id, run_id, product_key, product_name, platform, category, sales_page_url,
                    price, commission_pct, gravity, ranking, refund_rate, product_age_days,
                    keyword_volume, trend_growth_30d, social_engagement, ads_competition_index,
                    buy_intent_score, trend_score, offer_score, final_score, classification,
                    rationale, raw_payload, created_at
                FROM product_mining_results
                ORDER BY product_key, run_id DESC, id DESC
            )
            SELECT
                l.*,
                r.created_at AS run_created_at,
                r.source_name
            FROM latest l
            JOIN product_mining_runs r ON r.id = l.run_id
            {where_sql}
            ORDER BY l.final_score DESC, l.created_at DESC
            LIMIT %s
        """
        params.append(limit)

        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                return [dict(row) for row in cur.fetchall()]

    def list_recent_runs(self, *, limit: int = 20) -> list[ProductMiningRunSummary]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        r.id,
                        r.source_name,
                        r.created_at,
                        r.candidates_count,
                        COUNT(pr.id)::INT AS stored_count
                    FROM product_mining_runs r
                    LEFT JOIN product_mining_results pr ON pr.run_id = r.id
                    GROUP BY r.id
                    ORDER BY r.id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [
            ProductMiningRunSummary(
                run_id=int(row["id"]),
                source_name=str(row["source_name"]),
                started_at=row["created_at"],
                candidates_count=int(row["candidates_count"]),
                stored_count=int(row["stored_count"]),
            )
            for row in rows
        ]
