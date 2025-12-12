DELETE FROM customers
WHERE id = 1
RETURNING id, name
