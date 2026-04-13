WITH claim_base AS (
    SELECT
        c.policy_id,
        COUNT(*) AS claim_count,
        SUM(c.amount) AS total_claim_amount
    FROM claims AS c
    GROUP BY c.policy_id
),
claim_final AS (
    SELECT
        policy_id,
        claim_count,
        total_claim_amount
    FROM claim_base
)
SELECT
    policy_id,
    claim_count,
    total_claim_amount
FROM claim_final;
