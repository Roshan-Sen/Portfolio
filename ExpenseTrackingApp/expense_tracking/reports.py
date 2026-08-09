"""Validated cash-flow report periods and Quarto orchestration."""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from expense_tracking.config import (
    DEFAULT_REPORT_OUTPUT_DIR,
    PROJECT_ROOT,
    REPORT_SOURCE,
    resolve_database,
)
from expense_tracking.errors import ReportGenerationError, ValidationError


@dataclass(frozen=True)
class ReportPeriod:
    start_date: date
    end_date: date
    label: str
    default_filename: str

    def __post_init__(self) -> None:
        if not isinstance(self.start_date, date) or not isinstance(self.end_date, date):
            raise ValidationError("report dates must be date values")
        if self.end_date < self.start_date:
            raise ValidationError("end date must be on or after start date")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValidationError("report period label must not be blank")
        if not isinstance(self.default_filename, str) or not self.default_filename.strip():
            raise ValidationError("report filename must not be blank")

    @property
    def end_date_exclusive(self) -> date:
        return self.end_date + timedelta(days=1)

    @classmethod
    def for_month(cls, year: int, month: int) -> "ReportPeriod":
        try:
            start = date(year, month, 1)
        except (TypeError, ValueError) as error:
            raise ValidationError("month must identify a valid calendar month") from error
        next_month = (
            date(year + 1, 1, 1)
            if month == 12
            else date(year, month + 1, 1)
        )
        value = start.strftime("%Y-%m")
        return cls(
            start_date=start,
            end_date=next_month - timedelta(days=1),
            label=start.strftime("%B %Y"),
            default_filename=f"cash-flow-{value}.html",
        )

    @classmethod
    def for_year(cls, year: int) -> "ReportPeriod":
        try:
            start = date(year, 1, 1)
            end = date(year, 12, 31)
        except (TypeError, ValueError) as error:
            raise ValidationError("year must identify a valid calendar year") from error
        return cls(
            start_date=start,
            end_date=end,
            label=str(year),
            default_filename=f"cash-flow-{year}.html",
        )

    @classmethod
    def for_range(cls, start_date: date, end_date: date) -> "ReportPeriod":
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise ValidationError("report dates must be date values")
        return cls(
            start_date=start_date,
            end_date=end_date,
            label=f"{start_date.isoformat()} through {end_date.isoformat()}",
            default_filename=(
                f"cash-flow-{start_date.isoformat()}-to-{end_date.isoformat()}.html"
            ),
        )


def build_quarto_command(*, output_filename: str, quarto: str) -> list[str]:
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


def build_render_environment(*, period: ReportPeriod, database: str) -> dict[str, str]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment.update(
        {
            "EXPENSE_REPORT_START_DATE": period.start_date.isoformat(),
            "EXPENSE_REPORT_END_DATE": period.end_date.isoformat(),
            "EXPENSE_REPORT_DATABASE": database,
            "EXPENSE_REPORT_PERIOD_LABEL": period.label,
            "PYTHONPATH": (
                f"{PROJECT_ROOT}{os.pathsep}{existing_pythonpath}"
                if existing_pythonpath
                else str(PROJECT_ROOT)
            ),
        }
    )
    return environment


def generate_report(
    *,
    period: ReportPeriod,
    database: str | None = None,
    output_path: Path | None = None,
    quarto: str | None = None,
) -> Path:
    """Generate a self-contained report and return its absolute output path."""

    if not isinstance(period, ReportPeriod):
        raise ValidationError("period must be a ReportPeriod")
    resolved_database = resolve_database(database)
    resolved_output = Path(
        output_path
        if output_path is not None
        else DEFAULT_REPORT_OUTPUT_DIR / period.default_filename
    ).resolve()
    resolved_quarto = quarto if quarto is not None else shutil.which("quarto")
    if resolved_quarto is None:
        raise ReportGenerationError(
            "Quarto is not installed or is not available on PATH."
        )

    staging_name = f"cash-flow-render-{uuid.uuid4().hex}.html"
    staging_path = DEFAULT_REPORT_OUTPUT_DIR / staging_name
    command = build_quarto_command(
        output_filename=staging_name,
        quarto=resolved_quarto,
    )
    try:
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            command,
            cwd=REPORT_SOURCE.parent,
            env=build_render_environment(
                period=period,
                database=resolved_database,
            ),
            check=True,
        )
        if not staging_path.is_file():
            raise RuntimeError(f"Quarto did not create {staging_path}")
        staging_path.replace(resolved_output)
    except subprocess.CalledProcessError as error:
        raise ReportGenerationError(
            f"Quarto exited with status {error.returncode}."
        ) from error
    except (OSError, RuntimeError) as error:
        raise ReportGenerationError(str(error)) from error
    finally:
        try:
            if staging_path.is_file():
                staging_path.unlink()
        except OSError as error:
            raise ReportGenerationError(str(error)) from error

    return resolved_output
