WITH
-- source: policy_main.sql  cte: policy_base,
policy_main__policy_base AS (
    SELECT
            p.policy_id,
            p.customer_id,
            p.policy_number,
            p.status,
            p.premium
        FROM policies AS p
),
-- source: policy_main.sql  cte: policy_final,
policy_main__policy_final AS (
    SELECT
            policy_id,
            customer_id,
            policy_number,
            status,
            premium
        FROM policy_main__policy_base
),
-- source: policy_main.sql  result,
policy_main__result AS (
    SELECT
        policy_id,
        customer_id,
        policy_number,
        status,
        premium
    FROM policy_main__policy_final
),
-- source: customer_profile.sql  cte: customer_base,
customer_profile__customer_base AS (
    SELECT
            c.customer_id,
            c.customer_name,
            c.city
        FROM customers AS c
),
-- source: customer_profile.sql  cte: customer_final,
customer_profile__customer_final AS (
    SELECT
            customer_id,
            customer_name,
            city
        FROM customer_profile__customer_base
),
-- source: customer_profile.sql  result,
customer_profile__result AS (
    SELECT
        customer_id,
        customer_name,
        city
    FROM customer_profile__customer_final
),
-- source: risk_summary.sql  cte: risk_base,
risk_summary__risk_base AS (
    SELECT
            r.policy_id,
            COUNT(*) AS risk_count,
            MAX(r.risk_level) AS highest_risk_level
        FROM risks AS r
        GROUP BY r.policy_id
),
-- source: risk_summary.sql  cte: risk_final,
risk_summary__risk_final AS (
    SELECT
            policy_id,
            risk_count,
            highest_risk_level
        FROM risk_summary__risk_base
),
-- source: risk_summary.sql  result,
risk_summary__result AS (
    SELECT
        policy_id,
        risk_count,
        highest_risk_level
    FROM risk_summary__risk_final
),
-- source: claim_summary.sql  cte: claim_base,
claim_summary__claim_base AS (
    SELECT
            c.policy_id,
            COUNT(*) AS claim_count,
            SUM(c.amount) AS total_claim_amount
        FROM claims AS c
        GROUP BY c.policy_id
),
-- source: claim_summary.sql  cte: claim_final,
claim_summary__claim_final AS (
    SELECT
            policy_id,
            claim_count,
            total_claim_amount
        FROM claim_summary__claim_base
),
-- source: claim_summary.sql  result,
claim_summary__result AS (
    SELECT
        policy_id,
        claim_count,
        total_claim_amount
    FROM claim_summary__claim_final
),
-- source: change_summary.sql  cte: change_base,
change_summary__change_base AS (
    SELECT
            pc.policy_id,
            COUNT(*) AS change_count,
            MAX(pc.change_date) AS latest_change_date
        FROM policy_changes AS pc
        GROUP BY pc.policy_id
),
-- source: change_summary.sql  cte: change_final,
change_summary__change_final AS (
    SELECT
            policy_id,
            change_count,
            latest_change_date
        FROM change_summary__change_base
),
-- source: change_summary.sql  result,
change_summary__result AS (
    SELECT
        policy_id,
        change_count,
        latest_change_date
    FROM change_summary__change_final
)
SELECT
    main_src.*,
    join_1.*,
    join_2.*,
    join_3.*,
    join_4.*
FROM policy_main__result AS main_src
LEFT JOIN customer_profile__result AS join_1 ON main_src.customer_id = join_1.customer_id
LEFT JOIN risk_summary__result AS join_2 ON main_src.policy_id = join_2.policy_id
LEFT JOIN claim_summary__result AS join_3 ON main_src.policy_id = join_3.policy_id
LEFT JOIN change_summary__result AS join_4 ON main_src.policy_id = join_4.policy_id;
