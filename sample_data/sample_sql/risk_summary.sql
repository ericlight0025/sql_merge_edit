WITH risk_base AS (
    SELECT
        r.policy_id,
        COUNT(*) AS risk_count,
        MAX(r.risk_level) AS highest_risk_level
    FROM risks AS r
    GROUP BY r.policy_id
),
risk_final AS (
    SELECT
        policy_id,
        risk_count,
        highest_risk_level
    FROM risk_base
)
SELECT
    policy_id,
    risk_count,
    highest_risk_level
FROM risk_final;
