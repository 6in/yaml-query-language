"""Tests for MySQL SQL Generator."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestMySQLGenerateBasic:
    """Basic MySQL SQL generation tests."""
    
    def test_generate_simple_select(self):
        """Test generating simple SELECT for MySQL."""
        result = parse_file(FIXTURES_DIR / "simple_select" / "before.yql")
        sql = generate_sql(result, Dialect.MYSQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "simple_select" / "mysql.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestMySQLGenerateLimitOffset:
    """MySQL LIMIT/OFFSET tests."""
    
    def test_generate_limit(self):
        """Test generating LIMIT for MySQL."""
        result = parse_file(FIXTURES_DIR / "select_with_limit" / "before.yql")
        sql = generate_sql(result, Dialect.MYSQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit" / "mysql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_limit_offset(self):
        """Test generating LIMIT and OFFSET for MySQL."""
        result = parse_file(FIXTURES_DIR / "select_with_limit_offset" / "before.yql")
        sql = generate_sql(result, Dialect.MYSQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit_offset" / "mysql.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestMySQLGenerateJoin:
    """MySQL JOIN tests."""
    
    def test_generate_inner_join(self):
        """Test generating INNER JOIN for MySQL."""
        result = parse_file(FIXTURES_DIR / "select_with_join" / "before.yql")
        sql = generate_sql(result, Dialect.MYSQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_join" / "mysql.sql").read_text().strip()
        assert sql.strip() == expected_sql

