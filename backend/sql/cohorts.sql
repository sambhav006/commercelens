-- Cohorts intentionally ignore category and state. Dates select first-purchase cohorts.
-- First purchase always comes from full history; never redefine it with filters.
-- Only complete acquisition months contained in the selected range are eligible.
WITH RECURSIVE offsets(age) AS (
 SELECT 0 UNION ALL SELECT age+1 FROM offsets WHERE age<
 (CAST(strftime('%Y',:end) AS INT)-CAST(strftime('%Y',:dataset_start) AS INT))*12+
 CAST(strftime('%m',:end) AS INT)-CAST(strftime('%m',:dataset_start) AS INT)
), first_purchase AS (
 SELECT customer_unique_id,MIN(purchase_date) AS first_date FROM order_facts
 WHERE status='delivered' AND customer_unique_id IS NOT NULL GROUP BY customer_unique_id
), cohort_members AS (
 SELECT *,substr(first_date,1,7) AS cohort FROM first_purchase
 WHERE date(first_date,'start of month')>=:start
 AND date(first_date,'start of month')>=:dataset_start
 AND date(first_date,'start of month','+1 month','-1 day')<=:end
), sizes AS (
 SELECT cohort,COUNT(*) AS customers FROM cohort_members GROUP BY cohort
), activity AS (
 SELECT c.cohort,
 (CAST(strftime('%Y',o.purchase_date) AS INT)-CAST(substr(c.cohort,1,4) AS INT))*12+
 CAST(strftime('%m',o.purchase_date) AS INT)-CAST(substr(c.cohort,6,2) AS INT) AS age,
 COUNT(DISTINCT o.customer_unique_id) AS active
 FROM cohort_members c JOIN order_facts o ON c.customer_unique_id=o.customer_unique_id
 WHERE o.status='delivered' GROUP BY c.cohort,age
)
SELECT s.cohort,s.customers AS cohort_size,m.age,
 CASE WHEN date(s.cohort||'-01','+'||m.age||' months','+1 month','-1 day')<=:end
 THEN COALESCE(a.active,0) END AS active_customers,
 CASE WHEN date(s.cohort||'-01','+'||m.age||' months','+1 month','-1 day')<=:end
 THEN 1.0*COALESCE(a.active,0)/s.customers END AS retention
FROM sizes s CROSS JOIN offsets m LEFT JOIN activity a ON a.cohort=s.cohort AND a.age=m.age
ORDER BY s.cohort,m.age;
