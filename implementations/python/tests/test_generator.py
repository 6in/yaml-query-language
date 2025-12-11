"""Tests for SQL Generator."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestGenerateBasic:
    """Basic SQL generation tests."""
    
    def test_generate_simple_select(self):
        """Test generating simple SELECT."""
        result = parse_file(FIXTURES_DIR / "simple_select.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "SELECT" in sql
        assert "c.id AS id" in sql
        assert "c.name AS name" in sql
        assert "FROM customers c" in sql
    
    def test_generate_with_where(self):
        """Test generating SELECT with WHERE."""
        result = parse_file(FIXTURES_DIR / "select_with_where.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "WHERE c.status = 'active'" in sql


class TestGenerateJoin:
    """JOIN SQL generation tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN."""
        result = parse_file(FIXTURES_DIR / "select_with_join.yql")
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
        from yql import parse
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "LEFT JOIN orders o ON c.id = o.customer_id" in sql


class TestGenerateGroupBy:
    """GROUP BY SQL generation tests."""
    
    def test_generate_group_by(self):
        """Test generating GROUP BY."""
        from yql import parse
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
        result = parse_file(FIXTURES_DIR / "select_with_group_by_having.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "GROUP BY o.customer_id" in sql
        assert "HAVING COUNT(*) > 5" in sql


class TestGenerateOrderBy:
    """ORDER BY SQL generation tests."""
    
    def test_generate_order_by(self):
        """Test generating ORDER BY."""
        result = parse_file(FIXTURES_DIR / "select_with_order_by_desc.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "ORDER BY c.created_at DESC" in sql
    
    def test_generate_multiple_order_by(self):
        """Test generating multiple ORDER BY columns."""
        result = parse_file(FIXTURES_DIR / "select_with_multiple_order_by.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "ORDER BY c.status ASC, c.created_at DESC" in sql


class TestGenerateLimitOffset:
    """LIMIT/OFFSET SQL generation tests."""
    
    def test_generate_limit(self):
        """Test generating LIMIT."""
        result = parse_file(FIXTURES_DIR / "select_with_limit.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "LIMIT 10" in sql
    
    def test_generate_limit_offset(self):
        """Test generating LIMIT and OFFSET."""
        result = parse_file(FIXTURES_DIR / "select_with_limit_offset.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql


class TestGenerateWithClause:
    """WITH clause (CTE) SQL generation tests."""
    
    def test_generate_single_cte(self):
        """Test generating single CTE."""
        result = parse_file(FIXTURES_DIR / "select_with_cte.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "WITH active_customers AS" in sql
        assert "c.status = 'active'" in sql
        assert "FROM active_customers ac" in sql


class TestGenerateComplex:
    """Complex query SQL generation tests."""
    
    def test_generate_complex_query(self):
        """Test generating complex query with multiple clauses."""
        result = parse_file(FIXTURES_DIR / "select_complex.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Verify all parts are present
        assert "SELECT" in sql
        assert "c.id AS customer_id" in sql or "customer_id" in sql
        assert "COUNT(o.id) AS order_count" in sql
        assert "SUM(o.amount) AS total_amount" in sql
        assert "FROM customers c" in sql
        assert "LEFT JOIN orders o ON c.id = o.customer_id" in sql
        assert "WHERE c.status = 'active'" in sql
        assert "GROUP BY c.id, c.name" in sql
        assert "HAVING COUNT(o.id) > 0" in sql
        assert "ORDER BY total_amount DESC" in sql
        assert "LIMIT 10" in sql

