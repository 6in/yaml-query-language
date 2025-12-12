INSERT INTO test
(id, name)
VALUES (1, John)
ON DUPLICATE KEY UPDATE
  name = VALUES(name)
