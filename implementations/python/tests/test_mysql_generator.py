"""Tests for MySQL SQL Generator."""

import pytest

from yql import parse, generate_sql, Dialect


class TestMySQLGenerateBasic:
    """Basic MySQL SQL generation tests."""
    
    def test_generate_simple_select(self):
        """Test generating simple SELECT for MySQL."""
        yql = """
query:
  select:
    - id: c.id
    - name: c.name
  from:
    c: customers
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.MYSQL)
        
        assert "SELECT" in sql
        assert "c.id AS id" in sql
        assert "c.name AS name" in sql
        assert "FROM customers c" in sql


class TestMySQLGenerateLimitOffset:
    """MySQL LIMIT/OFFSET tests."""
    
    def test_generate_limit(self):
        """Test generating LIMIT for MySQL."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  limit: 10
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.MYSQL)
        
        assert "LIMIT 10" in sql
    
    def test_generate_limit_offset(self):
        """Test generating LIMIT and OFFSET for MySQL."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  limit: 10
  offset: 20
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.MYSQL)
        
        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql


class TestMySQLGenerateJoin:
    """MySQL JOIN tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN for MySQL."""
        yql = """
query:
  select:
    - customer_id: c.id
    - order_id: o.id
  from:
    c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.MYSQL)
        
        assert "INNER JOIN orders o ON c.id = o.customer_id" in sql

