# Database migrations

These migrations create the PostgreSQL database and schema for the personal
expense tracking application. PostgreSQL becomes the source of truth after the
historical data is imported in a later phase.

## Prerequisites

- PostgreSQL and `psql` are installed.
- The PostgreSQL role used by `psql` can create databases.
- Connection settings are available through PostgreSQL's standard environment
  variables, command-line defaults, or `.pgpass`.
- `make` is available when using the convenience targets.

The migration files do not contain usernames, passwords, hosts, or ports.

## Running the migrations

From the project root, create the database and apply the schema:

```sh
make db-setup
```

The targets can also be run independently:

```sh
make db-create
make db-migrate
```

The defaults are:

| Make variable | Default value |
| --- | --- |
| `PSQL` | `psql` |
| `DATABASE_NAME` | `expense_tracking_app` |
| `MAINTENANCE_DB` | `postgres` |

Override a default on the command line when needed:

```sh
make db-setup DATABASE_NAME=expense_tracking_app MAINTENANCE_DB=postgres
```

Standard PostgreSQL connection variables continue to work:

```sh
PGHOST=localhost PGUSER=my_user make db-setup
```

Equivalent direct `psql` commands are:

```sh
psql -X -v ON_ERROR_STOP=1 \
  -v database_name=expense_tracking_app \
  --dbname=postgres \
  --file=migrations/000_create_database.sql

psql -X -v ON_ERROR_STOP=1 \
  --dbname=expense_tracking_app \
  --file=migrations/001_create_transactions.sql

psql -X -v ON_ERROR_STOP=1 \
  --dbname=expense_tracking_app \
  --file=migrations/002_reject_nan_amounts.sql
```

Migration `000` must run against an existing maintenance database because
PostgreSQL cannot create a database while connected to that same database.
Migration `001` then connects to the new application database. Migration `002`
repairs any existing `NaN` amounts and strengthens the amount constraint.

All migrations are safe to run more than once. Existing objects are retained.
PostgreSQL may print notices that an existing table or index was skipped.
Migration `002` drops and recreates its named constraint so a rerun restores the
intended definition without changing valid rows. `IF NOT EXISTS` does not
reconcile an incorrectly shaped existing object, so applied migration files
should remain unchanged. Put future schema changes in new, sequentially
numbered migration files.

## Transaction schema

`public.transactions` stores one row per transaction:

| Column | Type | Purpose |
| --- | --- | --- |
| `id` | `bigint` identity | Database-generated primary key |
| `occurred_on` | `date` | Calendar date of the transaction |
| `transaction_type` | `text` | `income`, `expense`, or `investment` |
| `amount` | `numeric(12,2)` | Positive monetary amount |
| `description` | `text` | Nonblank transaction description |
| `created_at` | `timestamp with time zone` | Row creation time |
| `updated_at` | `timestamp with time zone` | Most recent application update |

Amounts are stored as finite positive values. `transaction_type` determines
their meaning in reports. Migration `002` replaces any existing PostgreSQL
`NaN` amount with `$0.01` and updates that row's `updated_at` timestamp; the
affected transaction IDs are listed in the migration output. This repair is a
nominal substitute and does not recover the original amount. The application is
responsible for changing `updated_at` when a transaction is edited.

The schema enforces:

- A valid lowercase transaction type.
- A finite amount greater than zero; PostgreSQL `NaN` is explicitly rejected.
- A description containing at least one non-whitespace character.

Indexes support date-range queries and queries filtered by both transaction type
and date. Exact duplicate transaction details are allowed because repeated
transactions can be legitimate.

Reports, monthly totals, and net cash flow should be calculated from transaction
rows rather than stored separately. Categories, source-workbook metadata,
application roles, and historical data loading are intentionally deferred.

## Verification

After running the migrations, these commands can be used manually:

```sh
psql --dbname=postgres \
  --command="\l expense_tracking_app"

psql --dbname=expense_tracking_app \
  --command="\d+ public.transactions"
```

To verify the constraints, run test inserts inside a transaction that is always
rolled back:

```sql
BEGIN;

INSERT INTO public.transactions (
    occurred_on,
    transaction_type,
    amount,
    description
) VALUES (
    DATE '2026-07-26',
    'expense',
    12.50,
    'Constraint test'
);

ROLLBACK;
```

Invalid transaction types, `NaN`, amounts less than or equal to zero, amounts
outside `numeric(12,2)`, and blank descriptions should be rejected by
PostgreSQL.
