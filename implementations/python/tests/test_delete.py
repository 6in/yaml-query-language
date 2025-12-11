"""Tests for DELETE statement parsing and generation."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect
from yql.ast import OperationType

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestParseDelete:
    """DELETE parsing tests."""
    
    def test_parse_simple_delete(self):
        """Test parsing simple DELETE."""
        result = parse_file(FIXTURES_DIR / "delete_simple.yql")
        
        assert result.operation == OperationType.DELETE
        assert result.delete_query is not None
        assert result.delete_query.table == "customers"
        assert len(result.delete_query.where) == 1
    
    def test_parse_delete_with_alias(self):
        """Test parsing DELETE with table alias."""
        result = parse_file(FIXTURES_DIR / "delete_with_alias.yql")
        
        assert result.delete_query.table == "customers"
        assert result.delete_query.alias == "c"
    
    def test_parse_delete_with_returning(self):
        """Test parsing DELETE with RETURNING."""
        result = parse_file(FIXTURES_DIR / "delete_with_returning.yql")
        
        assert result.delete_query.returning == ["id", "name"]


class TestGenerateDelete:
    """DELETE SQL generation tests."""
    
    def test_generate_simple_delete(self):
        """Test generating simple DELETE."""
        result = parse_file(FIXTURES_DIR / "delete_simple.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "DELETE FROM customers" in sql
        assert "WHERE id = 1" in sql
    
    def test_generate_delete_with_alias(self):
        """Test generating DELETE with alias."""
        result = parse_file(FIXTURES_DIR / "delete_with_alias.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "DELETE FROM customers c" in sql
        assert "WHERE c.status = 'deleted'" in sql
    
    def test_generate_delete_with_returning(self):
        """Test generating DELETE with RETURNING (PostgreSQL)."""
        result = parse_file(FIXTURES_DIR / "delete_with_returning.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "RETURNING id, name" in sql

