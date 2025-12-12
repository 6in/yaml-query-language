"""Tests for UPSERT statement parsing and generation."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect
from yql.ast import OperationType

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestParseUpsert:
    """UPSERT parsing tests."""
    
    def test_parse_upsert_postgresql(self):
        """Test parsing PostgreSQL UPSERT (ON CONFLICT)."""
        result = parse_file(FIXTURES_DIR / "upsert_postgresql" / "before.yql")
        
        assert result.operation == OperationType.UPSERT
        assert result.upsert_query is not None
        assert result.upsert_query.table == "test"
        assert result.upsert_query.on_conflict is not None
        assert result.upsert_query.on_conflict.target == ["id"]
    
    def test_parse_upsert_mysql(self):
        """Test parsing MySQL UPSERT (ON DUPLICATE KEY)."""
        result = parse_file(FIXTURES_DIR / "upsert_mysql" / "before.yql")
        
        assert result.operation == OperationType.UPSERT
        assert result.upsert_query.table == "test"
        assert result.upsert_query.on_duplicate_key is not None
    
    def test_parse_upsert_merge(self):
        """Test parsing SQL Server/Oracle UPSERT (MERGE)."""
        result = parse_file(FIXTURES_DIR / "upsert_merge" / "before.yql")
        
        assert result.operation == OperationType.UPSERT
        assert result.upsert_query.table == "test"
        assert result.upsert_query.alias == "target"
        assert result.upsert_query.match_on == ["id"]
        assert result.upsert_query.when_matched is not None
        assert result.upsert_query.when_not_matched is not None


class TestGenerateUpsert:
    """UPSERT SQL generation tests."""
    
    def test_generate_upsert_postgresql(self):
        """Test generating PostgreSQL UPSERT (INSERT ... ON CONFLICT)."""
        result = parse_file(FIXTURES_DIR / "upsert_postgresql" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "upsert_postgresql" / "postgresql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_upsert_mysql(self):
        """Test generating MySQL UPSERT (INSERT ... ON DUPLICATE KEY UPDATE)."""
        result = parse_file(FIXTURES_DIR / "upsert_mysql" / "before.yql")
        sql = generate_sql(result, Dialect.MYSQL)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "upsert_mysql" / "mysql.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_upsert_sqlserver(self):
        """Test generating SQL Server UPSERT (MERGE)."""
        result = parse_file(FIXTURES_DIR / "upsert_merge" / "before.yql")
        sql = generate_sql(result, Dialect.SQLSERVER)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "upsert_merge" / "sqlserver.sql").read_text().strip()
        assert sql.strip() == expected_sql
    
    def test_generate_upsert_oracle(self):
        """Test generating Oracle UPSERT (MERGE)."""
        result = parse_file(FIXTURES_DIR / "upsert_merge" / "before.yql")
        sql = generate_sql(result, Dialect.ORACLE)
        
        # Compare with expected SQL file
        expected_sql = (FIXTURES_DIR / "upsert_merge" / "oracle.sql").read_text().strip()
        assert sql.strip() == expected_sql

