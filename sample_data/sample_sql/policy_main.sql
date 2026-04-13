WITH policy_base AS (
    SELECT
        p.policy_id,
        p.customer_id,
        p.policy_number,
        p.status,
        p.premium
    FROM policies AS p
),
policy_final AS (
    SELECT
        policy_id,
        customer_id,
        policy_number,
        status,
        premium
    FROM policy_base
)
SELECT
    policy_id,
    customer_id,
    policy_number,
    status,
    premium
FROM policy_final;
