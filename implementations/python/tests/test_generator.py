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
        result = parse_file(FIXTURES_DIR / "simple_select" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "simple_select" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_with_where(self):
        """Test generating SELECT with WHERE."""
        result = parse_file(FIXTURES_DIR / "select_with_where" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "WHERE c.status = 'active'" in sql


class TestGenerateJoin:
    """JOIN SQL generation tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN."""
        result = parse_file(FIXTURES_DIR / "select_with_join" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_join" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
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
        result = parse_file(FIXTURES_DIR / "select_with_group_by_having" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_group_by_having" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestGenerateOrderBy:
    """ORDER BY SQL generation tests."""
    
    def test_generate_order_by(self):
        """Test generating ORDER BY."""
        result = parse_file(FIXTURES_DIR / "select_with_order_by_desc" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_order_by_desc" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_multiple_order_by(self):
        """Test generating multiple ORDER BY columns."""
        result = parse_file(FIXTURES_DIR / "select_with_multiple_order_by" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_multiple_order_by" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestGenerateLimitOffset:
    """LIMIT/OFFSET SQL generation tests."""
    
    def test_generate_limit(self):
        """Test generating LIMIT."""
        result = parse_file(FIXTURES_DIR / "select_with_limit" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_limit_offset(self):
        """Test generating LIMIT and OFFSET."""
        result = parse_file(FIXTURES_DIR / "select_with_limit_offset" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit_offset" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestGenerateWithClause:
    """WITH clause (CTE) SQL generation tests."""
    
    def test_generate_single_cte(self):
        """Test generating single CTE."""
        result = parse_file(FIXTURES_DIR / "select_with_cte" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_cte" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestGenerateComplex:
    """Complex query SQL generation tests."""
    
    def test_generate_complex_query(self):
        """Test generating complex query with multiple clauses."""
        result = parse_file(FIXTURES_DIR / "select_complex" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_complex" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql

