INSERT INTO test
(id, name)
VALUES (1, John)
ON CONFLICT (id)
DO UPDATE SET
  name = EXCLUDED.name
