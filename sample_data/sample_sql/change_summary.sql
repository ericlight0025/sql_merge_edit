WITH change_base AS (
    SELECT
        pc.policy_id,
        COUNT(*) AS change_count,
        MAX(pc.change_date) AS latest_change_date
    FROM policy_changes AS pc
    GROUP BY pc.policy_id
),
change_final AS (
    SELECT
        policy_id,
        change_count,
        latest_change_date
    FROM change_base
)
SELECT
    policy_id,
    change_count,
    latest_change_date
FROM change_final;
