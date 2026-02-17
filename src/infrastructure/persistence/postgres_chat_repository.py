from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor


class PostgresChatRepository:
    """
    CRUD de campanhas, mensagens e métricas para dashboard/chat.
    """

    def __init__(self, dsn: str | None = None, *, ensure_schema: bool = False):
        self.dsn = dsn or os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/chat_history")
        if ensure_schema:
            self._ensure_schema()

    def _connect(self):
        return psycopg2.connect(self.dsn, connect_timeout=15)

    @staticmethod
    def _is_retryable_error(exc: psycopg2.OperationalError) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in (
                "could not connect",
                "connection refused",
                "connection timed out",
                "the database system is starting up",
                "temporary failure",
            )
        )

    def _run_with_retry(self, fn, *, retries: int = 12, sleep_s: float = 0.5):
        for i in range(retries):
            try:
                return fn()
            except psycopg2.OperationalError as exc:
                if not self._is_retryable_error(exc) or i == retries - 1:
                    raise
                time.sleep(sleep_s * (i + 1))

    def _ensure_schema(self) -> None:
        def _op() -> None:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS campaigns (
                            id SERIAL PRIMARY KEY,
                            campaign_name TEXT,
                            product_name TEXT,
                            date_created TIMESTAMPTZ DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS messages (
                            id SERIAL PRIMARY KEY,
                            campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            timestamp TIMESTAMPTZ NOT NULL
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS metrics (
                            id SERIAL PRIMARY KEY,
                            campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                            impressions INTEGER,
                            clicks INTEGER,
                            ctr DOUBLE PRECISION,
                            conversions INTEGER,
                            cost_per_conversion DOUBLE PRECISION,
                            conversion_rate DOUBLE PRECISION,
                            total_cost DOUBLE PRECISION,
                            daily_budget DOUBLE PRECISION,
                            cpc DOUBLE PRECISION,
                            keyword_data JSONB,
                            demographic_data TEXT,
                            device_data TEXT,
                            ad_performance TEXT,
                            trends TEXT,
                            last_updated TIMESTAMPTZ NOT NULL
                        )
                        """
                    )
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_campaign_id ON messages(campaign_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_metrics_campaign_id ON metrics(campaign_id)")
                    # Backward-compatible migration for existing databases.
                    cur.execute("ALTER TABLE campaigns ALTER COLUMN campaign_name DROP NOT NULL")
                    cur.execute("ALTER TABLE campaigns ALTER COLUMN product_name DROP NOT NULL")
                    cur.execute("ALTER TABLE campaigns ALTER COLUMN date_created DROP NOT NULL")
                    cur.execute("ALTER TABLE campaigns ALTER COLUMN date_created SET DEFAULT NOW()")
                conn.commit()

        self._run_with_retry(_op, retries=15, sleep_s=0.4)

    def create_campaign(self, campaign_name: str | None = None, product_name: str | None = None) -> int:
        campaign_name = campaign_name.strip() if campaign_name else None
        product_name = product_name.strip() if product_name else None
        date_created = datetime.now(timezone.utc)

        def _op() -> int:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO campaigns (campaign_name, product_name, date_created)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (campaign_name, product_name, date_created),
                    )
                    campaign_id = int(cur.fetchone()[0])
                conn.commit()
                return campaign_id

        return int(self._run_with_retry(_op))

    def list_campaigns(self) -> list[dict[str, Any]]:
        def _op():
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT id, campaign_name, product_name, date_created
                        FROM campaigns
                        ORDER BY id DESC
                        """
                    )
                    return cur.fetchall()

        rows = self._run_with_retry(_op)
        return [dict(row) for row in rows]

    def save_message(self, campaign_id: int, role: str, content: str) -> None:
        def _op() -> None:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO messages (campaign_id, role, content, timestamp)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (campaign_id, role, content, datetime.now(timezone.utc)),
                    )
                conn.commit()

        self._run_with_retry(_op)

    def get_messages(self, campaign_id: int) -> list[dict[str, Any]]:
        def _op():
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT id, campaign_id, role, content, timestamp
                        FROM messages
                        WHERE campaign_id = %s
                        ORDER BY id ASC
                        """,
                        (campaign_id,),
                    )
                    return cur.fetchall()

        rows = self._run_with_retry(_op)
        return [dict(row) for row in rows]

    def save_metrics(self, campaign_id: int, metrics: dict[str, Any]) -> None:
        latest = self.get_metrics(campaign_id) or {}
        merged = {**latest, **metrics}

        def _op() -> None:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO metrics (
                            campaign_id, impressions, clicks, ctr, conversions, cost_per_conversion,
                            conversion_rate, total_cost, daily_budget, cpc, keyword_data,
                            demographic_data, device_data, ad_performance, trends, last_updated
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            campaign_id,
                            merged.get("impressions"),
                            merged.get("clicks"),
                            merged.get("ctr"),
                            merged.get("conversions"),
                            merged.get("cost_per_conversion"),
                            merged.get("conversion_rate"),
                            merged.get("total_cost"),
                            merged.get("daily_budget"),
                            merged.get("cpc"),
                            Json(merged.get("keyword_data")) if merged.get("keyword_data") is not None else None,
                            merged.get("demographic_data"),
                            merged.get("device_data"),
                            merged.get("ad_performance"),
                            merged.get("trends"),
                            datetime.now(timezone.utc),
                        ),
                    )
                conn.commit()

        self._run_with_retry(_op)

    def get_metrics(self, campaign_id: int) -> dict[str, Any] | None:
        def _op():
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT *
                        FROM metrics
                        WHERE campaign_id = %s
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (campaign_id,),
                    )
                    return cur.fetchone()

        row = self._run_with_retry(_op)
        if row is None:
            return None
        data = dict(row)
        keyword_data = data.get("keyword_data")
        if isinstance(keyword_data, str):
            try:
                data["keyword_data"] = json.loads(keyword_data)
            except Exception:
                data["keyword_data"] = []
        return data
