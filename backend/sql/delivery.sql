-- Calendar days; missing or impossible dates remain excluded from denominators.
SELECT substr(purchase_date,1,7) AS month,AVG(delivery_days) AS average_delivery_days,
 COUNT(delivery_days) AS duration_sample,AVG(late) AS late_rate,COUNT(late) AS delivery_sample
FROM scoped WHERE status='delivered' GROUP BY month ORDER BY month;
