# Expense Tracking App

A personal expense tracker backed by PostgreSQL. Transactions can be entered
through a local Streamlit interface, and cash-flow reports are generated as
self-contained Quarto HTML files.

## Prerequisites

- PostgreSQL with the migrations in `migrations/` applied.
- Quarto available on `PATH` for report generation.
- The pinned Python dependencies available in `analysis_env`.

Database connections use Psycopg's standard `PGHOST`, `PGPORT`, `PGUSER`,
`PGPASSWORD`, and `PGPASSFILE` settings. `PGDATABASE` defaults to
`expense_tracking_app`; credentials can also be stored in `.pgpass`.

## Run the GUI

```sh
make app
```

Alternatively:

```sh
analysis_env/bin/python -m streamlit run streamlit_app.py
```

The application opens locally with separate pages for adding transactions and
generating monthly, yearly, or custom-range reports. Generated reports are
written under `reports/output/` and can be downloaded from the app.

Reports contain personal financial data. The generated output directory and
local credential files are excluded from Git and should remain private.

## Tests

```sh
analysis_env/bin/python -m unittest discover -v
```

The PostgreSQL migration integration test starts a temporary database cluster
and may need to be run outside restricted containers that prohibit shared
memory allocation.
