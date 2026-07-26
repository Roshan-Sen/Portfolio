\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS public.transactions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_on date NOT NULL,
    transaction_type text NOT NULL,
    amount numeric(12, 2) NOT NULL,
    description text NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT current_timestamp,
    updated_at timestamp with time zone NOT NULL DEFAULT current_timestamp,

    CONSTRAINT transactions_type_check
        CHECK (transaction_type IN ('income', 'expense', 'investment')),
    CONSTRAINT transactions_amount_check
        CHECK (amount > 0),
    CONSTRAINT transactions_description_check
        CHECK (btrim(description) <> '')
);

CREATE INDEX IF NOT EXISTS transactions_occurred_on_idx
    ON public.transactions (occurred_on);

CREATE INDEX IF NOT EXISTS transactions_type_occurred_on_idx
    ON public.transactions (transaction_type, occurred_on);
