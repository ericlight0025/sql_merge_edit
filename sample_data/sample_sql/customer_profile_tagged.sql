-- 範例：Join SQL（4 個 CTE），包含：
-- 1) CTE 欄位清單寫法（name(col1, col2) AS (...)）
-- 2) 註解與字串中出現 CTE 名稱，用來驗證合併時不會誤替換字串/註解內容
WITH customer_base AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.city
    FROM customers AS c
),
city_group_map(city, city_group) AS (
    SELECT
        city,
        CASE
            WHEN city = 'Taipei' THEN 'NORTH'
            WHEN city = 'Taichung' THEN 'CENTRAL'
            ELSE 'SOUTH'
        END AS city_group
    FROM customer_base
    GROUP BY city
),
customer_joined AS (
    SELECT
        cb.customer_id,
        cb.customer_name,
        cb.city,
        cg.city_group,
        -- 這裡故意放字串 'customer_base'，合併時不應把字串內容替換掉
        'customer_base' AS note_text
    FROM customer_base AS cb
    LEFT JOIN city_group_map AS cg
        ON cb.city = cg.city
),
customer_final AS (
    SELECT
        customer_id,
        customer_name,
        city,
        city_group
    FROM customer_joined
)
SELECT
    customer_id,
    customer_name,
    city,
    city_group
FROM customer_final;

