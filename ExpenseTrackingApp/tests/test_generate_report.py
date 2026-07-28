"""Tests for the cash-flow report command."""

from __future__ import annotations

import argparse
import io
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.generate_report import (
    REPO_ROOT,
    ReportPeriod,
    build_quarto_command,
    build_render_environment,
    generate_report,
    main,
    parse_args,
    report_period_from_args,
)


class PeriodArgumentTests(unittest.TestCase):
    def test_month_period(self) -> None:
        args = parse_args(["--month", "2026-02"])
        period = report_period_from_args(args)

        self.assertEqual(period.start_date, date(2026, 2, 1))
        self.assertEqual(period.end_date, date(2026, 2, 28))
        self.assertEqual(period.end_date_exclusive, date(2026, 3, 1))
        self.assertEqual(period.default_filename, "cash-flow-2026-02.html")

    def test_leap_month_and_year_periods(self) -> None:
        month = report_period_from_args(parse_args(["--month", "2024-02"]))
        year = report_period_from_args(parse_args(["--year", "2026"]))

        self.assertEqual(month.end_date, date(2024, 2, 29))
        self.assertEqual(year.start_date, date(2026, 1, 1))
        self.assertEqual(year.end_date, date(2026, 12, 31))
        self.assertEqual(year.default_filename, "cash-flow-2026.html")

    def test_explicit_range_is_inclusive(self) -> None:
        args = parse_args(
            ["--start", "2026-01-01", "--end", "2026-07-31"]
        )
        period = report_period_from_args(args)

        self.assertEqual(period.end_date, date(2026, 7, 31))
        self.assertEqual(period.end_date_exclusive, date(2026, 8, 1))
        self.assertEqual(
            period.default_filename,
            "cash-flow-2026-01-01-to-2026-07-31.html",
        )

    def test_pgdatabase_is_default(self) -> None:
        with patch.dict("os.environ", {"PGDATABASE": "configured_db"}, clear=True):
            args = parse_args(["--year", "2026"])
        self.assertEqual(args.database, "configured_db")

    def test_invalid_period_combinations_exit_with_argparse_status(self) -> None:
        invalid = [
            [],
            ["--month", "2026-01", "--year", "2026"],
            ["--start", "2026-01-01"],
            ["--year", "2026", "--end", "2026-01-31"],
            ["--start", "2026-02-01", "--end", "2026-01-01"],
            ["--month", "2026-13"],
        ]
        for argv in invalid:
            with self.subTest(argv=argv):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        parse_args(argv)
                self.assertEqual(raised.exception.code, 2)


class RenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.period = ReportPeriod(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            label="July 2026",
            default_filename="cash-flow-2026-07.html",
        )

    def test_quarto_command_and_environment_are_normalized(self) -> None:
        command = build_quarto_command(
            output_filename="report.html",
            quarto="/usr/local/bin/quarto",
        )

        self.assertEqual(command[:3], [
            "/usr/local/bin/quarto",
            "render",
            str(REPO_ROOT / "reports" / "cash_flow.qmd"),
        ])
        self.assertNotIn("-P", command)
        self.assertEqual(
            command[command.index("--output-dir") + 1],
            "output",
        )

        environment = build_render_environment(
            period=self.period,
            database="expense_tracking_app",
        )
        self.assertEqual(environment["EXPENSE_REPORT_START_DATE"], "2026-07-01")
        self.assertEqual(environment["EXPENSE_REPORT_END_DATE"], "2026-07-31")
        self.assertEqual(
            environment["EXPENSE_REPORT_DATABASE"],
            "expense_tracking_app",
        )
        self.assertEqual(environment["EXPENSE_REPORT_PERIOD_LABEL"], "July 2026")
        self.assertIn(str(REPO_ROOT), environment["PYTHONPATH"])

    @patch("scripts.generate_report.subprocess.run")
    @patch("scripts.generate_report.uuid.uuid4")
    def test_successful_render_replaces_output_after_quarto_finishes(
        self,
        uuid_mock,
        run_mock,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.html"
            output.write_text("old", encoding="utf-8")
            uuid_mock.return_value.hex = "test"

            def create_rendered(command, **kwargs):
                filename = command[command.index("--output") + 1]
                generated = (
                    REPO_ROOT / "reports" / "output" / filename
                )
                generated.parent.mkdir(parents=True, exist_ok=True)
                generated.write_text("new", encoding="utf-8")

            run_mock.side_effect = create_rendered
            generate_report(
                period=self.period,
                database="expense_tracking_app",
                output_path=output,
                quarto="/usr/local/bin/quarto",
            )

            self.assertEqual(output.read_text(encoding="utf-8"), "new")
            run_mock.assert_called_once()
            self.assertTrue(run_mock.call_args.kwargs["check"])
            self.assertEqual(
                run_mock.call_args.kwargs["env"]["EXPENSE_REPORT_DATABASE"],
                "expense_tracking_app",
            )

    @patch("scripts.generate_report.subprocess.run")
    @patch("scripts.generate_report.uuid.uuid4")
    def test_failed_render_preserves_existing_output(
        self,
        uuid_mock,
        run_mock,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.html"
            output.write_text("old", encoding="utf-8")
            uuid_mock.return_value.hex = "failed-test"
            run_mock.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["quarto", "render"],
            )

            with self.assertRaises(subprocess.CalledProcessError):
                generate_report(
                    period=self.period,
                    database="expense_tracking_app",
                    output_path=output,
                    quarto="/usr/local/bin/quarto",
                )

            self.assertEqual(output.read_text(encoding="utf-8"), "old")
            self.assertFalse(
                (
                    REPO_ROOT
                    / "reports"
                    / "output"
                    / "cash-flow-render-failed-test.html"
                ).exists()
            )

    @patch("scripts.generate_report.generate_report")
    @patch("scripts.generate_report.shutil.which", return_value="/usr/local/bin/quarto")
    def test_main_prints_created_path(self, which_mock, generate_mock) -> None:
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.html"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    ["--month", "2026-07", "--output", str(output)]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("Created cash-flow report:", stdout.getvalue())
        generate_mock.assert_called_once()
        which_mock.assert_called_once_with("quarto")

    @patch("scripts.generate_report.shutil.which", return_value=None)
    def test_missing_quarto_is_concise(self, which_mock) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(["--year", "2026"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Quarto is not installed", stderr.getvalue())
        which_mock.assert_called_once_with("quarto")


if __name__ == "__main__":
    unittest.main()
