-- Sales and AOV share exactly the same delivered, complete-price order population.
SELECT COUNT(*) AS placed_orders,
 SUM(CASE WHEN status='delivered' AND sales_eligible=1 THEN scoped_sales END) AS sales,
 COUNT(CASE WHEN status='delivered' AND sales_eligible=1 THEN 1 END) AS eligible_delivered_orders,
 COUNT(CASE WHEN status='delivered' THEN 1 END) AS delivered_orders,
 AVG(CASE WHEN status='delivered' AND sales_eligible=1 THEN scoped_sales END) AS aov,
 COUNT(CASE WHEN status='canceled' THEN 1 END) AS canceled_orders,
 1.0*COUNT(CASE WHEN status='canceled' THEN 1 END)/NULLIF(COUNT(*),0) AS cancellation_rate,
 AVG(late) AS late_rate,COUNT(late) AS delivery_sample,
 COUNT(CASE WHEN late=1 THEN 1 END) AS late_orders,
 COUNT(DISTINCT CASE WHEN status='delivered' THEN customer_unique_id END) AS purchasing_customers,
 COUNT(CASE WHEN status='delivered' AND sales_eligible=0 THEN 1 END) AS excluded_sales_orders
FROM scoped;
