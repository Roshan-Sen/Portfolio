"""Plotly chart builders for cash-flow reports."""

from __future__ import annotations

from plotly import graph_objects as go

from reporting.cash_flow import CashFlowReport


INCOME_COLOR = "#198754"
EXPENSE_COLOR = "#dc3545"
INVESTMENT_COLOR = "#0d6efd"
POSITIVE_NET_COLOR = "#198754"
NEGATIVE_NET_COLOR = "#dc3545"
NEUTRAL_NET_COLOR = "#6c757d"


def create_cash_flow_waterfall(report: CashFlowReport) -> go.Figure:
    summary = report.summary
    net_color = (
        POSITIVE_NET_COLOR if summary.net_cash_flow >= 0 else NEGATIVE_NET_COLOR
    )
    figure = go.Figure(
        go.Waterfall(
            name="Cash flow",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["Income", "Expenses", "Investments", "Net Cash Flow"],
            y=[
                float(summary.income),
                -float(summary.expenses),
                -float(summary.investments),
                0,
            ],
            text=[
                f"${summary.income:,.2f}",
                f"-${summary.expenses:,.2f}",
                f"-${summary.investments:,.2f}",
                f"${summary.net_cash_flow:,.2f}",
            ],
            textposition="outside",
            increasing={"marker": {"color": INCOME_COLOR}},
            decreasing={"marker": {"color": EXPENSE_COLOR}},
            totals={"marker": {"color": net_color}},
            connector={"line": {"color": "#6c757d"}},
        )
    )
    figure.update_layout(
        margin={"l": 30, "r": 30, "t": 30, "b": 30},
        showlegend=False,
        yaxis_title="Amount ($)",
        hovermode="x",
    )
    figure.update_yaxes(tickprefix="$", separatethousands=True)
    return figure


def create_monthly_net_cash_flow_chart(report: CashFlowReport) -> go.Figure:
    """Render one signed, color-coded net-cash-flow bar per month."""

    spans_multiple_years = len({summary.month.year for summary in report.monthly}) > 1
    label_format = "%b '%y" if spans_multiple_years else "%b"
    months = [summary.month.strftime(label_format) for summary in report.monthly]
    values = [float(summary.net_cash_flow) for summary in report.monthly]
    colors = [
        (
            POSITIVE_NET_COLOR
            if value > 0
            else NEGATIVE_NET_COLOR
            if value < 0
            else NEUTRAL_NET_COLOR
        )
        for value in values
    ]
    figure = go.Figure(
        go.Bar(
            name="Net Cash Flow",
            x=months,
            y=values,
            marker_color=colors,
            hovertemplate=(
                "%{x}<br>Net cash flow: %{y:$,.2f}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        hovermode="x",
        margin={"l": 30, "r": 30, "t": 30, "b": 30},
        showlegend=False,
    )
    figure.update_yaxes(
        title_text="Net cash flow ($)",
        tickprefix="$",
        separatethousands=True,
        zeroline=True,
        zerolinecolor="#6c757d",
        zerolinewidth=1,
    )
    return figure
