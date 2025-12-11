"""Tests for UPDATE statement parsing and generation."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect
from yql.ast import OperationType

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestParseUpdate:
    """UPDATE parsing tests."""
    
    def test_parse_simple_update(self):
        """Test parsing simple UPDATE."""
        result = parse_file(FIXTURES_DIR / "update_simple.yql")
        
        assert result.operation == OperationType.UPDATE
        assert result.update_query is not None
        assert result.update_query.table == "customers"
        assert result.update_query.set_values["name"] == "John Doe"
        assert len(result.update_query.where) == 1
    
    def test_parse_update_with_alias(self):
        """Test parsing UPDATE with table alias."""
        result = parse_file(FIXTURES_DIR / "update_with_alias.yql")
        
        assert result.update_query.table == "customers"
        assert result.update_query.alias == "c"
    
    def test_parse_update_with_returning(self):
        """Test parsing UPDATE with RETURNING."""
        result = parse_file(FIXTURES_DIR / "update_with_returning.yql")
        
        assert result.update_query.returning == ["id", "status"]


class TestGenerateUpdate:
    """UPDATE SQL generation tests."""
    
    def test_generate_simple_update(self):
        """Test generating simple UPDATE."""
        result = parse_file(FIXTURES_DIR / "update_simple.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "UPDATE customers" in sql
        assert "SET" in sql
        assert "name = John Doe" in sql
        assert "status = active" in sql
        assert "WHERE id = 1" in sql
    
    def test_generate_update_with_returning(self):
        """Test generating UPDATE with RETURNING (PostgreSQL)."""
        result = parse_file(FIXTURES_DIR / "update_with_returning.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "RETURNING id, status" in sql

