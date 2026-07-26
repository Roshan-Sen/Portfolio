\set ON_ERROR_STOP on

-- One-time historical transaction import.
--
-- Run the curation workflow first:
--   analysis_env/bin/python data_curation/curate_transactions.py
--
-- Then run this script from the repository root so the client-side \copy path
-- resolves correctly:
--   psql -X -v ON_ERROR_STOP=1 \
--     --dbname=expense_tracking_app \
--     --file=data_curation/import_transactions.sql
--
-- This import intentionally aborts unless public.transactions is empty. The
-- curated history contains legitimate duplicate transaction details, so an
-- empty-table guard is safer than attempting to deduplicate repeated imports.

BEGIN;

LOCK TABLE public.transactions IN EXCLUSIVE MODE;

DO $$
DECLARE
    existing_count bigint;
BEGIN
    SELECT count(*)
    INTO existing_count
    FROM public.transactions;

    IF existing_count <> 0 THEN
        RAISE EXCEPTION
            'Historical import requires an empty public.transactions table; found % rows.',
            existing_count;
    END IF;
END
$$;

CREATE TEMPORARY TABLE historical_transactions_import (
    import_row bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_on date NOT NULL,
    transaction_type text NOT NULL,
    amount numeric(12, 2) NOT NULL,
    description text NOT NULL,

    CONSTRAINT historical_transactions_import_type_check
        CHECK (transaction_type IN ('income', 'expense', 'investment')),
    CONSTRAINT historical_transactions_import_amount_check
        CHECK (amount > 0),
    CONSTRAINT historical_transactions_import_description_check
        CHECK (btrim(description) <> '')
) ON COMMIT DROP;

\copy historical_transactions_import (occurred_on, transaction_type, amount, description) FROM 'data_curation/output/curated_transactions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

DO $$
DECLARE
    total_count bigint;
    income_count bigint;
    expense_count bigint;
    investment_count bigint;
    income_total numeric;
    expense_total numeric;
    investment_total numeric;
BEGIN
    SELECT
        count(*),
        count(*) FILTER (WHERE transaction_type = 'income'),
        count(*) FILTER (WHERE transaction_type = 'expense'),
        count(*) FILTER (WHERE transaction_type = 'investment'),
        coalesce(sum(amount) FILTER (WHERE transaction_type = 'income'), 0),
        coalesce(sum(amount) FILTER (WHERE transaction_type = 'expense'), 0),
        coalesce(sum(amount) FILTER (WHERE transaction_type = 'investment'), 0)
    INTO
        total_count,
        income_count,
        expense_count,
        investment_count,
        income_total,
        expense_total,
        investment_total
    FROM historical_transactions_import;

    IF total_count <> 452 THEN
        RAISE EXCEPTION
            'Expected 452 staged transactions; found %.',
            total_count;
    END IF;

    IF (income_count, expense_count, investment_count) <> (30, 340, 82) THEN
        RAISE EXCEPTION
            'Unexpected staged counts: income %, expense %, investment %.',
            income_count,
            expense_count,
            investment_count;
    END IF;

    IF (income_total, expense_total, investment_total)
        <> (78632.30, 10696.35, 66824.56)
    THEN
        RAISE EXCEPTION
            'Unexpected staged totals: income %, expense %, investment %.',
            income_total,
            expense_total,
            investment_total;
    END IF;
END
$$;

INSERT INTO public.transactions (
    occurred_on,
    transaction_type,
    amount,
    description
)
SELECT
    occurred_on,
    transaction_type,
    amount,
    description
FROM historical_transactions_import
ORDER BY import_row;

DO $$
DECLARE
    total_count bigint;
    income_count bigint;
    expense_count bigint;
    investment_count bigint;
    income_total numeric;
    expense_total numeric;
    investment_total numeric;
BEGIN
    SELECT
        count(*),
        count(*) FILTER (WHERE transaction_type = 'income'),
        count(*) FILTER (WHERE transaction_type = 'expense'),
        count(*) FILTER (WHERE transaction_type = 'investment'),
        coalesce(sum(amount) FILTER (WHERE transaction_type = 'income'), 0),
        coalesce(sum(amount) FILTER (WHERE transaction_type = 'expense'), 0),
        coalesce(sum(amount) FILTER (WHERE transaction_type = 'investment'), 0)
    INTO
        total_count,
        income_count,
        expense_count,
        investment_count,
        income_total,
        expense_total,
        investment_total
    FROM public.transactions;

    IF total_count <> 452
        OR (income_count, expense_count, investment_count) <> (30, 340, 82)
        OR (income_total, expense_total, investment_total)
            <> (78632.30, 10696.35, 66824.56)
    THEN
        RAISE EXCEPTION
            'Post-import validation failed: total rows %, counts (%, %, %), totals (%, %, %).',
            total_count,
            income_count,
            expense_count,
            investment_count,
            income_total,
            expense_total,
            investment_total;
    END IF;
END
$$;

COMMIT;

SELECT
    transaction_type,
    count(*) AS transaction_count,
    sum(amount) AS total_amount
FROM public.transactions
GROUP BY transaction_type
ORDER BY transaction_type;
