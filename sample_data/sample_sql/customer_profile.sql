WITH customer_base AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.city
    FROM customers AS c
),
customer_final AS (
    SELECT
        customer_id,
        customer_name,
        city
    FROM customer_base
)
SELECT
    customer_id,
    customer_name,
    city
FROM customer_final;
