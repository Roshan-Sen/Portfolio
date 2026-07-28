"""Pandas and ITables presentation helpers."""

from __future__ import annotations

import pandas as pd
from itables import JavascriptFunction, init_notebook_mode, show

from reporting.cash_flow import CashFlowReport


CURRENCY_RENDERER = JavascriptFunction(
    """
    function(data, type) {
      if (type === 'display' || type === 'filter') {
        return new Intl.NumberFormat(
          'en-US',
          {style: 'currency', currency: 'USD'}
        ).format(data);
      }
      return data;
    }
    """
)


def initialize_transaction_tables() -> None:
    """Embed the DataTables assets required by offline report tables."""

    init_notebook_mode(all_interactive=False, connected=False)


def transactions_frame(
    report: CashFlowReport,
    transaction_type: str,
) -> pd.DataFrame:
    rows = [
        {
            "Date": transaction.occurred_on.isoformat(),
            "Description": transaction.description,
            "Amount": float(transaction.amount),
        }
        for transaction in report.transactions_for(transaction_type)
    ]
    return pd.DataFrame(rows, columns=["Date", "Description", "Amount"])


def show_transaction_table(
    report: CashFlowReport,
    transaction_type: str,
) -> None:
    frame = transactions_frame(report, transaction_type)
    if frame.empty:
        print(f"No {transaction_type} transactions occurred in this period.")
        return

    show(
        frame,
        caption=(
            f"{transaction_type.title()} subtotal: "
            f"${report.subtotal_for(transaction_type):,.2f}"
        ),
        connected=False,
        pageLength=10,
        lengthMenu=[10, 25, 50, -1],
        scrollX=True,
        column_filters="header",
        maxBytes=0,
        columnDefs=[
            {"targets": 0, "type": "date"},
            {"targets": 2, "render": CURRENCY_RENDERER, "className": "dt-body-right"},
        ],
        order=[[0, "asc"]],
    )
