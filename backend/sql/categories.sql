-- Items are attributed to their own category. Order counts are NOT additive across categories.
, ranked AS (
 SELECT i.category,SUM(i.price) AS sales,COUNT(DISTINCT o.order_id) AS orders,COUNT(*) AS items
 FROM scoped o JOIN item_facts i ON o.order_id=i.order_id
 WHERE o.status='delivered' AND o.sales_eligible=1 AND (:category='' OR i.category=:category)
 GROUP BY i.category
)
SELECT *,sales/NULLIF(SUM(sales) OVER(),0) AS sales_share,
 DENSE_RANK() OVER(ORDER BY sales DESC) AS sales_rank FROM ranked ORDER BY sales DESC,category;
