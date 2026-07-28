"""Plotly chart builders for cash-flow reports."""

from __future__ import annotations

from plotly import graph_objects as go
from plotly.subplots import make_subplots

from reporting.cash_flow import CashFlowReport


INCOME_COLOR = "#198754"
EXPENSE_COLOR = "#dc3545"
INVESTMENT_COLOR = "#0d6efd"
POSITIVE_NET_COLOR = "#198754"
NEGATIVE_NET_COLOR = "#dc3545"


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


def create_monthly_activity_chart(report: CashFlowReport) -> go.Figure:
    months = [summary.month.strftime("%b %Y") for summary in report.monthly]
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Bar(
            name="Income",
            x=months,
            y=[float(summary.income) for summary in report.monthly],
            marker_color=INCOME_COLOR,
            hovertemplate="%{x}<br>Income: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Bar(
            name="Expenses",
            x=months,
            y=[float(summary.expenses) for summary in report.monthly],
            marker_color=EXPENSE_COLOR,
            hovertemplate="%{x}<br>Expenses: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Bar(
            name="Investments",
            x=months,
            y=[float(summary.investments) for summary in report.monthly],
            marker_color=INVESTMENT_COLOR,
            hovertemplate="%{x}<br>Investments: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            name="Net Cash Flow",
            x=months,
            y=[float(summary.net_cash_flow) for summary in report.monthly],
            mode="lines+markers",
            line={"color": "#212529", "width": 3},
            marker={"size": 8},
            hovertemplate="%{x}<br>Net cash flow: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=True,
    )
    figure.update_layout(
        barmode="group",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0},
        margin={"l": 30, "r": 30, "t": 45, "b": 30},
    )
    figure.update_yaxes(
        title_text="Category totals ($)",
        tickprefix="$",
        separatethousands=True,
        secondary_y=False,
    )
    figure.update_yaxes(
        title_text="Net cash flow ($)",
        tickprefix="$",
        separatethousands=True,
        zeroline=True,
        zerolinecolor="#6c757d",
        secondary_y=True,
    )
    return figure
