"""Streamlit transaction-entry page."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st

from expense_tracking.errors import ExpenseTrackingError, ValidationError
from expense_tracking.transactions import (
    ALLOWED_TRANSACTION_TYPES,
    Transaction,
    add_transaction,
    validate_amount,
)


TRANSACTION_TYPE_LABELS = {
    "expense": "Expense",
    "income": "Income",
    "investment": "Investment",
}


def parse_gui_amount(value: str) -> Decimal:
    """Parse a GUI amount without converting through a binary float."""

    if not isinstance(value, str) or not value.strip():
        raise ValidationError("amount must not be blank")
    try:
        amount = Decimal(value.strip())
    except InvalidOperation as error:
        raise ValidationError("amount must be a valid decimal number") from error
    return validate_amount(amount)


def render_add_transaction_page() -> None:
    """Render the transaction form and submit through the application service."""

    st.title("Add Transaction")
    st.caption("Record an expense, income payment, or investment.")

    last_inserted = st.session_state.pop("transaction_success", None)
    if last_inserted is not None:
        st.success(
            f"Added transaction #{last_inserted.id}: "
            f"{last_inserted.occurred_on.isoformat()} · "
            f"{TRANSACTION_TYPE_LABELS[last_inserted.transaction_type]} · "
            f"${last_inserted.amount:,.2f} · {last_inserted.description}"
        )

    form_version = st.session_state.get("transaction_form_version", 0)
    retained_date = st.session_state.get("transaction_date", date.today())
    retained_type = st.session_state.get(
        "transaction_type", ALLOWED_TRANSACTION_TYPES[0]
    )

    with st.form("add_transaction_form"):
        occurred_on = st.date_input(
            "Date",
            value=retained_date,
            key=f"transaction_date_{form_version}",
        )
        transaction_type = st.selectbox(
            "Type",
            options=ALLOWED_TRANSACTION_TYPES,
            index=ALLOWED_TRANSACTION_TYPES.index(retained_type),
            format_func=TRANSACTION_TYPE_LABELS.__getitem__,
            key=f"transaction_type_{form_version}",
        )
        amount_text = st.text_input(
            "Amount",
            placeholder="0.00",
            key=f"transaction_amount_{form_version}",
        )
        description = st.text_input(
            "Description",
            placeholder="What was this transaction for?",
            key=f"transaction_description_{form_version}",
        )
        submitted = st.form_submit_button(
            "Add transaction",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        transaction = Transaction(
            occurred_on=occurred_on,
            transaction_type=transaction_type,
            amount=parse_gui_amount(amount_text),
            description=description,
        )
        inserted = add_transaction(transaction)
    except ExpenseTrackingError as error:
        st.error(str(error))
        return
    except Exception:
        st.error("The transaction could not be added because of an unexpected error.")
        return

    st.session_state["transaction_success"] = inserted
    st.session_state["transaction_date"] = occurred_on
    st.session_state["transaction_type"] = transaction_type
    st.session_state["transaction_form_version"] = form_version + 1
    st.rerun()
