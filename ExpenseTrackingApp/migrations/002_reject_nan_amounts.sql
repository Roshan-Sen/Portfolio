\set ON_ERROR_STOP on

BEGIN;

UPDATE public.transactions
SET
    amount = 0.01,
    updated_at = current_timestamp
WHERE amount = 'NaN'::numeric
RETURNING id;

ALTER TABLE public.transactions
    DROP CONSTRAINT IF EXISTS transactions_amount_check;

ALTER TABLE public.transactions
    ADD CONSTRAINT transactions_amount_check
        CHECK (amount > 0 AND amount <> 'NaN'::numeric);

COMMIT;
