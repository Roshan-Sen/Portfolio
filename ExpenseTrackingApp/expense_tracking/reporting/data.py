"""Read transaction data from PostgreSQL for reporting."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

import psycopg
from psycopg.rows import dict_row

from expense_tracking.config import REPORT_QUERY_PATH
from expense_tracking.reporting.cash_flow import ReportTransaction


def load_report_query(path: Path = REPORT_QUERY_PATH) -> str:
    return path.read_text(encoding="utf-8")


def transaction_from_row(row: Mapping[str, Any]) -> ReportTransaction:
    return ReportTransaction(
        id=int(row["id"]),
        occurred_on=row["occurred_on"],
        transaction_type=str(row["transaction_type"]),
        amount=Decimal(row["amount"]),
        description=str(row["description"]),
    )


def load_transactions(
    *,
    start_date: date,
    end_date_exclusive: date,
    database: str,
    query: str | None = None,
) -> tuple[ReportTransaction, ...]:
    """Load transactions for a half-open date range using a read-only session."""

    if end_date_exclusive <= start_date:
        raise ValueError("exclusive end date must be after start date")

    report_query = query if query is not None else load_report_query()
    parameters = {
        "start_date": start_date,
        "end_date_exclusive": end_date_exclusive,
    }

    with psycopg.connect(
        dbname=database,
        row_factory=dict_row,
        options="-c default_transaction_read_only=on",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(report_query, parameters)
            rows = cursor.fetchall()

    return tuple(transaction_from_row(row) for row in rows)
