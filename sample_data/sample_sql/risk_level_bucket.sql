-- 範例：Join SQL（3 個 CTE），將風險等級做分桶，測試 CASE 與多段 CTE 連結。
WITH risk_base AS (
    SELECT
        r.policy_id,
        MAX(r.risk_level) AS max_risk_level
    FROM risks AS r
    GROUP BY r.policy_id
),
risk_bucketed AS (
    SELECT
        policy_id,
        max_risk_level,
        CASE
            WHEN max_risk_level >= 4 THEN 'HIGH'
            WHEN max_risk_level >= 3 THEN 'MID'
            ELSE 'LOW'
        END AS risk_bucket
    FROM risk_base
),
risk_final AS (
    SELECT
        policy_id,
        risk_bucket
    FROM risk_bucketed
)
SELECT
    policy_id,
    risk_bucket
FROM risk_final;

