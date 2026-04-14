-- 範例：Join SQL（3+ 個 CTE），包含參數 CTE 與日期運算，用來測試較複雜的 CTE 組合。
WITH params(anchor_date) AS (
    -- anchor_date 用固定值，避免測試因「今天日期」而不穩定
    SELECT '2026-04-01' AS anchor_date
),
claim_recent AS (
    SELECT
        c.policy_id,
        c.amount,
        c.claim_date
    FROM claims AS c
    CROSS JOIN params AS p
    WHERE
        julianday(p.anchor_date) - julianday(c.claim_date) BETWEEN 0 AND 60
),
claim_agg AS (
    SELECT
        policy_id,
        MAX(claim_date) AS last_claim_date,
        SUM(amount) AS recent_claim_amount_total
    FROM claim_recent
    GROUP BY policy_id
),
claim_final AS (
    SELECT
        policy_id,
        last_claim_date,
        recent_claim_amount_total
    FROM claim_agg
)
SELECT
    policy_id,
    last_claim_date,
    recent_claim_amount_total
FROM claim_final;

