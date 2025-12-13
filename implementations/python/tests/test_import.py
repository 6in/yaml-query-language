"""Tests for import functionality."""

from pathlib import Path

import pytest

from yql import parse_file, generate_sql, Dialect

# Fixture directory (shared across implementations)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestImportBasic:
    """Basic import functionality tests."""
    
    def test_import_select_definition(self):
        """Test importing a SELECT definition."""
        result = parse_file(FIXTURES_DIR / "test_import_usage" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Should contain the imported CTE
        assert "WITH customer_summary AS" in sql
        assert "FROM customer_summary cs" in sql
        assert "cs.order_count > 0" in sql
    
    def test_import_with_parameters(self):
        """Test importing a SELECT definition with parameters."""
        result = parse_file(FIXTURES_DIR / "test_import_param_usage" / "before.yql")
        sql = generate_sql(result, Dialect.POSTGRESQL)
        
        # Should contain the imported CTE with parameters applied
        assert "WITH premium_orders AS" in sql
        assert "c.status = premium" in sql or "c.status = 'premium'" in sql
        assert "o.amount >= 10000" in sql

