"""AST (Abstract Syntax Tree) definitions for YQL."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JoinType(Enum):
    """JOIN types."""
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"


class SortDirection(Enum):
    """Sort directions."""
    ASC = "ASC"
    DESC = "DESC"


class OperationType(Enum):
    """DML operation types."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"


@dataclass
class Column:
    """SELECT clause column."""
    alias: str
    expression: str


@dataclass
class FromClause:
    """FROM clause."""
    alias: str
    table: str


@dataclass
class JoinClause:
    """JOIN clause."""
    type: JoinType
    alias: str
    table: str
    on: str | list[str]
    additional_conditions: list[str] = field(default_factory=list)


@dataclass
class OrderByClause:
    """ORDER BY clause."""
    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class WithClause:
    """WITH clause (CTE)."""
    name: str
    query: "SelectQuery"


@dataclass
class Pagination:
    """Pagination settings."""
    page: str  # parameter expression like "#{page:1}"
    per_page: str  # parameter expression like "#{per_page:20}"


@dataclass
class SelectQuery:
    """SELECT query AST."""
    select: list[Column] = field(default_factory=list)
    from_clause: FromClause | None = None
    joins: list[JoinClause] = field(default_factory=list)
    where: list[str] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    having: list[str] = field(default_factory=list)
    order_by: list[OrderByClause] = field(default_factory=list)
    limit: int | str | None = None
    offset: int | str | None = None
    with_clauses: list[WithClause] = field(default_factory=list)
    pagination: Pagination | None = None


@dataclass
class InsertQuery:
    """INSERT query AST."""
    table: str
    columns: list[str] = field(default_factory=list)
    values: list[dict[str, Any]] = field(default_factory=list)  # List of row dicts
    from_query: SelectQuery | None = None  # INSERT ... SELECT
    returning: list[str] = field(default_factory=list)


@dataclass
class UpdateQuery:
    """UPDATE query AST."""
    table: str
    alias: str | None = None
    set_values: dict[str, Any] = field(default_factory=dict)
    joins: list[JoinClause] = field(default_factory=list)
    where: list[str] = field(default_factory=list)
    returning: list[str] = field(default_factory=list)


@dataclass
class DeleteQuery:
    """DELETE query AST."""
    table: str
    alias: str | None = None
    joins: list[JoinClause] = field(default_factory=list)
    where: list[str] = field(default_factory=list)
    returning: list[str] = field(default_factory=list)


@dataclass
class OnConflictClause:
    """PostgreSQL ON CONFLICT clause."""
    target: list[str] | None = None  # Column names
    unique_constraint: str | None = None  # Constraint name
    action: str = "update"  # "update" or "ignore"
    update: dict[str, Any] = field(default_factory=dict)  # Update values
    where: str | None = None  # Conditional update


@dataclass
class OnDuplicateKeyClause:
    """MySQL ON DUPLICATE KEY UPDATE clause."""
    update: dict[str, Any] = field(default_factory=dict)  # Update values


@dataclass
class WhenMatchedClause:
    """SQL Server/Oracle WHEN MATCHED clause."""
    update: dict[str, Any] = field(default_factory=dict)  # Update values
    where: str | None = None  # Conditional update
    delete: bool = False  # DELETE action


@dataclass
class WhenNotMatchedClause:
    """SQL Server/Oracle WHEN NOT MATCHED clause."""
    insert: dict[str, Any] = field(default_factory=dict)  # Insert values


@dataclass
class UpsertQuery:
    """UPSERT query AST."""
    table: str
    alias: str | None = None
    columns: list[str] = field(default_factory=list)
    values: list[dict[str, Any]] = field(default_factory=list)  # List of row dicts
    from_query: SelectQuery | None = None  # INSERT ... SELECT
    
    # PostgreSQL: on_conflict
    on_conflict: OnConflictClause | None = None
    
    # MySQL: on_duplicate_key
    on_duplicate_key: OnDuplicateKeyClause | None = None
    
    # SQL Server/Oracle: using, match_on, when_matched, when_not_matched
    using: SelectQuery | None = None  # USING clause (SELECT query)
    match_on: list[str] = field(default_factory=list)  # Match columns
    when_matched: WhenMatchedClause | None = None
    when_not_matched: WhenNotMatchedClause | None = None
    
    returning: list[str] = field(default_factory=list)


@dataclass
class YQLQuery:
    """Top-level YQL query container."""
    operation: OperationType = OperationType.SELECT
    select_query: SelectQuery | None = None
    insert_query: InsertQuery | None = None
    update_query: UpdateQuery | None = None
    delete_query: DeleteQuery | None = None
    upsert_query: UpsertQuery | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    
    @property
    def query(self) -> SelectQuery | None:
        """Backward compatibility: return select_query."""
        return self.select_query
