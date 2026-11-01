-- Repeat means >=2 delivered orders WITHIN the active date/state/category scope.
, frequency AS (
 SELECT customer_unique_id,COUNT(*) AS purchases FROM scoped
 WHERE status='delivered' AND customer_unique_id IS NOT NULL GROUP BY customer_unique_id
)
SELECT COUNT(*) AS customers,COUNT(CASE WHEN purchases>=2 THEN 1 END) AS repeat_customers,
 1.0*COUNT(CASE WHEN purchases>=2 THEN 1 END)/NULLIF(COUNT(*),0) AS repeat_rate,
 AVG(purchases) AS orders_per_customer FROM frequency;
