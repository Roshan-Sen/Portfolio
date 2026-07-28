"""Generate a self-contained cash-flow dashboard with Quarto."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_SOURCE = REPO_ROOT / "reports" / "cash_flow.qmd"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports" / "output"
DEFAULT_DATABASE = "expense_tracking_app"


@dataclass(frozen=True)
class ReportPeriod:
    start_date: date
    end_date: date
    label: str
    default_filename: str

    @property
    def end_date_exclusive(self) -> date:
        return self.end_date + timedelta(days=1)


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from error


def parse_month(value: str) -> tuple[int, int]:
    try:
        parsed = date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise argparse.ArgumentTypeError("month must use YYYY-MM format") from error
    if parsed.strftime("%Y-%m") != value:
        raise argparse.ArgumentTypeError("month must use YYYY-MM format")
    return parsed.year, parsed.month


def parse_year(value: str) -> int:
    if len(value) != 4 or not value.isascii() or not value.isdigit():
        raise argparse.ArgumentTypeError("year must use YYYY format")
    year = int(value)
    if year < 1:
        raise argparse.ArgumentTypeError("year must be greater than zero")
    return year


def parse_database(value: str) -> str:
    database = value.strip()
    if not database:
        raise argparse.ArgumentTypeError("database must not be blank")
    return database


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an interactive cash-flow HTML report.",
        epilog=(
            "PostgreSQL connection settings use the standard PGHOST, PGPORT, "
            "PGUSER, PGPASSWORD, and PGPASSFILE environment variables or .pgpass."
        ),
    )
    period = parser.add_mutually_exclusive_group(required=True)
    period.add_argument("--month", type=parse_month, metavar="YYYY-MM")
    period.add_argument("--year", type=parse_year, metavar="YYYY")
    period.add_argument("--start", type=parse_iso_date, metavar="YYYY-MM-DD")
    parser.add_argument(
        "--end",
        type=parse_iso_date,
        metavar="YYYY-MM-DD",
        help="Inclusive end date; required with --start.",
    )
    parser.add_argument(
        "--database",
        type=parse_database,
        default=os.environ.get("PGDATABASE") or DEFAULT_DATABASE,
        help=(
            "PostgreSQL database name "
            f"(default: PGDATABASE or {DEFAULT_DATABASE})."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output HTML path (default: reports/output/<period>.html).",
    )
    args = parser.parse_args(argv)

    if args.start is not None and args.end is None:
        parser.error("--end is required with --start")
    if args.start is None and args.end is not None:
        parser.error("--end can only be used with --start")
    if args.start is not None and args.end < args.start:
        parser.error("--end must be on or after --start")
    return args


def report_period_from_args(args: argparse.Namespace) -> ReportPeriod:
    if args.month is not None:
        year, month = args.month
        start = date(year, month, 1)
        next_month = (
            date(year + 1, 1, 1)
            if month == 12
            else date(year, month + 1, 1)
        )
        end = next_month - timedelta(days=1)
        value = start.strftime("%Y-%m")
        return ReportPeriod(
            start_date=start,
            end_date=end,
            label=start.strftime("%B %Y"),
            default_filename=f"cash-flow-{value}.html",
        )

    if args.year is not None:
        year = args.year
        return ReportPeriod(
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            label=str(year),
            default_filename=f"cash-flow-{year}.html",
        )

    assert args.start is not None and args.end is not None
    return ReportPeriod(
        start_date=args.start,
        end_date=args.end,
        label=f"{args.start.isoformat()} through {args.end.isoformat()}",
        default_filename=(
            f"cash-flow-{args.start.isoformat()}-to-{args.end.isoformat()}.html"
        ),
    )


def build_quarto_command(
    *,
    output_filename: str,
    quarto: str,
) -> list[str]:
    return [
        quarto,
        "render",
        str(REPORT_SOURCE),
        "--execute",
        "--no-cache",
        "--output",
        output_filename,
        "--output-dir",
        "output",
    ]


def build_render_environment(
    *,
    period: ReportPeriod,
    database: str,
) -> dict[str, str]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment.update(
        {
            "EXPENSE_REPORT_START_DATE": period.start_date.isoformat(),
            "EXPENSE_REPORT_END_DATE": period.end_date.isoformat(),
            "EXPENSE_REPORT_DATABASE": database,
            "EXPENSE_REPORT_PERIOD_LABEL": period.label,
            "PYTHONPATH": (
                f"{REPO_ROOT}{os.pathsep}{existing_pythonpath}"
                if existing_pythonpath
                else str(REPO_ROOT)
            ),
        }
    )
    return environment


def generate_report(
    *,
    period: ReportPeriod,
    database: str,
    output_path: Path,
    quarto: str,
) -> None:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    staging_name = f"cash-flow-render-{uuid.uuid4().hex}.html"
    staging_path = DEFAULT_OUTPUT_DIR / staging_name
    command = build_quarto_command(
        output_filename=staging_name,
        quarto=quarto,
    )
    try:
        subprocess.run(
            command,
            cwd=REPORT_SOURCE.parent,
            env=build_render_environment(period=period, database=database),
            check=True,
        )
        if not staging_path.is_file():
            raise RuntimeError(f"Quarto did not create {staging_path}")
        staging_path.replace(output_path)
    finally:
        if staging_path.is_file():
            staging_path.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    period = report_period_from_args(args)
    output_path = (
        args.output
        if args.output is not None
        else DEFAULT_OUTPUT_DIR / period.default_filename
    )
    quarto = shutil.which("quarto")
    if quarto is None:
        print(
            "Report error: Quarto is not installed or is not available on PATH.",
            file=sys.stderr,
        )
        return 1

    try:
        generate_report(
            period=period,
            database=args.database,
            output_path=output_path,
            quarto=quarto,
        )
    except subprocess.CalledProcessError as error:
        print(
            f"Report error: Quarto exited with status {error.returncode}.",
            file=sys.stderr,
        )
        return 1
    except (OSError, RuntimeError) as error:
        print(f"Report error: {error}", file=sys.stderr)
        return 1

    print(f"Created cash-flow report: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
