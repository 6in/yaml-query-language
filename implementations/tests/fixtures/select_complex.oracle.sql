SELECT
  c.id AS customer_id,
  c.name AS customer_name,
  COUNT(o.id) AS order_count,
  SUM(o.amount) AS total_amount
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE c.status = 'active'
  AND ROWNUM <= 10
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 0
ORDER BY total_amount DESC
