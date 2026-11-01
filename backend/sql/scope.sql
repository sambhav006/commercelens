-- Shared parameterized scope. Category selects matching orders for order metrics;
-- scoped_sales includes ONLY matching item prices. Full order completeness is required.
WITH scoped AS (
 SELECT o.*,
   CASE WHEN :category='' THEN o.item_sales ELSE
     (SELECT SUM(i.price) FROM item_facts i WHERE i.order_id=o.order_id AND i.category=:category)
   END AS scoped_sales
 FROM order_facts o
 WHERE purchase_date BETWEEN :start AND :end
   AND (:state='' OR state=:state)
   AND (:category='' OR EXISTS(SELECT 1 FROM item_facts i WHERE i.order_id=o.order_id AND i.category=:category))
)
