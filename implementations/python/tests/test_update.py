"""Tests for UPDATE statement parsing and generation."""

import pytest

from yql import parse, generate_sql, Dialect
from yql.ast import OperationType


class TestParseUpdate:
    """UPDATE parsing tests."""
    
    def test_parse_simple_update(self):
        """Test parsing simple UPDATE."""
        yql = """
operation: update
table: customers
set:
  name: "John Doe"
  status: "active"
where:
  - "id = 1"
"""
        result = parse(yql)
        
        assert result.operation == OperationType.UPDATE
        assert result.update_query is not None
        assert result.update_query.table == "customers"
        assert result.update_query.set_values["name"] == "John Doe"
        assert len(result.update_query.where) == 1
    
    def test_parse_update_with_alias(self):
        """Test parsing UPDATE with table alias."""
        yql = """
operation: update
table:
  c: customers
set:
  name: "John Doe"
where:
  - "c.id = 1"
"""
        result = parse(yql)
        
        assert result.update_query.table == "customers"
        assert result.update_query.alias == "c"
    
    def test_parse_update_with_returning(self):
        """Test parsing UPDATE with RETURNING."""
        yql = """
operation: update
table: customers
set:
  status: "inactive"
where:
  - "id = 1"
returning:
  - id
  - status
"""
        result = parse(yql)
        
        assert result.update_query.returning == ["id", "status"]


class TestGenerateUpdate:
    """UPDATE SQL generation tests."""
    
    def test_generate_simple_update(self):
        """Test generating simple UPDATE."""
        yql = """
operation: update
table: customers
set:
  name: "John Doe"
  status: "active"
where:
  - "id = 1"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "UPDATE customers" in sql
        assert "SET" in sql
        assert "name = John Doe" in sql
        assert "status = active" in sql
        assert "WHERE id = 1" in sql
    
    def test_generate_update_with_returning(self):
        """Test generating UPDATE with RETURNING (PostgreSQL)."""
        yql = """
operation: update
table: customers
set:
  status: "inactive"
where:
  - "id = 1"
returning:
  - id
  - status
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "RETURNING id, status" in sql

