"""Local Streamlit launcher for the expense tracker."""

import streamlit as st

from expense_tracking.ui import render_add_transaction_page, render_report_page


st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💵",
    layout="centered",
)

navigation = st.navigation(
    [
        st.Page(
            render_add_transaction_page,
            title="Add Transaction",
            icon=":material/add_card:",
            default=True,
        ),
        st.Page(
            render_report_page,
            title="Generate Report",
            icon=":material/assessment:",
        ),
    ],
    position="sidebar",
)
navigation.run()
