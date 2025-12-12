"""Tests for INSERT statement parsing and generation."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect
from yql.ast import OperationType

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestParseInsert:
    """INSERT parsing tests."""
    
    def test_parse_simple_insert(self):
        """Test parsing simple INSERT."""
        result = parse_file(FIXTURES_DIR / "insert_simple" / "before.yql")
        
        assert result.operation == OperationType.INSERT
        assert result.insert_query is not None
        assert result.insert_query.table == "customers"
        assert len(result.insert_query.values) == 1
        assert result.insert_query.values[0]["id"] == 1
    
    def test_parse_insert_multiple_rows(self):
        """Test parsing INSERT with multiple rows."""
        result = parse_file(FIXTURES_DIR / "insert_multiple_rows" / "before.yql")
        
        assert result.operation == OperationType.INSERT
        assert len(result.insert_query.values) == 2
    
    def test_parse_insert_with_returning(self):
        """Test parsing INSERT with RETURNING."""
        result = parse_file(FIXTURES_DIR / "insert_with_returning" / "before.yql")
        
        assert result.insert_query.returning == ["id", "created_at"]


class TestGenerateInsert:
    """INSERT SQL generation tests."""
    
    def test_generate_simple_insert(self):
        """Test generating simple INSERT."""
        result = parse_file(FIXTURES_DIR / "insert_simple" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "INSERT INTO customers" in sql
        assert "(id, name, email)" in sql
        assert "VALUES" in sql
    
    def test_generate_insert_multiple_rows(self):
        """Test generating INSERT with multiple rows."""
        result = parse_file(FIXTURES_DIR / "insert_multiple_rows" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "INSERT INTO customers" in sql
        assert "VALUES" in sql
    
    def test_generate_insert_with_returning(self):
        """Test generating INSERT with RETURNING (PostgreSQL)."""
        result = parse_file(FIXTURES_DIR / "insert_with_returning" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "RETURNING id, created_at" in sql

