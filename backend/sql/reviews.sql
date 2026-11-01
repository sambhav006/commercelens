-- One latest valid answered review per order. Association, not causation.
SELECT CASE WHEN late=1 THEN 'Late' WHEN late=0 THEN 'On time' ELSE 'Unknown dates' END AS delivery_status,
 AVG(review_score) AS average_review,COUNT(review_score) AS reviewed_orders,COUNT(*) AS delivered_orders
FROM scoped WHERE status='delivered' GROUP BY 1 ORDER BY 1;
