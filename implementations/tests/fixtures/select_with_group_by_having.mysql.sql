SELECT
  o.customer_id AS customer_id,
  COUNT(*) AS order_count
FROM orders o
GROUP BY o.customer_id
HAVING COUNT(*) > 5
