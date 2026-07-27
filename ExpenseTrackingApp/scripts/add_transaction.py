"""Add one transaction to the expense tracking database."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

import psycopg
from psycopg.rows import dict_row


REPO_ROOT = Path(__file__).resolve().parent.parent
INSERT_QUERY_PATH = REPO_ROOT / "queries" / "insert_transaction.sql"
DEFAULT_DATABASE = "expense_tracking_app"
ALLOWED_TYPES = ("expense", "income", "investment")
CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("9999999999.99")


@dataclass(frozen=True)
class Transaction:
    occurred_on: date
    transaction_type: str
    amount: Decimal
    description: str

    def query_parameters(self) -> dict[str, Any]:
        return {
            "occurred_on": self.occurred_on,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "description": self.description,
        }


def parse_amount(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("amount must be a valid decimal number") from error

    if not amount.is_finite():
        raise argparse.ArgumentTypeError("amount must be a finite decimal number")
    if amount <= 0:
        raise argparse.ArgumentTypeError("amount must be greater than zero")
    if amount > MAX_AMOUNT:
        raise argparse.ArgumentTypeError(
            f"amount must not exceed {format(MAX_AMOUNT, '.2f')}"
        )

    normalized = amount.quantize(CENT)
    if normalized != amount:
        raise argparse.ArgumentTypeError("amount must have at most two decimal places")
    return normalized


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from error


def parse_description(value: str) -> str:
    description = value.strip()
    if not description:
        raise argparse.ArgumentTypeError("description must not be blank")
    return description


def parse_database(value: str) -> str:
    database = value.strip()
    if not database:
        raise argparse.ArgumentTypeError("database must not be blank")
    return database


def parse_args(
    argv: Sequence[str] | None = None,
    *,
    today: date | None = None,
) -> argparse.Namespace:
    default_date = today or date.today()
    default_database = os.environ.get("PGDATABASE") or DEFAULT_DATABASE
    parser = argparse.ArgumentParser(
        description="Add one transaction to the expense tracking database.",
        epilog=(
            "Connection settings use PostgreSQL's standard PGHOST, PGPORT, "
            "PGUSER, PGPASSWORD, and PGPASSFILE environment variables or .pgpass."
        ),
    )
    parser.add_argument(
        "--amount",
        required=True,
        type=parse_amount,
        help="Positive transaction amount with at most two decimal places.",
    )
    parser.add_argument(
        "--description",
        required=True,
        type=parse_description,
        help="Nonblank transaction description.",
    )
    parser.add_argument(
        "--date",
        dest="occurred_on",
        type=parse_date,
        default=default_date,
        metavar="YYYY-MM-DD",
        help=f"Transaction date (default: {default_date.isoformat()}).",
    )
    parser.add_argument(
        "--type",
        dest="transaction_type",
        choices=ALLOWED_TYPES,
        default="expense",
        help="Transaction type (default: expense).",
    )
    parser.add_argument(
        "--database",
        type=parse_database,
        default=default_database,
        help=(
            "PostgreSQL database name "
            f"(default: PGDATABASE or {DEFAULT_DATABASE})."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the transaction without connecting or inserting.",
    )
    return parser.parse_args(argv)


def load_insert_query(path: Path = INSERT_QUERY_PATH) -> str:
    return path.read_text(encoding="utf-8")


def insert_transaction(
    transaction: Transaction,
    database: str,
    query: str,
) -> Mapping[str, Any]:
    with psycopg.connect(dbname=database, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, transaction.query_parameters())
            inserted = cursor.fetchone()

    if inserted is None:
        raise RuntimeError("the database did not return the inserted transaction")
    return inserted


def format_transaction(transaction: Mapping[str, Any]) -> str:
    return (
        f"{transaction['occurred_on']} | {transaction['transaction_type']} | "
        f"${Decimal(transaction['amount']):.2f} | {transaction['description']}"
    )


def transaction_from_args(args: argparse.Namespace) -> Transaction:
    return Transaction(
        occurred_on=args.occurred_on,
        transaction_type=args.transaction_type,
        amount=args.amount,
        description=args.description,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    transaction = transaction_from_args(args)

    if args.dry_run:
        print(f"Dry run: {format_transaction(transaction.query_parameters())}")
        return 0

    try:
        query = load_insert_query()
        inserted = insert_transaction(transaction, args.database, query)
    except OSError as error:
        print(f"Unable to load insert query: {error}", file=sys.stderr)
        return 1
    except psycopg.Error as error:
        message = str(error).splitlines()[0] if str(error) else error.__class__.__name__
        print(f"Database error: {message}", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(f"Insert error: {error}", file=sys.stderr)
        return 1

    print(f"Added transaction #{inserted['id']}")
    print(format_transaction(inserted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
