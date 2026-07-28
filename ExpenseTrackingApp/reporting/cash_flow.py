"""Pure cash-flow report calculations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable


ALLOWED_TRANSACTION_TYPES = ("income", "expense", "investment")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ReportTransaction:
    """One transaction used by a generated report."""

    id: int
    occurred_on: date
    transaction_type: str
    amount: Decimal
    description: str

    def __post_init__(self) -> None:
        if self.transaction_type not in ALLOWED_TRANSACTION_TYPES:
            raise ValueError(f"invalid transaction type: {self.transaction_type!r}")
        if not self.amount.is_finite() or self.amount <= 0:
            raise ValueError("transaction amount must be positive and finite")
        if not self.description.strip():
            raise ValueError("transaction description must not be blank")


@dataclass(frozen=True)
class MonthlySummary:
    """Cash-flow totals for one calendar month."""

    month: date
    income: Decimal = ZERO
    expenses: Decimal = ZERO
    investments: Decimal = ZERO

    @property
    def net_cash_flow(self) -> Decimal:
        return self.income - self.expenses - self.investments


@dataclass(frozen=True)
class CashFlowSummary:
    """Cash-flow totals for the complete reporting period."""

    start_date: date
    end_date: date
    income: Decimal
    expenses: Decimal
    investments: Decimal

    @property
    def cash_after_expenses(self) -> Decimal:
        return self.income - self.expenses

    @property
    def net_cash_flow(self) -> Decimal:
        return self.income - self.expenses - self.investments


@dataclass(frozen=True)
class CashFlowReport:
    """Calculated report data, independent of its output format."""

    summary: CashFlowSummary
    monthly: tuple[MonthlySummary, ...]
    transactions: tuple[ReportTransaction, ...]

    def transactions_for(self, transaction_type: str) -> tuple[ReportTransaction, ...]:
        if transaction_type not in ALLOWED_TRANSACTION_TYPES:
            raise ValueError(f"invalid transaction type: {transaction_type!r}")
        return tuple(
            transaction
            for transaction in self.transactions
            if transaction.transaction_type == transaction_type
        )

    def subtotal_for(self, transaction_type: str) -> Decimal:
        return sum(
            (
                transaction.amount
                for transaction in self.transactions_for(transaction_type)
            ),
            ZERO,
        )


def first_of_month(value: date) -> date:
    return value.replace(day=1)


def next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def build_cash_flow_report(
    transactions: Iterable[ReportTransaction],
    start_date: date,
    end_date: date,
) -> CashFlowReport:
    """Build a report for an inclusive date range."""

    if end_date < start_date:
        raise ValueError("end date must be on or after start date")

    selected = sorted(
        (
            transaction
            for transaction in transactions
            if start_date <= transaction.occurred_on <= end_date
        ),
        key=lambda transaction: (transaction.occurred_on, transaction.id),
    )

    totals = {transaction_type: ZERO for transaction_type in ALLOWED_TRANSACTION_TYPES}
    monthly_totals: dict[date, dict[str, Decimal]] = defaultdict(
        lambda: {
            transaction_type: ZERO
            for transaction_type in ALLOWED_TRANSACTION_TYPES
        }
    )

    for transaction in selected:
        totals[transaction.transaction_type] += transaction.amount
        monthly_totals[first_of_month(transaction.occurred_on)][
            transaction.transaction_type
        ] += transaction.amount

    monthly: list[MonthlySummary] = []
    month = first_of_month(start_date)
    final_month = first_of_month(end_date)
    while month <= final_month:
        month_totals = monthly_totals[month]
        monthly.append(
            MonthlySummary(
                month=month,
                income=month_totals["income"],
                expenses=month_totals["expense"],
                investments=month_totals["investment"],
            )
        )
        month = next_month(month)

    return CashFlowReport(
        summary=CashFlowSummary(
            start_date=start_date,
            end_date=end_date,
            income=totals["income"],
            expenses=totals["expense"],
            investments=totals["investment"],
        ),
        monthly=tuple(monthly),
        transactions=tuple(selected),
    )
