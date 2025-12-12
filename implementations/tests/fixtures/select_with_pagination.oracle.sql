SELECT
  c.id AS id,
  c.name AS name
FROM customers c
ORDER BY c.id DESC
SELECT c.id AS id, c.name AS name FROM (
  SELECT c.id AS id, c.name AS name, ROW_NUMBER() OVER (ORDER BY c.id DESC) AS rn
  FROM (SELECT
  c.id AS id,
  c.name AS name
FROM customers c
ORDER BY c.id DESC) subquery
) WHERE rn > ((#{page:1} - 1) * #{per_page:20}) AND rn <= (((#{page:1} - 1) * #{per_page:20}) + #{per_page:20})
