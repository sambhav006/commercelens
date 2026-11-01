-- One row per order. Never join item, payment and review detail together.
CREATE TABLE item_facts AS
SELECT i.order_id,i.order_item_id,i.product_id,i.price,i.freight_value,
       COALESCE(t.product_category_name_english,p.product_category_name,'Unknown') AS category
FROM items i LEFT JOIN products p ON i.product_id=p.product_id
LEFT JOIN translations t ON p.product_category_name=t.product_category_name;
CREATE INDEX ix_item_order ON item_facts(order_id);
CREATE INDEX ix_item_category ON item_facts(category,order_id);
CREATE TABLE order_facts AS
WITH item_totals AS (
 SELECT order_id,COUNT(*) AS item_count,SUM(price) AS item_sales,
        CASE WHEN COUNT(price)=COUNT(*) THEN 1 ELSE 0 END AS complete_prices
 FROM item_facts GROUP BY order_id
), payment_totals AS (
 SELECT order_id,SUM(payment_value) AS paid_value,COUNT(*) AS payment_count FROM payments GROUP BY order_id
), ranked_reviews AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY review_answer_timestamp DESC,review_id DESC) AS rn
 FROM reviews WHERE review_score IS NOT NULL
)
SELECT o.order_id,o.customer_id,c.customer_unique_id,COALESCE(c.customer_state,'Unknown') AS state,
 o.order_status AS status,date(o.order_purchase_timestamp) AS purchase_date,
 date(o.order_delivered_customer_date) AS delivered_date,date(o.order_estimated_delivery_date) AS estimated_date,
 COALESCE(i.item_count,0) AS item_count,i.item_sales,
 CASE WHEN i.complete_prices=1 THEN 1 ELSE 0 END AS sales_eligible,
 p.paid_value,COALESCE(p.payment_count,0) AS payment_count,r.review_score,
 CASE WHEN o.order_status='delivered' AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
      THEN CASE WHEN date(o.order_delivered_customer_date)>date(o.order_estimated_delivery_date) THEN 1 ELSE 0 END END AS late,
 CASE WHEN o.order_status='delivered' THEN julianday(date(o.order_delivered_customer_date))-julianday(date(o.order_purchase_timestamp)) END AS delivery_days
FROM orders o LEFT JOIN customers c ON o.customer_id=c.customer_id
LEFT JOIN item_totals i ON o.order_id=i.order_id
LEFT JOIN payment_totals p ON o.order_id=p.order_id
LEFT JOIN ranked_reviews r ON o.order_id=r.order_id AND r.rn=1;
CREATE UNIQUE INDEX pk_facts ON order_facts(order_id);
CREATE INDEX ix_facts_date ON order_facts(purchase_date,state,status);
