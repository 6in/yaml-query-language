"""Tests for INSERT statement parsing and generation."""

import pytest

from yql import parse, generate_sql, Dialect
from yql.ast import OperationType


class TestParseInsert:
    """INSERT parsing tests."""
    
    def test_parse_simple_insert(self):
        """Test parsing simple INSERT."""
        yql = """
operation: insert
table: customers
values:
  id: 1
  name: "John Doe"
  email: "john@example.com"
"""
        result = parse(yql)
        
        assert result.operation == OperationType.INSERT
        assert result.insert_query is not None
        assert result.insert_query.table == "customers"
        assert len(result.insert_query.values) == 1
        assert result.insert_query.values[0]["id"] == 1
    
    def test_parse_insert_multiple_rows(self):
        """Test parsing INSERT with multiple rows."""
        yql = """
operation: insert
table: customers
values:
  - id: 1
    name: "John Doe"
  - id: 2
    name: "Jane Smith"
"""
        result = parse(yql)
        
        assert result.operation == OperationType.INSERT
        assert len(result.insert_query.values) == 2
    
    def test_parse_insert_with_returning(self):
        """Test parsing INSERT with RETURNING."""
        yql = """
operation: insert
table: customers
values:
  name: "John Doe"
returning:
  - id
  - created_at
"""
        result = parse(yql)
        
        assert result.insert_query.returning == ["id", "created_at"]


class TestGenerateInsert:
    """INSERT SQL generation tests."""
    
    def test_generate_simple_insert(self):
        """Test generating simple INSERT."""
        yql = """
operation: insert
table: customers
values:
  id: 1
  name: "John Doe"
  email: "john@example.com"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "INSERT INTO customers" in sql
        assert "(id, name, email)" in sql
        assert "VALUES" in sql
    
    def test_generate_insert_multiple_rows(self):
        """Test generating INSERT with multiple rows."""
        yql = """
operation: insert
table: customers
values:
  - id: 1
    name: "John"
  - id: 2
    name: "Jane"
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "INSERT INTO customers" in sql
        assert "VALUES" in sql
    
    def test_generate_insert_with_returning(self):
        """Test generating INSERT with RETURNING (PostgreSQL)."""
        yql = """
operation: insert
table: customers
values:
  name: "John Doe"
returning:
  - id
  - created_at
"""
        result = parse(yql)
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        assert "RETURNING id, created_at" in sql

