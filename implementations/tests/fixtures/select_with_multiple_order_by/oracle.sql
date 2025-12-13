SELECT
  c.id AS id
FROM customers c
ORDER BY c.status ASC, c.created_at DESC
