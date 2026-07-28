"""Tests for cash-flow calculations and report presentation."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from reporting.cash_flow import (
    CashFlowReport,
    ReportTransaction,
    build_cash_flow_report,
)
from reporting.charts import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    create_cash_flow_waterfall,
    create_monthly_activity_chart,
)
from reporting.tables import (
    initialize_transaction_tables,
    show_transaction_table,
    transactions_frame,
)


def transaction(
    id: int,
    occurred_on: date,
    transaction_type: str,
    amount: str,
    description: str = "Test transaction",
) -> ReportTransaction:
    return ReportTransaction(
        id=id,
        occurred_on=occurred_on,
        transaction_type=transaction_type,
        amount=Decimal(amount),
        description=description,
    )


class CalculationTests(unittest.TestCase):
    def test_totals_months_ordering_and_date_filtering(self) -> None:
        report = build_cash_flow_report(
            [
                transaction(4, date(2026, 3, 1), "expense", "999.00"),
                transaction(3, date(2026, 2, 15), "investment", "300.00"),
                transaction(2, date(2026, 1, 20), "expense", "250.25"),
                transaction(1, date(2026, 1, 5), "income", "1000.50"),
                transaction(5, date(2025, 12, 31), "income", "999.00"),
            ],
            date(2026, 1, 1),
            date(2026, 2, 28),
        )

        self.assertEqual(report.summary.income, Decimal("1000.50"))
        self.assertEqual(report.summary.expenses, Decimal("250.25"))
        self.assertEqual(report.summary.investments, Decimal("300.00"))
        self.assertEqual(report.summary.cash_after_expenses, Decimal("750.25"))
        self.assertEqual(report.summary.net_cash_flow, Decimal("450.25"))
        self.assertEqual(
            [item.month for item in report.monthly],
            [date(2026, 1, 1), date(2026, 2, 1)],
        )
        self.assertEqual(
            [item.id for item in report.transactions],
            [1, 2, 3],
        )

    def test_missing_months_and_empty_period_are_zero_filled(self) -> None:
        report = build_cash_flow_report(
            [],
            date(2025, 12, 15),
            date(2026, 2, 2),
        )

        self.assertEqual(
            [item.month for item in report.monthly],
            [date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)],
        )
        self.assertTrue(
            all(item.net_cash_flow == Decimal("0.00") for item in report.monthly)
        )
        self.assertEqual(report.summary.net_cash_flow, Decimal("0.00"))

    def test_negative_cash_flow_and_type_subtotals(self) -> None:
        report = build_cash_flow_report(
            [
                transaction(1, date(2026, 7, 1), "income", "100.00"),
                transaction(2, date(2026, 7, 2), "expense", "125.00"),
                transaction(3, date(2026, 7, 3), "investment", "25.00"),
            ],
            date(2026, 7, 1),
            date(2026, 7, 31),
        )

        self.assertEqual(report.summary.net_cash_flow, Decimal("-50.00"))
        self.assertEqual(report.subtotal_for("expense"), Decimal("125.00"))
        self.assertEqual(len(report.transactions_for("income")), 1)

    def test_invalid_period_and_transaction_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "end date"):
            build_cash_flow_report([], date(2026, 2, 1), date(2026, 1, 1))
        with self.assertRaisesRegex(ValueError, "invalid transaction type"):
            transaction(1, date(2026, 1, 1), "transfer", "1.00")
        with self.assertRaisesRegex(ValueError, "positive"):
            transaction(1, date(2026, 1, 1), "expense", "0.00")
        with self.assertRaisesRegex(ValueError, "blank"):
            transaction(1, date(2026, 1, 1), "expense", "1.00", "  ")


class ChartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = build_cash_flow_report(
            [
                transaction(1, date(2026, 1, 1), "income", "1000.00"),
                transaction(2, date(2026, 1, 2), "expense", "250.00"),
                transaction(3, date(2026, 2, 2), "investment", "300.00"),
            ],
            date(2026, 1, 1),
            date(2026, 2, 28),
        )

    def test_waterfall_uses_signed_cash_flow_values(self) -> None:
        figure = create_cash_flow_waterfall(self.report)
        trace = figure.data[0]

        self.assertEqual(
            list(trace.x),
            ["Income", "Expenses", "Investments", "Net Cash Flow"],
        )
        self.assertEqual(list(trace.y), [1000.0, -250.0, -300.0, 0])
        self.assertEqual(list(trace.measure), ["relative", "relative", "relative", "total"])

    def test_monthly_chart_contains_three_bars_and_net_line(self) -> None:
        figure = create_monthly_activity_chart(self.report)

        self.assertEqual(
            [trace.name for trace in figure.data],
            ["Income", "Expenses", "Investments", "Net Cash Flow"],
        )
        self.assertEqual(figure.data[0].marker.color, INCOME_COLOR)
        self.assertEqual(figure.data[1].marker.color, EXPENSE_COLOR)
        self.assertEqual(figure.data[2].marker.color, INVESTMENT_COLOR)
        self.assertEqual(list(figure.data[3].y), [750.0, -300.0])


class TableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report: CashFlowReport = build_cash_flow_report(
            [
                transaction(
                    1,
                    date(2026, 7, 1),
                    "expense",
                    "12.50",
                    "Lunch",
                )
            ],
            date(2026, 7, 1),
            date(2026, 7, 31),
        )

    def test_transaction_frame_has_stable_columns_and_numeric_amount(self) -> None:
        frame = transactions_frame(self.report, "expense")

        self.assertEqual(list(frame.columns), ["Date", "Description", "Amount"])
        self.assertEqual(frame.to_dict("records"), [
            {
                "Date": "2026-07-01",
                "Description": "Lunch",
                "Amount": 12.5,
            }
        ])

    @patch("reporting.tables.init_notebook_mode")
    def test_table_assets_are_initialized_for_offline_reports(
        self,
        init_notebook_mode_mock,
    ) -> None:
        initialize_transaction_tables()

        init_notebook_mode_mock.assert_called_once_with(
            all_interactive=False,
            connected=False,
        )

    @patch("reporting.tables.show")
    def test_interactive_table_configuration(self, show_mock) -> None:
        show_transaction_table(self.report, "expense")

        show_mock.assert_called_once()
        args, kwargs = show_mock.call_args
        self.assertEqual(len(args[0]), 1)
        self.assertEqual(kwargs["caption"], "Expense subtotal: $12.50")
        self.assertFalse(kwargs["connected"])
        self.assertEqual(kwargs["maxBytes"], 0)
        self.assertEqual(kwargs["column_filters"], "header")

    @patch("reporting.tables.show")
    @patch("builtins.print")
    def test_empty_table_prints_message(self, print_mock, show_mock) -> None:
        show_transaction_table(self.report, "income")

        print_mock.assert_called_once_with(
            "No income transactions occurred in this period."
        )
        show_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
