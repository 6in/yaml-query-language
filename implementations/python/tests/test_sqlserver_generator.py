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
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "simple_select" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestSQLServerGenerateTop:
    """SQL Server TOP tests."""
    
    def test_generate_top(self):
        """Test generating TOP for SQL Server (LIMIT without OFFSET)."""
        result = parse_file(FIXTURES_DIR / "select_with_limit" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestSQLServerGenerateOffsetFetch:
    """SQL Server OFFSET-FETCH tests."""
    
    def test_generate_offset_fetch(self):
        """Test generating OFFSET-FETCH for SQL Server."""
        result = parse_file(FIXTURES_DIR / "select_with_order_by" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_order_by" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_offset_fetch_requires_order_by(self):
        """Test that OFFSET-FETCH adds ORDER BY if not specified."""
        result = parse_file(FIXTURES_DIR / "select_with_limit_offset" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit_offset" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestSQLServerGeneratePagination:
    """SQL Server pagination tests."""
    
    def test_generate_pagination(self):
        """Test generating pagination for SQL Server."""
        result = parse_file(FIXTURES_DIR / "select_with_pagination_literal" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_pagination_literal" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestSQLServerGenerateJoin:
    """SQL Server JOIN tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN for SQL Server."""
        result = parse_file(FIXTURES_DIR / "select_with_join" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_join" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql

