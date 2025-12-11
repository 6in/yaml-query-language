"""Tests for SQL Server SQL Generator."""

import pytest

from yql import parse, generate_sql, Dialect


class TestSQLServerGenerateBasic:
    """Basic SQL Server SQL generation tests."""
    
    def test_generate_simple_select(self):
        """Test generating simple SELECT for SQL Server."""
        yql = """
query:
  select:
    - id: c.id
    - name: c.name
  from:
    c: customers
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "SELECT" in sql
        assert "c.id AS id" in sql
        assert "c.name AS name" in sql
        assert "FROM customers c" in sql


class TestSQLServerGenerateTop:
    """SQL Server TOP tests."""
    
    def test_generate_top(self):
        """Test generating TOP for SQL Server (LIMIT without OFFSET)."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  limit: 10
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "SELECT TOP 10" in sql
        assert "OFFSET" not in sql


class TestSQLServerGenerateOffsetFetch:
    """SQL Server OFFSET-FETCH tests."""
    
    def test_generate_offset_fetch(self):
        """Test generating OFFSET-FETCH for SQL Server."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  order_by:
    - field: c.id
      direction: ASC
  limit: 10
  offset: 20
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "OFFSET 20 ROWS" in sql
        assert "FETCH NEXT 10 ROWS ONLY" in sql
        assert "TOP" not in sql
    
    def test_generate_offset_fetch_requires_order_by(self):
        """Test that OFFSET-FETCH adds ORDER BY if not specified."""
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
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Should have ORDER BY (SELECT NULL) for SQL Server
        assert "ORDER BY" in sql
        assert "OFFSET 20 ROWS" in sql


class TestSQLServerGeneratePagination:
    """SQL Server pagination tests."""
    
    def test_generate_pagination(self):
        """Test generating pagination for SQL Server."""
        yql = """
query:
  pagination:
    page: 2
    per_page: 20
  select:
    - id: c.id
  from:
    c: customers
  order_by:
    - field: c.id
      direction: ASC
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # page=2, per_page=20 -> OFFSET (2-1)*20=20 ROWS FETCH NEXT 20 ROWS ONLY
        assert "OFFSET 20 ROWS" in sql
        assert "FETCH NEXT 20 ROWS ONLY" in sql


class TestSQLServerGenerateJoin:
    """SQL Server JOIN tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN for SQL Server."""
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
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "INNER JOIN orders o ON c.id = o.customer_id" in sql

