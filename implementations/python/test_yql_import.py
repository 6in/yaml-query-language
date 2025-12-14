#!/usr/bin/env python3
"""Test script to import YQL modules for pyodide-pack."""

from yql import parse, generate_sql, Dialect

# Test import
yql_content = """
query:
  select:
    - id: c.id
    - name: c.name
  from: { c: customers }
  limit: 10
"""

query = parse(yql_content)
sql = generate_sql(query, Dialect.POSTGRESQL)
print(f"Generated SQL: {sql}")


