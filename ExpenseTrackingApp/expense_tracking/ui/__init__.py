"""Streamlit pages for the local expense tracker."""

from expense_tracking.ui.reports import render_report_page
from expense_tracking.ui.transactions import render_add_transaction_page

__all__ = ["render_add_transaction_page", "render_report_page"]
