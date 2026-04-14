-- 範例：主 SQL（3+ 個 CTE），包含額外衍生欄位，方便測試合併輸出是否正常。
WITH policy_base AS (
    SELECT
        p.policy_id,
        p.customer_id,
        p.policy_number,
        p.status,
        p.premium
    FROM policies AS p
),
policy_enriched AS (
    SELECT
        policy_id,
        customer_id,
        policy_number,
        status,
        premium,
        CASE
            WHEN premium >= 15000 THEN 'HIGH'
            WHEN premium >= 10000 THEN 'MID'
            ELSE 'LOW'
        END AS premium_band,
        CASE
            WHEN status = 'ACTIVE' THEN 1
            ELSE 0
        END AS is_active
    FROM policy_base
),
policy_final AS (
    SELECT
        policy_id,
        customer_id,
        policy_number,
        status,
        premium,
        premium_band,
        is_active
    FROM policy_enriched
)
SELECT
    policy_id,
    customer_id,
    policy_number,
    status,
    premium,
    premium_band,
    is_active
FROM policy_final;

