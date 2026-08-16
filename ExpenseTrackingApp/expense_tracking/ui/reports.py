"""Streamlit report-generation page."""

from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

from expense_tracking.errors import ExpenseTrackingError
from expense_tracking.reports import ReportPeriod, generate_report


REPORT_MODES = ("Month", "Year", "Custom range")
MONTH_NAMES = tuple(calendar.month_name[1:])


def build_gui_report_period(
    mode: str,
    *,
    year: int,
    month: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ReportPeriod:
    """Build a validated report period from the visible GUI controls."""

    if mode == "Month":
        if month is None:
            raise ValueError("month is required")
        return ReportPeriod.for_month(year, month)
    if mode == "Year":
        return ReportPeriod.for_year(year)
    if mode == "Custom range":
        if start_date is None or end_date is None:
            raise ValueError("start and end dates are required")
        return ReportPeriod.for_range(start_date, end_date)
    raise ValueError(f"unknown report mode: {mode}")


def load_report_download(output_path: Path) -> dict[str, Any]:
    """Read a generated report into session-safe download data."""

    return {
        "filename": output_path.name,
        "data": output_path.read_bytes(),
    }


def render_report_page() -> None:
    """Render report period controls and an HTML download action."""

    today = date.today()
    st.title("Generate Report")
    st.caption("Create a self-contained cash-flow report for a selected period.")

    mode = st.radio(
        "Reporting period",
        REPORT_MODES,
        horizontal=True,
    )

    with st.form("generate_report_form"):
        if mode == "Month":
            month_name = st.selectbox(
                "Month",
                MONTH_NAMES,
                index=today.month - 1,
            )
            year = int(
                st.number_input(
                    "Year",
                    min_value=1,
                    max_value=9999,
                    value=today.year,
                    step=1,
                )
            )
            month = MONTH_NAMES.index(month_name) + 1
            start_date = None
            end_date = None
        elif mode == "Year":
            year = int(
                st.number_input(
                    "Year",
                    min_value=1,
                    max_value=9999,
                    value=today.year,
                    step=1,
                )
            )
            month = None
            start_date = None
            end_date = None
        else:
            start_column, end_column = st.columns(2)
            with start_column:
                start_date = st.date_input(
                    "Start date",
                    value=today.replace(day=1),
                )
            with end_column:
                end_date = st.date_input("End date", value=today)
            year = today.year
            month = None

        submitted = st.form_submit_button(
            "Generate report",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            period = build_gui_report_period(
                mode,
                year=year,
                month=month,
                start_date=start_date,
                end_date=end_date,
            )
            with st.spinner("Generating report…"):
                output_path = generate_report(period=period)
                download = load_report_download(output_path)
        except (ExpenseTrackingError, OSError, ValueError) as error:
            st.error(str(error))
        except Exception:
            st.error(
                "The report could not be generated because of an unexpected error."
            )
        else:
            st.session_state["latest_report_download"] = download
            st.success(f"Report ready: {download['filename']}")

    latest_report = st.session_state.get("latest_report_download")
    if latest_report is not None:
        st.download_button(
            "Download report",
            data=latest_report["data"],
            file_name=latest_report["filename"],
            mime="text/html",
            type="primary",
            use_container_width=True,
        )
