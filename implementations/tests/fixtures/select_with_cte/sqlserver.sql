WITH active_customers AS (
  SELECT
    c.id AS id,
    c.name AS name
  FROM customers c
  WHERE c.status = 'active'
)
SELECT
  ac.id AS id,
  ac.name AS name
FROM active_customers ac
