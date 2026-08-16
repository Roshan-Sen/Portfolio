"""Tests for the local Streamlit user interface."""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from expense_tracking.errors import (
    DatabaseError,
    ReportGenerationError,
    ValidationError,
)
from expense_tracking.transactions import InsertedTransaction
from expense_tracking.ui.reports import (
    build_gui_report_period,
    load_report_download,
)
from expense_tracking.ui.transactions import parse_gui_amount


TRANSACTION_APP = """
from expense_tracking.ui.transactions import render_add_transaction_page
render_add_transaction_page()
"""

REPORT_APP = """
from expense_tracking.ui.reports import render_report_page
render_report_page()
"""


class LauncherTests(unittest.TestCase):
    def test_launcher_renders_default_page(self) -> None:
        launcher = Path(__file__).resolve().parent.parent / "streamlit_app.py"

        app = AppTest.from_file(launcher).run()

        self.assertEqual([title.value for title in app.title], ["Add Transaction"])
        self.assertEqual(len(app.exception), 0)


class GuiHelperTests(unittest.TestCase):
    def test_amount_is_parsed_directly_as_decimal(self) -> None:
        self.assertEqual(parse_gui_amount(" 12.30 "), Decimal("12.30"))

        for value in ("", "not-a-number", "NaN", "0", "1.001"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    parse_gui_amount(value)

    def test_all_report_period_modes_use_domain_model(self) -> None:
        month = build_gui_report_period("Month", year=2024, month=2)
        year = build_gui_report_period("Year", year=2026)
        custom = build_gui_report_period(
            "Custom range",
            year=2026,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )

        self.assertEqual(month.end_date, date(2024, 2, 29))
        self.assertEqual(year.default_filename, "cash-flow-2026.html")
        self.assertEqual(custom.start_date, date(2026, 3, 1))
        self.assertEqual(custom.end_date, date(2026, 3, 15))

    def test_custom_period_rejects_reversed_dates(self) -> None:
        with self.assertRaisesRegex(ValidationError, "end date"):
            build_gui_report_period(
                "Custom range",
                year=2026,
                start_date=date(2026, 3, 15),
                end_date=date(2026, 3, 1),
            )

    def test_report_download_uses_generated_name_and_bytes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "cash-flow-2026.html"
            output.write_bytes(b"<html>report</html>")

            download = load_report_download(output)

        self.assertEqual(download["filename"], "cash-flow-2026.html")
        self.assertEqual(download["data"], b"<html>report</html>")


class TransactionPageTests(unittest.TestCase):
    def test_page_defaults_and_invalid_input(self) -> None:
        with patch("expense_tracking.ui.transactions.add_transaction") as add_mock:
            app = AppTest.from_string(TRANSACTION_APP).run()
            app.button[0].click().run()

        self.assertEqual([title.value for title in app.title], ["Add Transaction"])
        self.assertEqual(app.selectbox[0].value, "expense")
        self.assertEqual(
            app.selectbox[0].options,
            ["Expense", "Income", "Investment"],
        )
        self.assertEqual(app.date_input[0].value, date.today())
        self.assertIn("amount must not be blank", app.error[0].value)
        add_mock.assert_not_called()
        self.assertEqual(len(app.exception), 0)

    def test_success_uses_service_and_clears_free_text_fields(self) -> None:
        inserted = InsertedTransaction(
            id=42,
            occurred_on=date(2026, 8, 15),
            transaction_type="income",
            amount=Decimal("2500.00"),
            description="Paycheck",
            created_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
        )
        with patch(
            "expense_tracking.ui.transactions.add_transaction",
            return_value=inserted,
        ) as add_mock:
            app = AppTest.from_string(TRANSACTION_APP).run()
            app.date_input[0].set_value(date(2026, 8, 15))
            app.selectbox[0].select("income")
            app.text_input[0].input("2500.00")
            app.text_input[1].input("Paycheck")
            app.button[0].click().run()

        transaction = add_mock.call_args.args[0]
        self.assertEqual(transaction.amount, Decimal("2500.00"))
        self.assertEqual(transaction.transaction_type, "income")
        self.assertEqual(app.date_input[0].value, date(2026, 8, 15))
        self.assertEqual(app.selectbox[0].value, "income")
        self.assertEqual([field.value for field in app.text_input], ["", ""])
        self.assertIn("Added transaction #42", app.success[0].value)
        self.assertEqual(len(app.exception), 0)

    def test_database_error_is_shown_without_clearing_input(self) -> None:
        with patch(
            "expense_tracking.ui.transactions.add_transaction",
            side_effect=DatabaseError("connection failed"),
        ):
            app = AppTest.from_string(TRANSACTION_APP).run()
            app.text_input[0].input("18.75")
            app.text_input[1].input("Lunch")
            app.button[0].click().run()

        self.assertIn("connection failed", app.error[0].value)
        self.assertEqual(
            [field.value for field in app.text_input],
            ["18.75", "Lunch"],
        )
        self.assertEqual(len(app.success), 0)
        self.assertEqual(len(app.exception), 0)


class ReportPageTests(unittest.TestCase):
    def test_success_creates_download_and_calls_service(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "cash-flow-2024-02.html"
            output.write_bytes(b"<html>February report</html>")
            with patch(
                "expense_tracking.ui.reports.generate_report",
                return_value=output,
            ) as generate_mock:
                app = AppTest.from_string(REPORT_APP).run()
                app.selectbox[0].select("February")
                app.number_input[0].set_value(2024)
                app.button[0].click().run()

        period = generate_mock.call_args.kwargs["period"]
        self.assertEqual(period.start_date, date(2024, 2, 1))
        self.assertEqual(period.end_date, date(2024, 2, 29))
        self.assertEqual(len(app.download_button), 1)
        self.assertEqual(app.download_button[0].label, "Download report")
        self.assertIn("cash-flow-2024-02.html", app.success[0].value)
        self.assertEqual(len(app.exception), 0)

    def test_failed_generation_preserves_previous_download(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "cash-flow-2026.html"
            output.write_bytes(b"<html>report</html>")
            with patch(
                "expense_tracking.ui.reports.generate_report",
                side_effect=[
                    output,
                    ReportGenerationError("Quarto failed."),
                ],
            ):
                app = AppTest.from_string(REPORT_APP).run()
                app.button[0].click().run()
                app.button[0].click().run()

        self.assertIn("Quarto failed.", app.error[0].value)
        self.assertEqual(len(app.download_button), 1)
        self.assertEqual(len(app.exception), 0)

    def test_custom_range_validation_does_not_generate(self) -> None:
        with patch("expense_tracking.ui.reports.generate_report") as generate_mock:
            app = AppTest.from_string(REPORT_APP).run()
            app.radio[0].set_value("Custom range").run()
            app.date_input[0].set_value(date(2026, 8, 15))
            app.date_input[1].set_value(date(2026, 8, 1))
            app.button[0].click().run()

        self.assertIn("end date must be on or after start date", app.error[0].value)
        generate_mock.assert_not_called()
        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
