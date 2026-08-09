"""Add one transaction to the expense tracking database."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from expense_tracking.config import DEFAULT_DATABASE, resolve_database
from expense_tracking.errors import DatabaseError, QueryLoadError, TransactionError, ValidationError
from expense_tracking.transactions import (
    ALLOWED_TRANSACTION_TYPES,
    MAX_AMOUNT,
    InsertedTransaction,
    Transaction,
    add_transaction,
    validate_amount,
    validate_description,
)


ALLOWED_TYPES = ALLOWED_TRANSACTION_TYPES


def parse_amount(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("amount must be a valid decimal number") from error
    try:
        return validate_amount(amount)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from error


def parse_description(value: str) -> str:
    try:
        return validate_description(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_database(value: str) -> str:
    try:
        return resolve_database(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_args(
    argv: Sequence[str] | None = None,
    *,
    today: date | None = None,
) -> argparse.Namespace:
    default_date = today or date.today()
    default_database = resolve_database()
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


def format_transaction(
    transaction: Mapping[str, Any] | InsertedTransaction,
) -> str:
    values = (
        transaction.as_mapping()
        if isinstance(transaction, InsertedTransaction)
        else transaction
    )
    return (
        f"{values['occurred_on']} | {values['transaction_type']} | "
        f"${Decimal(values['amount']):.2f} | {values['description']}"
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
        inserted = add_transaction(transaction, args.database)
    except QueryLoadError as error:
        print(f"Unable to load insert query: {error}", file=sys.stderr)
        return 1
    except DatabaseError as error:
        print(f"Database error: {error}", file=sys.stderr)
        return 1
    except TransactionError as error:
        print(f"Insert error: {error}", file=sys.stderr)
        return 1

    print(f"Added transaction #{inserted.id}")
    print(format_transaction(inserted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
