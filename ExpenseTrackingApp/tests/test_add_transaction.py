"""Tests for the standalone transaction entry command."""

from __future__ import annotations

import argparse
import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import psycopg

from scripts.add_transaction import (
    INSERT_QUERY_PATH,
    MAX_AMOUNT,
    Transaction,
    insert_transaction,
    load_insert_query,
    main,
    parse_amount,
    parse_args,
    parse_date,
    parse_description,
)


class ValidationTests(unittest.TestCase):
    def test_default_date_type_and_database(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            args = parse_args(
                ["--amount", "18.5", "--description", " Lunch "],
                today=date(2026, 7, 27),
            )

        self.assertEqual(args.amount, Decimal("18.50"))
        self.assertEqual(args.description, "Lunch")
        self.assertEqual(args.occurred_on, date(2026, 7, 27))
        self.assertEqual(args.transaction_type, "expense")
        self.assertEqual(args.database, "expense_tracking_app")

    def test_explicit_values_and_all_transaction_types(self) -> None:
        for transaction_type in ("expense", "income", "investment"):
            with self.subTest(transaction_type=transaction_type):
                args = parse_args(
                    [
                        "--amount",
                        "2500.00",
                        "--description",
                        "Paycheck",
                        "--date",
                        "2026-07-26",
                        "--type",
                        transaction_type,
                        "--database",
                        "other_database",
                    ]
                )
                self.assertEqual(args.occurred_on, date(2026, 7, 26))
                self.assertEqual(args.transaction_type, transaction_type)
                self.assertEqual(args.database, "other_database")

    def test_pgdatabase_sets_default_database(self) -> None:
        with patch.dict(os.environ, {"PGDATABASE": "configured_database"}, clear=True):
            args = parse_args(
                ["--amount", "1.00", "--description", "Test"],
                today=date(2026, 7, 27),
            )
        self.assertEqual(args.database, "configured_database")

    def test_valid_amount_boundaries(self) -> None:
        self.assertEqual(parse_amount("0.01"), Decimal("0.01"))
        self.assertEqual(
            parse_amount(format(MAX_AMOUNT, ".2f")),
            Decimal("9999999999.99"),
        )
        self.assertEqual(parse_amount("12.000"), Decimal("12.00"))

    def test_invalid_amounts(self) -> None:
        for value in (
            "not-a-number",
            "NaN",
            "Infinity",
            "0",
            "-1.00",
            "1.001",
            "10000000000.00",
        ):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_amount(value)

    def test_invalid_dates(self) -> None:
        for value in ("07/27/2026", "2026-02-30", ""):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_date(value)

    def test_description_is_trimmed_and_must_not_be_blank(self) -> None:
        self.assertEqual(parse_description("  Groceries  "), "Groceries")
        with self.assertRaises(argparse.ArgumentTypeError):
            parse_description(" \t ")

    def test_invalid_type_exits_with_argparse_status(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                parse_args(
                    [
                        "--amount",
                        "1.00",
                        "--description",
                        "Test",
                        "--type",
                        "transfer",
                    ]
                )
        self.assertEqual(raised.exception.code, 2)


class QueryTests(unittest.TestCase):
    def test_query_is_loaded_from_the_central_queries_directory(self) -> None:
        query = load_insert_query()

        self.assertEqual(
            INSERT_QUERY_PATH,
            Path(__file__).resolve().parent.parent
            / "queries"
            / "insert_transaction.sql",
        )
        self.assertIn("INSERT INTO public.transactions", query)
        for parameter in (
            "%(occurred_on)s",
            "%(transaction_type)s",
            "%(amount)s",
            "%(description)s",
        ):
            self.assertIn(parameter, query)

    def test_missing_query_file_raises_os_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.sql"
            with self.assertRaises(OSError):
                load_insert_query(missing)

    @patch("scripts.add_transaction.psycopg.connect")
    def test_insert_uses_named_parameters_and_returns_row(
        self,
        connect_mock: MagicMock,
    ) -> None:
        transaction = Transaction(
            occurred_on=date(2026, 7, 27),
            transaction_type="expense",
            amount=Decimal("18.75"),
            description="Lunch",
        )
        inserted = {
            "id": 453,
            **transaction.query_parameters(),
            "created_at": datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc),
        }
        connection = connect_mock.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = inserted

        result = insert_transaction(
            transaction,
            "expense_tracking_app",
            "INSERT QUERY",
        )

        self.assertEqual(result, inserted)
        connect_mock.assert_called_once()
        self.assertEqual(
            connect_mock.call_args.kwargs["dbname"],
            "expense_tracking_app",
        )
        cursor.execute.assert_called_once_with(
            "INSERT QUERY",
            transaction.query_parameters(),
        )

    @patch("scripts.add_transaction.psycopg.connect")
    def test_insert_requires_returned_row(self, connect_mock: MagicMock) -> None:
        transaction = Transaction(
            occurred_on=date(2026, 7, 27),
            transaction_type="expense",
            amount=Decimal("18.75"),
            description="Lunch",
        )
        connection = connect_mock.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        with self.assertRaisesRegex(RuntimeError, "did not return"):
            insert_transaction(transaction, "expense_tracking_app", "INSERT QUERY")


class CommandTests(unittest.TestCase):
    @patch("scripts.add_transaction.psycopg.connect")
    def test_dry_run_prints_without_connecting(
        self,
        connect_mock: MagicMock,
    ) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "--amount",
                    "18.75",
                    "--description",
                    "Lunch",
                    "--date",
                    "2026-07-27",
                    "--dry-run",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output.getvalue(),
            "Dry run: 2026-07-27 | expense | $18.75 | Lunch\n",
        )
        connect_mock.assert_not_called()

    @patch("scripts.add_transaction.insert_transaction")
    @patch("scripts.add_transaction.load_insert_query", return_value="INSERT QUERY")
    def test_success_prints_inserted_transaction(
        self,
        load_query_mock: MagicMock,
        insert_mock: MagicMock,
    ) -> None:
        insert_mock.return_value = {
            "id": 453,
            "occurred_on": date(2026, 7, 27),
            "transaction_type": "expense",
            "amount": Decimal("18.75"),
            "description": "Lunch",
            "created_at": datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc),
        }
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "--amount",
                    "18.75",
                    "--description",
                    "Lunch",
                    "--date",
                    "2026-07-27",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output.getvalue(),
            "Added transaction #453\n"
            "2026-07-27 | expense | $18.75 | Lunch\n",
        )
        load_query_mock.assert_called_once_with()
        insert_mock.assert_called_once()

    @patch(
        "scripts.add_transaction.insert_transaction",
        side_effect=psycopg.OperationalError("connection failed"),
    )
    @patch("scripts.add_transaction.load_insert_query", return_value="INSERT QUERY")
    def test_database_error_is_concise(
        self,
        load_query_mock: MagicMock,
        insert_mock: MagicMock,
    ) -> None:
        errors = io.StringIO()

        with redirect_stderr(errors):
            exit_code = main(
                [
                    "--amount",
                    "18.75",
                    "--description",
                    "Lunch",
                    "--date",
                    "2026-07-27",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(errors.getvalue(), "Database error: connection failed\n")
        load_query_mock.assert_called_once_with()
        insert_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
