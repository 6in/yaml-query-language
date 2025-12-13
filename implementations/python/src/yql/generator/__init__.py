"""SQL Generators for different database dialects."""

from enum import Enum
from typing import TYPE_CHECKING

from ..ast import YQLQuery
from .base import BaseGenerator
from .mysql import MySQLGenerator
from .oracle import OracleGenerator
from .postgresql import PostgreSQLGenerator
from .sqlserver import SQLServerGenerator

if TYPE_CHECKING:
    from ..security import SecurityConfig


class Dialect(Enum):
    """Supported database dialects."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"


_GENERATORS: dict[Dialect, type[BaseGenerator]] = {
    Dialect.POSTGRESQL: PostgreSQLGenerator,
    Dialect.MYSQL: MySQLGenerator,
    Dialect.SQLSERVER: SQLServerGenerator,
    Dialect.ORACLE: OracleGenerator,
}


def generate_sql(
    query: YQLQuery,
    dialect: Dialect = Dialect.POSTGRESQL,
    security_config: "SecurityConfig | None" = None,
) -> str:
    """Generate SQL from YQL AST.
    
    Args:
        query: YQL AST
        dialect: Target database dialect
        security_config: Optional security configuration for table access control
        
    Returns:
        Generated SQL string
        
    Raises:
        ValueError: If dialect is not supported
        SecurityError: If forbidden tables are used (when security_config is provided)
    """
    generator_class = _GENERATORS.get(dialect)
    if generator_class is None:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    generator = generator_class()
    sql = generator.generate(query)
    
    # Validate SQL against security rules (hook before file output)
    if security_config is not None:
        security_config.validate_sql(sql)
    
    return sql


__all__ = [
    "Dialect",
    "generate_sql",
    "BaseGenerator",
    "PostgreSQLGenerator",
    "MySQLGenerator",
    "SQLServerGenerator",
    "OracleGenerator",
]

