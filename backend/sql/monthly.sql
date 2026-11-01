-- Purchase month, including all placed statuses for the order series.
SELECT substr(purchase_date,1,7) AS month,
 SUM(CASE WHEN status='delivered' AND sales_eligible=1 THEN scoped_sales ELSE 0 END) AS sales,
 COUNT(*) AS placed_orders,
 COUNT(CASE WHEN status='delivered' AND sales_eligible=1 THEN 1 END) AS eligible_delivered_orders,
 AVG(CASE WHEN status='delivered' AND sales_eligible=1 THEN scoped_sales END) AS aov
FROM scoped GROUP BY month ORDER BY month;
