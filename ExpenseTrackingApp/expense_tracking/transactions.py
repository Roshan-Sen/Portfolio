"""Validated transaction entry and PostgreSQL persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, DecimalException, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

import psycopg
from psycopg.rows import dict_row

from expense_tracking.config import INSERT_QUERY_PATH, resolve_database
from expense_tracking.errors import (
    DatabaseError,
    QueryLoadError,
    TransactionError,
    ValidationError,
)


ALLOWED_TRANSACTION_TYPES = ("expense", "income", "investment")
CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("9999999999.99")


def validate_amount(amount: Decimal) -> Decimal:
    if not isinstance(amount, Decimal):
        raise ValidationError("amount must be a decimal number")
    if not amount.is_finite():
        raise ValidationError("amount must be a finite decimal number")
    if amount <= 0:
        raise ValidationError("amount must be greater than zero")
    if amount > MAX_AMOUNT:
        raise ValidationError(
            f"amount must not exceed {format(MAX_AMOUNT, '.2f')}"
        )

    try:
        normalized = amount.quantize(CENT)
    except InvalidOperation as error:
        raise ValidationError("amount must have at most two decimal places") from error
    if normalized != amount:
        raise ValidationError("amount must have at most two decimal places")
    return normalized


def validate_description(description: str) -> str:
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("description must not be blank")
    return description.strip()


def validate_transaction_type(transaction_type: str) -> str:
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        allowed = ", ".join(ALLOWED_TRANSACTION_TYPES)
        raise ValidationError(f"transaction type must be one of: {allowed}")
    return transaction_type


@dataclass(frozen=True)
class Transaction:
    occurred_on: date
    transaction_type: str
    amount: Decimal
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.occurred_on, date):
            raise ValidationError("transaction date must be a date")
        object.__setattr__(
            self,
            "transaction_type",
            validate_transaction_type(self.transaction_type),
        )
        object.__setattr__(self, "amount", validate_amount(self.amount))
        object.__setattr__(
            self,
            "description",
            validate_description(self.description),
        )

    def query_parameters(self) -> dict[str, Any]:
        return {
            "occurred_on": self.occurred_on,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "description": self.description,
        }


@dataclass(frozen=True)
class InsertedTransaction:
    id: int
    occurred_on: date
    transaction_type: str
    amount: Decimal
    description: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "InsertedTransaction":
        try:
            return cls(
                id=int(row["id"]),
                occurred_on=row["occurred_on"],
                transaction_type=str(row["transaction_type"]),
                amount=Decimal(row["amount"]),
                description=str(row["description"]),
                created_at=row["created_at"],
            )
        except (KeyError, TypeError, ValueError, DecimalException) as error:
            raise TransactionError(
                "the database returned an invalid transaction"
            ) from error

    def as_mapping(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "occurred_on": self.occurred_on,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "description": self.description,
            "created_at": self.created_at,
        }


def load_insert_query(path: Path = INSERT_QUERY_PATH) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise QueryLoadError(str(error)) from error


def add_transaction(
    transaction: Transaction,
    database: str | None = None,
    *,
    query: str | None = None,
) -> InsertedTransaction:
    """Validate and insert one transaction, returning the stored record."""

    if not isinstance(transaction, Transaction):
        raise ValidationError("transaction must be a Transaction")
    resolved_database = resolve_database(database)
    insert_query = query if query is not None else load_insert_query()

    try:
        with psycopg.connect(
            dbname=resolved_database,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_query, transaction.query_parameters())
                inserted = cursor.fetchone()
    except psycopg.Error as error:
        message = str(error).splitlines()[0] if str(error) else error.__class__.__name__
        raise DatabaseError(message) from error

    if inserted is None:
        raise TransactionError("the database did not return the inserted transaction")
    return InsertedTransaction.from_row(inserted)
