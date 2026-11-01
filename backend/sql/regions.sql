SELECT state,
 SUM(CASE WHEN status='delivered' AND sales_eligible=1 THEN scoped_sales ELSE 0 END) AS sales,
 COUNT(*) AS placed_orders,COUNT(CASE WHEN status='delivered' AND sales_eligible=1 THEN 1 END) AS sales_orders,
 AVG(late) AS late_rate,COUNT(late) AS delivery_sample,
 COUNT(CASE WHEN late=1 THEN 1 END) AS late_orders,
 AVG(delivery_days) AS average_delivery_days,COUNT(delivery_days) AS duration_sample
FROM scoped GROUP BY state ORDER BY sales DESC,state;
