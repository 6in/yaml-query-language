"""SQL Generators for different database dialects."""

from enum import Enum

from ..ast import YQLQuery
from .base import BaseGenerator
from .postgresql import PostgreSQLGenerator
from .mysql import MySQLGenerator
from .sqlserver import SQLServerGenerator


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
}


def generate_sql(query: YQLQuery, dialect: Dialect = Dialect.POSTGRESQL) -> str:
    """Generate SQL from YQL AST.
    
    Args:
        query: YQL AST
        dialect: Target database dialect
        
    Returns:
        Generated SQL string
        
    Raises:
        ValueError: If dialect is not supported
    """
    generator_class = _GENERATORS.get(dialect)
    if generator_class is None:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    generator = generator_class()
    return generator.generate(query)


__all__ = ["Dialect", "generate_sql", "BaseGenerator", "PostgreSQLGenerator", "MySQLGenerator", "SQLServerGenerator"]

