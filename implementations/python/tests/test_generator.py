"""Tests for SQL Generator."""

import pytest

from yql import parse, generate_sql, Dialect


class TestGenerateBasic:
    """Basic SQL generation tests."""
    
    def test_generate_simple_select(self):
        """Test generating simple SELECT."""
        yql = """
query:
  select:
    - id: c.id
    - name: c.name
  from:
    c: customers
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "SELECT" in sql
        assert "c.id AS id" in sql
        assert "c.name AS name" in sql
        assert "FROM customers c" in sql
    
    def test_generate_with_where(self):
        """Test generating SELECT with WHERE."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  where:
    - "c.status = 'active'"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "WHERE c.status = 'active'" in sql


class TestGenerateJoin:
    """JOIN SQL generation tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN."""
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
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "INNER JOIN orders o ON c.id = o.customer_id" in sql
    
    def test_generate_left_join(self):
        """Test generating LEFT JOIN."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.id = o.customer_id"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "LEFT JOIN orders o ON c.id = o.customer_id" in sql


class TestGenerateGroupBy:
    """GROUP BY SQL generation tests."""
    
    def test_generate_group_by(self):
        """Test generating GROUP BY."""
        yql = """
query:
  select:
    - customer_id: o.customer_id
    - order_count: "COUNT(*)"
  from:
    o: orders
  group_by:
    - o.customer_id
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "GROUP BY o.customer_id" in sql
    
    def test_generate_group_by_having(self):
        """Test generating GROUP BY with HAVING."""
        yql = """
query:
  select:
    - customer_id: o.customer_id
    - order_count: "COUNT(*)"
  from:
    o: orders
  group_by:
    - o.customer_id
  having:
    - "COUNT(*) > 5"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "GROUP BY o.customer_id" in sql
        assert "HAVING COUNT(*) > 5" in sql


class TestGenerateOrderBy:
    """ORDER BY SQL generation tests."""
    
    def test_generate_order_by(self):
        """Test generating ORDER BY."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  order_by:
    - field: c.created_at
      direction: DESC
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "ORDER BY c.created_at DESC" in sql
    
    def test_generate_multiple_order_by(self):
        """Test generating multiple ORDER BY columns."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  order_by:
    - field: c.status
      direction: ASC
    - field: c.created_at
      direction: DESC
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "ORDER BY c.status ASC, c.created_at DESC" in sql


class TestGenerateLimitOffset:
    """LIMIT/OFFSET SQL generation tests."""
    
    def test_generate_limit(self):
        """Test generating LIMIT."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  limit: 10
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "LIMIT 10" in sql
    
    def test_generate_limit_offset(self):
        """Test generating LIMIT and OFFSET."""
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
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql


class TestGenerateWithClause:
    """WITH clause (CTE) SQL generation tests."""
    
    def test_generate_single_cte(self):
        """Test generating single CTE."""
        yql = """
query:
  with_clauses:
    active_customers:
      select:
        - id: c.id
        - name: c.name
      from:
        c: customers
      where:
        - "c.status = 'active'"
  select:
    - id: ac.id
    - name: ac.name
  from:
    ac: active_customers
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "WITH active_customers AS" in sql
        assert "c.status = 'active'" in sql
        assert "FROM active_customers ac" in sql


class TestGenerateComplex:
    """Complex query SQL generation tests."""
    
    def test_generate_complex_query(self):
        """Test generating complex query with multiple clauses."""
        yql = """
query:
  select:
    - customer_id: c.id
    - customer_name: c.name
    - order_count: "COUNT(o.id)"
    - total_amount: "SUM(o.amount)"
  from:
    c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.id = o.customer_id"
  where:
    - "c.status = 'active'"
  group_by:
    - c.id
    - c.name
  having:
    - "COUNT(o.id) > 0"
  order_by:
    - field: total_amount
      direction: DESC
  limit: 10
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Verify all parts are present
        assert "SELECT" in sql
        assert "c.id AS customer_id" in sql
        assert "COUNT(o.id) AS order_count" in sql
        assert "SUM(o.amount) AS total_amount" in sql
        assert "FROM customers c" in sql
        assert "LEFT JOIN orders o ON c.id = o.customer_id" in sql
        assert "WHERE c.status = 'active'" in sql
        assert "GROUP BY c.id, c.name" in sql
        assert "HAVING COUNT(o.id) > 0" in sql
        assert "ORDER BY total_amount DESC" in sql
        assert "LIMIT 10" in sql

