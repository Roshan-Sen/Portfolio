"""Shared configuration for the expense tracking application."""

from __future__ import annotations

import os
from pathlib import Path

from expense_tracking.errors import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = "expense_tracking_app"
INSERT_QUERY_PATH = PROJECT_ROOT / "queries" / "insert_transaction.sql"
REPORT_QUERY_PATH = PROJECT_ROOT / "queries" / "select_report_transactions.sql"
REPORT_SOURCE = PROJECT_ROOT / "reports" / "cash_flow.qmd"
DEFAULT_REPORT_OUTPUT_DIR = PROJECT_ROOT / "reports" / "output"


def resolve_database(database: str | None = None) -> str:
    """Return an explicit, environment-provided, or default database name."""

    value = database if database is not None else os.environ.get("PGDATABASE")
    resolved = value if value is not None else DEFAULT_DATABASE
    if not isinstance(resolved, str) or not resolved.strip():
        raise ValidationError("database must not be blank")
    return resolved.strip()
