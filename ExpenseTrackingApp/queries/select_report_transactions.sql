SELECT
    id,
    occurred_on,
    transaction_type,
    amount,
    description
FROM public.transactions
WHERE occurred_on >= %(start_date)s
  AND occurred_on < %(end_date_exclusive)s
ORDER BY
    occurred_on,
    id;
