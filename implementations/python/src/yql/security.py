"""Security configuration and validation for YQL."""

import re
from pathlib import Path
from typing import Any

import yaml


class SecurityConfig:
    """Security configuration for table access control."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize security configuration.
        
        Args:
            config: Security configuration dictionary
                Example:
                {
                    "denied_tables": ["user_passwords", "admin_logs"],
                    "allowed_tables": ["customers", "orders"],  # Optional: whitelist
                }
        """
        self.config = config or {}
        self.denied_tables = set(self.config.get("denied_tables", []))
        self.allowed_tables = set(self.config.get("allowed_tables", []))
    
    @classmethod
    def from_file(cls, config_path: Path | str) -> "SecurityConfig":
        """Load security configuration from YAML file.
        
        Args:
            config_path: Path to security configuration YAML file
            
        Returns:
            SecurityConfig instance
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Security config file not found: {path}")
        
        with path.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        return cls(config)
    
    def validate_sql(self, sql: str) -> None:
        """Validate generated SQL against security rules.
        
        Args:
            sql: Generated SQL string
            
        Raises:
            SecurityError: If forbidden tables are used
        """
        # Extract table names from SQL
        # Simple regex to find table names after FROM, JOIN, UPDATE, INSERT INTO, DELETE FROM
        table_patterns = [
            r'\bFROM\s+(\w+)',  # FROM table_name
            r'\bJOIN\s+(\w+)',  # JOIN table_name
            r'\bUPDATE\s+(\w+)',  # UPDATE table_name
            r'\bINSERT\s+INTO\s+(\w+)',  # INSERT INTO table_name
            r'\bDELETE\s+FROM\s+(\w+)',  # DELETE FROM table_name
            r'\bMERGE\s+INTO\s+(\w+)',  # MERGE INTO table_name (Oracle/SQL Server)
        ]
        
        found_tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            found_tables.update(matches)
        
        # Check for denied tables
        used_denied_tables = found_tables & self.denied_tables
        if used_denied_tables:
            raise SecurityError(
                f"Forbidden tables used: {', '.join(sorted(used_denied_tables))}",
                denied_tables=list(used_denied_tables),
                all_tables=list(found_tables),
            )
        
        # If allowed_tables is specified, check that only allowed tables are used
        if self.allowed_tables:
            used_tables = found_tables - self.allowed_tables
            if used_tables:
                raise SecurityError(
                    f"Unauthorized tables used: {', '.join(sorted(used_tables))}",
                    unauthorized_tables=list(used_tables),
                    allowed_tables=list(self.allowed_tables),
                    all_tables=list(found_tables),
                )


class SecurityError(Exception):
    """Security validation error."""
    
    def __init__(self, message: str, **details):
        self.message = message
        self.details = details
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message

