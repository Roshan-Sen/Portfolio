INSERT INTO public.transactions (
    occurred_on,
    transaction_type,
    amount,
    description
)
VALUES (
    %(occurred_on)s,
    %(transaction_type)s,
    %(amount)s,
    %(description)s
)
RETURNING
    id,
    occurred_on,
    transaction_type,
    amount,
    description,
    created_at;
