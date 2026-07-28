"""Tests for the read-only report data layer."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from reporting.data import (
    REPORT_QUERY_PATH,
    load_report_query,
    load_transactions,
    transaction_from_row,
)


class ReportDataTests(unittest.TestCase):
    def test_query_is_loaded_from_queries_directory(self) -> None:
        query = load_report_query()

        self.assertEqual(
            REPORT_QUERY_PATH,
            Path(__file__).resolve().parent.parent
            / "queries"
            / "select_report_transactions.sql",
        )
        self.assertIn("FROM public.transactions", query)
        self.assertIn("%(start_date)s", query)
        self.assertIn("%(end_date_exclusive)s", query)
        self.assertIn("ORDER BY", query)

    def test_missing_query_raises_os_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(OSError):
                load_report_query(Path(temp_dir) / "missing.sql")

    def test_row_is_converted_to_typed_transaction(self) -> None:
        converted = transaction_from_row(
            {
                "id": 10,
                "occurred_on": date(2026, 7, 1),
                "transaction_type": "expense",
                "amount": Decimal("18.75"),
                "description": "Lunch",
            }
        )

        self.assertEqual(converted.id, 10)
        self.assertEqual(converted.amount, Decimal("18.75"))

    @patch("reporting.data.psycopg.connect")
    def test_load_uses_read_only_connection_and_named_dates(
        self,
        connect_mock: MagicMock,
    ) -> None:
        connection = connect_mock.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            {
                "id": 10,
                "occurred_on": date(2026, 7, 1),
                "transaction_type": "expense",
                "amount": Decimal("18.75"),
                "description": "Lunch",
            }
        ]

        result = load_transactions(
            start_date=date(2026, 7, 1),
            end_date_exclusive=date(2026, 8, 1),
            database="expense_tracking_app",
            query="SELECT REPORT",
        )

        self.assertEqual(len(result), 1)
        connect_mock.assert_called_once_with(
            dbname="expense_tracking_app",
            row_factory=connect_mock.call_args.kwargs["row_factory"],
            options="-c default_transaction_read_only=on",
        )
        cursor.execute.assert_called_once_with(
            "SELECT REPORT",
            {
                "start_date": date(2026, 7, 1),
                "end_date_exclusive": date(2026, 8, 1),
            },
        )

    def test_invalid_half_open_range_is_rejected_before_connecting(self) -> None:
        with self.assertRaisesRegex(ValueError, "exclusive end"):
            load_transactions(
                start_date=date(2026, 7, 1),
                end_date_exclusive=date(2026, 7, 1),
                database="expense_tracking_app",
                query="SELECT REPORT",
            )


if __name__ == "__main__":
    unittest.main()
