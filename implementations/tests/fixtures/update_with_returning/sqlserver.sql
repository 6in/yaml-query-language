UPDATE customers
SET status = inactive
WHERE id = 1
RETURNING id, status
