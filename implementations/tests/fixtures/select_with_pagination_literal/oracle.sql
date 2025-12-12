SELECT
  c.id AS id
FROM customers c
ORDER BY c.id ASC
SELECT c.id AS id FROM (
  SELECT c.id AS id, ROW_NUMBER() OVER (ORDER BY c.id ASC) AS rn
  FROM (SELECT
  c.id AS id
FROM customers c
ORDER BY c.id ASC) subquery
) WHERE rn > 20 AND rn <= (20 + 20)
