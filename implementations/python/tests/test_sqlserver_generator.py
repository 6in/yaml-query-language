"""Tests for SQL Server SQL Generator."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestSQLServerGenerateBasic:
    """Basic SQL Server SQL generation tests."""
    
    def test_generate_simple_select(self):
        """Test generating simple SELECT for SQL Server."""
        result = parse_file(FIXTURES_DIR / "simple_select" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "SELECT" in sql
        assert "c.id AS id" in sql
        assert "c.name AS name" in sql
        assert "FROM customers c" in sql


class TestSQLServerGenerateTop:
    """SQL Server TOP tests."""
    
    def test_generate_top(self):
        """Test generating TOP for SQL Server (LIMIT without OFFSET)."""
        result = parse_file(FIXTURES_DIR / "select_with_limit" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "SELECT TOP 10" in sql
        assert "OFFSET" not in sql


class TestSQLServerGenerateOffsetFetch:
    """SQL Server OFFSET-FETCH tests."""
    
    def test_generate_offset_fetch(self):
        """Test generating OFFSET-FETCH for SQL Server."""
        result = parse_file(FIXTURES_DIR / "select_with_order_by" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "OFFSET 20 ROWS" in sql
        assert "FETCH NEXT 10 ROWS ONLY" in sql
        assert "TOP" not in sql
    
    def test_generate_offset_fetch_requires_order_by(self):
        """Test that OFFSET-FETCH adds ORDER BY if not specified."""
        result = parse_file(FIXTURES_DIR / "select_with_limit_offset" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Should have ORDER BY (SELECT NULL) for SQL Server
        assert "ORDER BY" in sql
        assert "OFFSET 20 ROWS" in sql


class TestSQLServerGeneratePagination:
    """SQL Server pagination tests."""
    
    def test_generate_pagination(self):
        """Test generating pagination for SQL Server."""
        result = parse_file(FIXTURES_DIR / "select_with_pagination_literal" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # page=2, per_page=20 -> OFFSET (2-1)*20=20 ROWS FETCH NEXT 20 ROWS ONLY
        assert "OFFSET 20 ROWS" in sql
        assert "FETCH NEXT 20 ROWS ONLY" in sql


class TestSQLServerGenerateJoin:
    """SQL Server JOIN tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN for SQL Server."""
        result = parse_file(FIXTURES_DIR / "select_with_join" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        assert "INNER JOIN orders o ON c.id = o.customer_id" in sql

