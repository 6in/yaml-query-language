"""Tests for security configuration and table access control."""

import pytest

from yql import generate_sql, parse, Dialect, SecurityConfig, SecurityError


class TestSecurityConfig:
    """Tests for SecurityConfig."""
    
    def test_denied_tables_validation(self):
        """Test that denied tables are detected in generated SQL."""
        yql_content = """
query:
  select:
    - id: c.id
  from: { c: customers }
"""
        query = parse(yql_content)
        
        # No security config - should work
        sql = generate_sql(query, Dialect.POSTGRESQL)
        assert "customers" in sql
        
        # With security config denying customers
        config = SecurityConfig({"denied_tables": ["customers"]})
        with pytest.raises(SecurityError) as exc_info:
            generate_sql(query, Dialect.POSTGRESQL, security_config=config)
        
        error = exc_info.value
        assert "customers" in error.message
        assert "customers" in error.details["denied_tables"]
    
    def test_allowed_tables_validation(self):
        """Test that only allowed tables can be used."""
        yql_content = """
query:
  select:
    - id: c.id
  from: { c: customers }
"""
        query = parse(yql_content)
        
        # With security config allowing only orders
        config = SecurityConfig({"allowed_tables": ["orders"]})
        with pytest.raises(SecurityError) as exc_info:
            generate_sql(query, Dialect.POSTGRESQL, security_config=config)
        
        error = exc_info.value
        assert "customers" in error.message
        assert "customers" in error.details["unauthorized_tables"]
    
    def test_multiple_tables_validation(self):
        """Test validation with multiple tables (JOIN)."""
        yql_content = """
query:
  select:
    - id: c.id
    - order_id: o.id
  from: { c: customers }
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
"""
        query = parse(yql_content)
        
        # Deny orders table
        config = SecurityConfig({"denied_tables": ["orders"]})
        with pytest.raises(SecurityError) as exc_info:
            generate_sql(query, Dialect.POSTGRESQL, security_config=config)
        
        error = exc_info.value
        assert "orders" in error.message
        assert "orders" in error.details["denied_tables"]
    
    def test_insert_table_validation(self):
        """Test validation for INSERT statements."""
        yql_content = """
operation: insert
table: customers
values:
  name: "John"
  email: "john@example.com"
"""
        query = parse(yql_content)
        
        # Deny customers table
        config = SecurityConfig({"denied_tables": ["customers"]})
        with pytest.raises(SecurityError) as exc_info:
            generate_sql(query, Dialect.POSTGRESQL, security_config=config)
        
        error = exc_info.value
        assert "customers" in error.message
    
    def test_update_table_validation(self):
        """Test validation for UPDATE statements."""
        yql_content = """
operation: update
table: customers
set:
  name: "John"
where:
  - "id = 1"
"""
        query = parse(yql_content)
        
        # Deny customers table
        config = SecurityConfig({"denied_tables": ["customers"]})
        with pytest.raises(SecurityError) as exc_info:
            generate_sql(query, Dialect.POSTGRESQL, security_config=config)
        
        error = exc_info.value
        assert "customers" in error.message
    
    def test_delete_table_validation(self):
        """Test validation for DELETE statements."""
        yql_content = """
operation: delete
table: customers
where:
  - "id = 1"
"""
        query = parse(yql_content)
        
        # Deny customers table
        config = SecurityConfig({"denied_tables": ["customers"]})
        with pytest.raises(SecurityError) as exc_info:
            generate_sql(query, Dialect.POSTGRESQL, security_config=config)
        
        error = exc_info.value
        assert "customers" in error.message
    
    def test_security_config_from_file(self, tmp_path):
        """Test loading security config from file."""
        config_file = tmp_path / "security.yaml"
        config_file.write_text("""
denied_tables:
  - user_passwords
  - admin_logs
allowed_tables:
  - customers
  - orders
""")
        
        config = SecurityConfig.from_file(config_file)
        assert "user_passwords" in config.denied_tables
        assert "admin_logs" in config.denied_tables
        assert "customers" in config.allowed_tables
        assert "orders" in config.allowed_tables

