WITH
policy_main__policy_base AS (
    SELECT
            p.policy_id,
            p.customer_id,
            p.policy_number,
            p.status,
            p.premium
        FROM policies AS p
),
policy_main__policy_final AS (
    SELECT
            policy_id,
            customer_id,
            policy_number,
            status,
            premium
        FROM policy_main__policy_base
),
policy_main__result AS (
    SELECT
        policy_id,
        customer_id,
        policy_number,
        status,
        premium
    FROM policy_main__policy_final
),
change_summary__change_base AS (
    SELECT
            pc.policy_id,
            COUNT(*) AS change_count,
            MAX(pc.change_date) AS latest_change_date
        FROM policy_changes AS pc
        GROUP BY pc.policy_id
),
change_summary__change_final AS (
    SELECT
            policy_id,
            change_count,
            latest_change_date
        FROM change_summary__change_base
),
change_summary__result AS (
    SELECT
        policy_id,
        change_count,
        latest_change_date
    FROM change_summary__change_final
),
customer_profile__customer_base AS (
    SELECT
            c.customer_id,
            c.customer_name,
            c.city
        FROM customers AS c
),
customer_profile__customer_final AS (
    SELECT
            customer_id,
            customer_name,
            city
        FROM customer_profile__customer_base
),
customer_profile__result AS (
    SELECT
        customer_id,
        customer_name,
        city
    FROM customer_profile__customer_final
),
risk_summary__risk_base AS (
    SELECT
            r.policy_id,
            COUNT(*) AS risk_count,
            MAX(r.risk_level) AS highest_risk_level
        FROM risks AS r
        GROUP BY r.policy_id
),
risk_summary__risk_final AS (
    SELECT
            policy_id,
            risk_count,
            highest_risk_level
        FROM risk_summary__risk_base
),
risk_summary__result AS (
    SELECT
        policy_id,
        risk_count,
        highest_risk_level
    FROM risk_summary__risk_final
)
SELECT
    join_1.policy_id,
    join_1.change_count,
    join_1.latest_change_date,
    join_2.customer_id,
    join_2.customer_name,
    join_2.city,
    join_3.policy_id,
    join_3.risk_count,
    join_3.highest_risk_level,
    main_src.policy_id,
    main_src.customer_id,
    main_src.policy_number,
    main_src.status,
    main_src.premium
FROM policy_main__result AS main_src
LEFT JOIN change_summary__result AS join_1 ON main_src.policy_id = join_1.policy_id
LEFT JOIN customer_profile__result AS join_2 ON main_src.customer_id = join_2.customer_id
LEFT JOIN risk_summary__result AS join_3 ON main_src.policy_id = join_3.policy_id;
