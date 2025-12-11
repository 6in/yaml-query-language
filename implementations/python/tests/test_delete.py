"""Tests for DELETE statement parsing and generation."""

import pytest

from yql import parse, generate_sql, Dialect
from yql.ast import OperationType


class TestParseDelete:
    """DELETE parsing tests."""
    
    def test_parse_simple_delete(self):
        """Test parsing simple DELETE."""
        yql = """
operation: delete
table: customers
where:
  - "id = 1"
"""
        result = parse(yql)
        
        assert result.operation == OperationType.DELETE
        assert result.delete_query is not None
        assert result.delete_query.table == "customers"
        assert len(result.delete_query.where) == 1
    
    def test_parse_delete_with_alias(self):
        """Test parsing DELETE with table alias."""
        yql = """
operation: delete
table:
  c: customers
where:
  - "c.id = 1"
"""
        result = parse(yql)
        
        assert result.delete_query.table == "customers"
        assert result.delete_query.alias == "c"
    
    def test_parse_delete_with_returning(self):
        """Test parsing DELETE with RETURNING."""
        yql = """
operation: delete
table: customers
where:
  - "id = 1"
returning:
  - id
  - name
"""
        result = parse(yql)
        
        assert result.delete_query.returning == ["id", "name"]


class TestGenerateDelete:
    """DELETE SQL generation tests."""
    
    def test_generate_simple_delete(self):
        """Test generating simple DELETE."""
        yql = """
operation: delete
table: customers
where:
  - "id = 1"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "DELETE FROM customers" in sql
        assert "WHERE id = 1" in sql
    
    def test_generate_delete_with_alias(self):
        """Test generating DELETE with alias."""
        yql = """
operation: delete
table:
  c: customers
where:
  - "c.status = 'deleted'"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "DELETE FROM customers c" in sql
        assert "WHERE c.status = 'deleted'" in sql
    
    def test_generate_delete_with_returning(self):
        """Test generating DELETE with RETURNING (PostgreSQL)."""
        yql = """
operation: delete
table: customers
where:
  - "id = 1"
returning:
  - id
  - name
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "RETURNING id, name" in sql

