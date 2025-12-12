MERGE test AS target
USING (SELECT
  1 AS id,
  John AS name
FROM dual d) AS source
ON (target.id = source.id)
WHEN MATCHED THEN
  UPDATE SET
    name = source.name
WHEN NOT MATCHED THEN
  INSERT (id, name)
  VALUES (source.id, source.name);
