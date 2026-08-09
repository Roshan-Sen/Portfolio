"""Generate a self-contained cash-flow dashboard with Quarto."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from expense_tracking.config import (
    DEFAULT_DATABASE,
    DEFAULT_REPORT_OUTPUT_DIR,
    resolve_database,
)
from expense_tracking.errors import ReportGenerationError, ValidationError
from expense_tracking.reports import ReportPeriod, generate_report


DEFAULT_OUTPUT_DIR = DEFAULT_REPORT_OUTPUT_DIR


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
    try:
        return resolve_database(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


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
        default=resolve_database(),
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
        return ReportPeriod.for_month(year, month)
    if args.year is not None:
        return ReportPeriod.for_year(args.year)

    assert args.start is not None and args.end is not None
    return ReportPeriod.for_range(args.start, args.end)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    period = report_period_from_args(args)

    try:
        output_path = generate_report(
            period=period,
            database=args.database,
            output_path=args.output,
        )
    except ReportGenerationError as error:
        print(f"Report error: {error}", file=sys.stderr)
        return 1

    print(f"Created cash-flow report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
