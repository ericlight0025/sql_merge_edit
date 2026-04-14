-- 範例：WITH RECURSIVE（4+ 個 CTE），用來測試合併後是否會正確輸出 WITH RECURSIVE。
WITH RECURSIVE seq(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1
    FROM seq
    WHERE n < 3
),
policy_rank AS (
    SELECT
        p.policy_id,
        p.customer_id,
        ROW_NUMBER() OVER (ORDER BY p.policy_id) AS n
    FROM policies AS p
),
policy_seq AS (
    SELECT
        pr.policy_id,
        pr.customer_id,
        pr.n AS seq_no
    FROM policy_rank AS pr
    INNER JOIN seq AS s
        ON s.n = pr.n
),
policy_final AS (
    SELECT
        policy_id,
        customer_id,
        seq_no
    FROM policy_seq
)
SELECT
    policy_id,
    customer_id,
    seq_no
FROM policy_final;

