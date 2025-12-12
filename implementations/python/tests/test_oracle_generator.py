"""Tests for Oracle SQL Generator."""

from pathlib import Path

import pytest

from yql import parse, parse_file, generate_sql, Dialect

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestOracleBasicSelect:
    """Test basic SELECT generation for Oracle."""
    
    def test_simple_select(self):
        """Test simple SELECT statement."""
        yql = """
query:
  select:
    - id: c.id
    - name: c.name
  from:
    c: customers
"""
        query = parse(yql)
        sql = generate_sql(query, Dialect.ORACLE)
        
        assert "SELECT" in sql
        assert "c.id AS id" in sql
        assert "c.name AS name" in sql
        assert "FROM customers c" in sql
    
    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  where:
    - "c.status = 'active'"
"""
        query = parse(yql)
        sql = generate_sql(query, Dialect.ORACLE)
        
        assert "WHERE" in sql
        assert "c.status = 'active'" in sql
    
    def test_select_with_join(self):
        """Test SELECT with JOIN."""
        yql = """
query:
  select:
    - customer_id: c.id
    - order_id: o.id
  from:
    c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
"""
        query = parse(yql)
        sql = generate_sql(query, Dialect.ORACLE)
        
        assert "INNER JOIN orders o" in sql
        assert "ON c.id = o.customer_id" in sql


class TestOracleLimitOffset:
    """Test LIMIT/OFFSET generation for Oracle."""
    
    def test_limit_only_with_rownum(self):
        """Test LIMIT only (uses ROWNUM)."""
        query = parse_file(FIXTURES_DIR / "select_with_limit" / "before.yql")
        sql = generate_sql(query, Dialect.ORACLE)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_limit" / "oracle.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_limit_with_offset_requires_order_by(self):
        """Test LIMIT with OFFSET requires ORDER BY."""
        query = parse_file(FIXTURES_DIR / "select_with_limit_offset" / "before.yql")
        
        # Should raise error without ORDER BY
        with pytest.raises(ValueError, match="ORDER BY"):
            generate_sql(query, Dialect.ORACLE)
    
    def test_limit_with_offset_with_order_by(self):
        """Test LIMIT with OFFSET and ORDER BY (uses ROW_NUMBER())."""
        query = parse_file(FIXTURES_DIR / "select_with_order_by" / "before.yql")
        sql = generate_sql(query, Dialect.ORACLE)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_order_by" / "oracle.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestOraclePagination:
    """Test pagination generation for Oracle."""
    
    def test_pagination_requires_order_by(self):
        """Test pagination requires ORDER BY."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
"""
        query = parse(yql)
        
        # Should raise error without ORDER BY
        with pytest.raises(ValueError, match="ORDER BY"):
            generate_sql(query, Dialect.ORACLE)
    
    def test_pagination_with_order_by(self):
        """Test pagination with ORDER BY."""
        query = parse_file(FIXTURES_DIR / "select_with_pagination" / "before.yql")
        sql = generate_sql(query, Dialect.ORACLE)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "select_with_pagination" / "oracle.sql").read_text().strip()
        assert sql.strip() == expected_sql


class TestOracleInsert:
    """Test INSERT generation for Oracle."""
    
    def test_simple_insert(self):
        """Test simple INSERT statement."""
        yql = """
operation: insert
table: customers
values:
  name: "John Doe"
  email: "john@example.com"
"""
        query = parse(yql)
        sql = generate_sql(query, Dialect.ORACLE)
        
        assert "INSERT INTO customers" in sql
        assert "VALUES" in sql
        assert "John Doe" in sql
    
    def test_insert_with_returning_raises_error(self):
        """Test INSERT with RETURNING raises error for Oracle."""
        yql = """
operation: insert
table: customers
values:
  name: "John Doe"
returning: [id]
"""
        query = parse(yql)
        
        # Oracle doesn't support RETURNING
        with pytest.raises(NotImplementedError, match="RETURNING"):
            generate_sql(query, Dialect.ORACLE)


class TestOracleUpdate:
    """Test UPDATE generation for Oracle."""
    
    def test_simple_update(self):
        """Test simple UPDATE statement."""
        from yql import parse
        yql = """
operation: update
table: customers
set:
  name: "John Doe"
  status: "active"
where:
  - "id = 1"
"""
        query = parse(yql)
        sql = generate_sql(query, Dialect.ORACLE)
        
        # Note: This test doesn't use fixture file, so we keep the assertion
        assert "UPDATE customers" in sql
        assert "SET" in sql
        assert "name = John Doe" in sql or "name = 'John Doe'" in sql
        assert "WHERE id = 1" in sql


class TestOracleDelete:
    """Test DELETE generation for Oracle."""
    
    def test_simple_delete(self):
        """Test simple DELETE statement."""
        from yql import parse
        yql = """
operation: delete
table: customers
where:
  - "status = 'deleted'"
"""
        query = parse(yql)
        sql = generate_sql(query, Dialect.ORACLE)
        
        # Note: This test doesn't use fixture file, so we keep the assertion
        assert "DELETE FROM customers" in sql
        assert "WHERE status = 'deleted'" in sql

