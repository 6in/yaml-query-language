SELECT
  c.id AS id,
  c.name AS name
FROM customers c
ORDER BY c.id DESC
OFFSET ((#{page:1} - 1) * #{per_page:20}) ROWS
FETCH NEXT #{per_page:20} ROWS ONLY
