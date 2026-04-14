WITH RECURSIVE
-- source: policy_main_enriched.sql  cte: policy_base,
policy_main_enriched__policy_base AS (
    SELECT
            p.policy_id,
            p.customer_id,
            p.policy_number,
            p.status,
            p.premium
        FROM policies AS p
),
-- source: policy_main_enriched.sql  cte: policy_enriched,
policy_main_enriched__policy_enriched AS (
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
        FROM policy_main_enriched__policy_base
),
-- source: policy_main_enriched.sql  cte: policy_final,
policy_main_enriched__policy_final AS (
    SELECT
            policy_id,
            customer_id,
            policy_number,
            status,
            premium,
            premium_band,
            is_active
        FROM policy_main_enriched__policy_enriched
),
-- source: policy_main_enriched.sql  result,
policy_main_enriched__result AS (
    SELECT
        policy_id,
        customer_id,
        policy_number,
        status,
        premium,
        premium_band,
        is_active
    FROM policy_main_enriched__policy_final
),
-- source: customer_profile_tagged.sql  cte: customer_base,
customer_profile_tagged__customer_base AS (
    SELECT
            c.customer_id,
            c.customer_name,
            c.city
        FROM customers AS c
),
-- source: customer_profile_tagged.sql  cte: city_group_map,
customer_profile_tagged__city_group_map(city, city_group) AS (
    SELECT
            city,
            CASE
                WHEN city = 'Taipei' THEN 'NORTH'
                WHEN city = 'Taichung' THEN 'CENTRAL'
                ELSE 'SOUTH'
            END AS city_group
        FROM customer_profile_tagged__customer_base
        GROUP BY city
),
-- source: customer_profile_tagged.sql  cte: customer_joined,
customer_profile_tagged__customer_joined AS (
    SELECT
            cb.customer_id,
            cb.customer_name,
            cb.city,
            cg.city_group,
            -- 這裡故意放字串 'customer_base'，合併時不應把字串內容替換掉
            'customer_base' AS note_text
        FROM customer_profile_tagged__customer_base AS cb
        LEFT JOIN customer_profile_tagged__city_group_map AS cg
            ON cb.city = cg.city
),
-- source: customer_profile_tagged.sql  cte: customer_final,
customer_profile_tagged__customer_final AS (
    SELECT
            customer_id,
            customer_name,
            city,
            city_group
        FROM customer_profile_tagged__customer_joined
),
-- source: customer_profile_tagged.sql  result,
customer_profile_tagged__result AS (
    SELECT
        customer_id,
        customer_name,
        city,
        city_group
    FROM customer_profile_tagged__customer_final
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
),
-- source: policy_sequence_recursive.sql  cte: seq,
policy_sequence_recursive__seq(n) AS (
    SELECT 1
        UNION ALL
        SELECT n + 1
        FROM policy_sequence_recursive__seq
        WHERE n < 3
),
-- source: policy_sequence_recursive.sql  cte: policy_rank,
policy_sequence_recursive__policy_rank AS (
    SELECT
            p.policy_id,
            p.customer_id,
            ROW_NUMBER() OVER (ORDER BY p.policy_id) AS n
        FROM policies AS p
),
-- source: policy_sequence_recursive.sql  cte: policy_seq,
policy_sequence_recursive__policy_seq AS (
    SELECT
            pr.policy_id,
            pr.customer_id,
            pr.n AS seq_no
        FROM policy_sequence_recursive__policy_rank AS pr
        INNER JOIN policy_sequence_recursive__seq AS s
            ON s.n = pr.n
),
-- source: policy_sequence_recursive.sql  cte: policy_final,
policy_sequence_recursive__policy_final AS (
    SELECT
            policy_id,
            customer_id,
            seq_no
        FROM policy_sequence_recursive__policy_seq
),
-- source: policy_sequence_recursive.sql  result,
policy_sequence_recursive__result AS (
    SELECT
        policy_id,
        customer_id,
        seq_no
    FROM policy_sequence_recursive__policy_final
),
-- source: policy_customer_key.sql  cte: policy_base,
policy_customer_key__policy_base AS (
    SELECT
            p.policy_id,
            p.customer_id
        FROM policies AS p
),
-- source: policy_customer_key.sql  cte: policy_key_calc,
policy_customer_key__policy_key_calc(policy_id, customer_id, key_text) AS (
    SELECT
            policy_id,
            customer_id,
            CAST(policy_id AS TEXT) || '-' || CAST(customer_id AS TEXT) AS key_text
        FROM policy_customer_key__policy_base
),
-- source: policy_customer_key.sql  cte: policy_final,
policy_customer_key__policy_final AS (
    SELECT
            policy_id,
            customer_id,
            key_text
        FROM policy_customer_key__policy_key_calc
),
-- source: policy_customer_key.sql  result,
policy_customer_key__result AS (
    SELECT
        policy_id,
        customer_id,
        key_text
    FROM policy_customer_key__policy_final
),
-- source: claim_recent_activity.sql  cte: params,
claim_recent_activity__params(anchor_date) AS (
    -- anchor_date 用固定值，避免測試因「今天日期」而不穩定
        SELECT '2026-04-01' AS anchor_date
),
-- source: claim_recent_activity.sql  cte: claim_recent,
claim_recent_activity__claim_recent AS (
    SELECT
            c.policy_id,
            c.amount,
            c.claim_date
        FROM claims AS c
        CROSS JOIN claim_recent_activity__params AS p
        WHERE
            julianday(p.anchor_date) - julianday(c.claim_date) BETWEEN 0 AND 60
),
-- source: claim_recent_activity.sql  cte: claim_agg,
claim_recent_activity__claim_agg AS (
    SELECT
            policy_id,
            MAX(claim_date) AS last_claim_date,
            SUM(amount) AS recent_claim_amount_total
        FROM claim_recent_activity__claim_recent
        GROUP BY policy_id
),
-- source: claim_recent_activity.sql  cte: claim_final,
claim_recent_activity__claim_final AS (
    SELECT
            policy_id,
            last_claim_date,
            recent_claim_amount_total
        FROM claim_recent_activity__claim_agg
),
-- source: claim_recent_activity.sql  result,
claim_recent_activity__result AS (
    SELECT
        policy_id,
        last_claim_date,
        recent_claim_amount_total
    FROM claim_recent_activity__claim_final
),
-- source: risk_level_bucket.sql  cte: risk_base,
risk_level_bucket__risk_base AS (
    SELECT
            r.policy_id,
            MAX(r.risk_level) AS max_risk_level
        FROM risks AS r
        GROUP BY r.policy_id
),
-- source: risk_level_bucket.sql  cte: risk_bucketed,
risk_level_bucket__risk_bucketed AS (
    SELECT
            policy_id,
            max_risk_level,
            CASE
                WHEN max_risk_level >= 4 THEN 'HIGH'
                WHEN max_risk_level >= 3 THEN 'MID'
                ELSE 'LOW'
            END AS risk_bucket
        FROM risk_level_bucket__risk_base
),
-- source: risk_level_bucket.sql  cte: risk_final,
risk_level_bucket__risk_final AS (
    SELECT
            policy_id,
            risk_bucket
        FROM risk_level_bucket__risk_bucketed
),
-- source: risk_level_bucket.sql  result,
risk_level_bucket__result AS (
    SELECT
        policy_id,
        risk_bucket
    FROM risk_level_bucket__risk_final
)
SELECT
    main_src.*,
    join_1.*,
    join_2.*,
    join_3.*,
    join_4.*,
    join_5.*,
    join_6.*,
    join_7.*,
    join_8.*
FROM policy_main_enriched__result AS main_src
LEFT JOIN customer_profile_tagged__result AS join_1 ON main_src.customer_id = join_1.customer_id
LEFT JOIN risk_summary__result AS join_2 ON main_src.policy_id = join_2.policy_id
LEFT JOIN claim_summary__result AS join_3 ON main_src.policy_id = join_3.policy_id
LEFT JOIN change_summary__result AS join_4 ON main_src.policy_id = join_4.policy_id
LEFT JOIN policy_sequence_recursive__result AS join_5 ON main_src.policy_id = join_5.policy_id
LEFT JOIN policy_customer_key__result AS join_6 ON main_src.policy_id = join_6.policy_id AND main_src.customer_id = join_6.customer_id
LEFT JOIN claim_recent_activity__result AS join_7 ON main_src.policy_id = join_7.policy_id
LEFT JOIN risk_level_bucket__result AS join_8 ON main_src.policy_id = join_8.policy_id;
