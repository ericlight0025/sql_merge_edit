-- 範例：Join SQL（3 個 CTE），用來測試「多欄位 join 條件」（policy_id + customer_id）。
WITH policy_base AS (
    SELECT
        p.policy_id,
        p.customer_id
    FROM policies AS p
),
policy_key_calc(policy_id, customer_id, key_text) AS (
    SELECT
        policy_id,
        customer_id,
        CAST(policy_id AS TEXT) || '-' || CAST(customer_id AS TEXT) AS key_text
    FROM policy_base
),
policy_final AS (
    SELECT
        policy_id,
        customer_id,
        key_text
    FROM policy_key_calc
)
SELECT
    policy_id,
    customer_id,
    key_text
FROM policy_final;
