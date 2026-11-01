, frequency AS (
 SELECT customer_unique_id,COUNT(*) AS purchases FROM scoped
 WHERE status='delivered' AND customer_unique_id IS NOT NULL GROUP BY customer_unique_id
)
SELECT CASE WHEN purchases>=4 THEN '4+' ELSE CAST(purchases AS TEXT) END AS purchases,
 COUNT(*) AS customers FROM frequency GROUP BY 1 ORDER BY 1;
