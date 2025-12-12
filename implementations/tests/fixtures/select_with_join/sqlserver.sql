SELECT
  c.id AS customer_id,
  o.id AS order_id
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
