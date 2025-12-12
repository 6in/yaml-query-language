"""Base SQL Generator."""

from abc import ABC, abstractmethod

from ..ast import (
    Column,
    DeleteQuery,
    FromClause,
    InsertQuery,
    JoinClause,
    OperationType,
    OrderByClause,
    SelectQuery,
    UpdateQuery,
    UpsertQuery,
    WithClause,
    YQLQuery,
)


class BaseGenerator(ABC):
    """Base class for SQL generators."""
    
    def __init__(self):
        self._indent = "  "
    
    def generate(self, yql: YQLQuery) -> str:
        """Generate SQL from YQL AST.
        
        Args:
            yql: YQL AST
            
        Returns:
            Generated SQL string
        """
        if yql.operation == OperationType.SELECT:
            if yql.select_query is None:
                raise ValueError("SELECT query is empty")
            return self._generate_select(yql.select_query)
        elif yql.operation == OperationType.INSERT:
            if yql.insert_query is None:
                raise ValueError("INSERT query is empty")
            return self._generate_insert(yql.insert_query)
        elif yql.operation == OperationType.UPDATE:
            if yql.update_query is None:
                raise ValueError("UPDATE query is empty")
            return self._generate_update(yql.update_query)
        elif yql.operation == OperationType.DELETE:
            if yql.delete_query is None:
                raise ValueError("DELETE query is empty")
            return self._generate_delete(yql.delete_query)
        elif yql.operation == OperationType.UPSERT:
            if yql.upsert_query is None:
                raise ValueError("UPSERT query is empty")
            return self._generate_upsert(yql.upsert_query)
        else:
            raise ValueError(f"Unsupported operation: {yql.operation}")
    
    def _generate_select(self, query: SelectQuery) -> str:
        """Generate SELECT statement."""
        parts = []
        
        # WITH clauses
        if query.with_clauses:
            parts.append(self._generate_with_clauses(query.with_clauses))
        
        # SELECT clause
        parts.append(self._generate_select_clause(query.select))
        
        # FROM clause
        if query.from_clause:
            parts.append(self._generate_from_clause(query.from_clause))
        
        # JOINs
        for join in query.joins:
            parts.append(self._generate_join(join))
        
        # WHERE clause
        if query.where:
            parts.append(self._generate_where_clause(query.where))
        
        # GROUP BY
        if query.group_by:
            parts.append(self._generate_group_by(query.group_by))
        
        # HAVING
        if query.having:
            parts.append(self._generate_having(query.having))
        
        # ORDER BY
        if query.order_by:
            parts.append(self._generate_order_by(query.order_by))
        
        # LIMIT/OFFSET or pagination
        if query.pagination:
            parts.append(self._generate_pagination(query))
        else:
            if query.limit is not None:
                parts.append(self._generate_limit(query.limit))
            if query.offset is not None:
                parts.append(self._generate_offset(query.offset))
        
        return "\n".join(parts)
    
    def _generate_with_clauses(self, with_clauses: list[WithClause]) -> str:
        """Generate WITH clauses."""
        cte_parts = []
        for cte in with_clauses:
            cte_sql = self._generate_select(cte.query)
            # Indent the CTE query
            indented = "\n".join(f"{self._indent}{line}" for line in cte_sql.split("\n"))
            cte_parts.append(f"{cte.name} AS (\n{indented}\n)")
        
        return "WITH " + ",\n".join(cte_parts)
    
    def _generate_select_clause(self, columns: list[Column]) -> str:
        """Generate SELECT clause."""
        if not columns:
            return "SELECT *"
        
        column_strs = []
        for col in columns:
            if col.alias == col.expression:
                column_strs.append(col.expression)
            else:
                column_strs.append(f"{col.expression} AS {col.alias}")
        
        return "SELECT\n" + ",\n".join(f"{self._indent}{c}" for c in column_strs)
    
    def _generate_from_clause(self, from_clause: FromClause) -> str:
        """Generate FROM clause."""
        if from_clause.alias == from_clause.table:
            return f"FROM {from_clause.table}"
        return f"FROM {from_clause.table} {from_clause.alias}"
    
    def _generate_join(self, join: JoinClause) -> str:
        """Generate JOIN clause."""
        join_type = join.type.value
        
        # Build ON conditions
        all_conditions = list(join.on) + list(join.additional_conditions)
        on_clause = " AND ".join(c for c in all_conditions if c)
        
        if on_clause:
            return f"{join_type} JOIN {join.table} {join.alias} ON {on_clause}"
        else:
            # CROSS JOIN doesn't need ON clause
            return f"{join_type} JOIN {join.table} {join.alias}"
    
    def _generate_where_clause(self, conditions: list[str]) -> str:
        """Generate WHERE clause."""
        if len(conditions) == 1:
            return f"WHERE {conditions[0]}"
        
        formatted = f"\n{self._indent}AND ".join(conditions)
        return f"WHERE {formatted}"
    
    def _generate_group_by(self, columns: list[str]) -> str:
        """Generate GROUP BY clause."""
        return f"GROUP BY {', '.join(columns)}"
    
    def _generate_having(self, conditions: list[str]) -> str:
        """Generate HAVING clause."""
        return f"HAVING {' AND '.join(conditions)}"
    
    def _generate_order_by(self, order_by: list[OrderByClause]) -> str:
        """Generate ORDER BY clause."""
        parts = []
        for ob in order_by:
            parts.append(f"{ob.field} {ob.direction.value}")
        return f"ORDER BY {', '.join(parts)}"
    
    @abstractmethod
    def _generate_limit(self, limit: int | str) -> str:
        """Generate LIMIT clause (dialect-specific)."""
        pass
    
    @abstractmethod
    def _generate_offset(self, offset: int | str) -> str:
        """Generate OFFSET clause (dialect-specific)."""
        pass
    
    @abstractmethod
    def _generate_pagination(self, query: SelectQuery) -> str:
        """Generate pagination (dialect-specific)."""
        pass
    
    # ==================== INSERT ====================
    
    def _generate_insert(self, query: InsertQuery) -> str:
        """Generate INSERT statement."""
        parts = []
        
        # INSERT INTO table
        parts.append(f"INSERT INTO {query.table}")
        
        # Columns
        if query.columns:
            cols = ", ".join(query.columns)
            parts.append(f"({cols})")
        elif query.values:
            # Infer columns from first row
            cols = ", ".join(query.values[0].keys())
            parts.append(f"({cols})")
        
        # VALUES or SELECT
        if query.from_query:
            parts.append(self._generate_select(query.from_query))
        elif query.values:
            values_parts = []
            for row in query.values:
                vals = ", ".join(self._format_value(v) for v in row.values())
                values_parts.append(f"({vals})")
            parts.append("VALUES " + ", ".join(values_parts))
        
        # RETURNING
        if query.returning:
            parts.append(self._generate_returning(query.returning))
        
        return "\n".join(parts)
    
    def _format_value(self, value) -> str:
        """Format a value for SQL.
        
        Parameters, macros, and expressions are passed through as-is
        to allow template engines to handle them.
        """
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            # Pass through parameters, macros, and expressions as-is
            # This allows template engines (Jinja2, etc.) to handle them
            if value.startswith("#{") or value.startswith("${") or value.startswith("@{"):
                # Parameter, array parameter, or macro - pass through
                return value
            else:
                # String literal or expression - pass through
                return value
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)
    
    def _generate_returning(self, columns: list[str]) -> str:
        """Generate RETURNING clause (PostgreSQL-specific, override for others)."""
        return f"RETURNING {', '.join(columns)}"
    
    # ==================== UPDATE ====================
    
    def _generate_update(self, query: UpdateQuery) -> str:
        """Generate UPDATE statement."""
        parts = []
        
        # UPDATE table
        if query.alias:
            parts.append(f"UPDATE {query.table} {query.alias}")
        else:
            parts.append(f"UPDATE {query.table}")
        
        # SET clause
        set_parts = []
        for col, val in query.set_values.items():
            set_parts.append(f"{col} = {self._format_value(val)}")
        parts.append("SET " + ", ".join(set_parts))
        
        # JOINs (dialect-specific, default: not supported)
        # Override in dialect-specific generators
        
        # WHERE clause
        if query.where:
            parts.append(self._generate_where_clause(query.where))
        
        # RETURNING
        if query.returning:
            parts.append(self._generate_returning(query.returning))
        
        return "\n".join(parts)
    
    # ==================== DELETE ====================
    
    def _generate_delete(self, query: DeleteQuery) -> str:
        """Generate DELETE statement."""
        parts = []
        
        # DELETE FROM table
        if query.alias:
            parts.append(f"DELETE FROM {query.table} {query.alias}")
        else:
            parts.append(f"DELETE FROM {query.table}")
        
        # JOINs (dialect-specific, default: not supported)
        # Override in dialect-specific generators
        
        # WHERE clause
        if query.where:
            parts.append(self._generate_where_clause(query.where))
        
        # RETURNING
        if query.returning:
            parts.append(self._generate_returning(query.returning))
        
        return "\n".join(parts)


    # ==================== UPSERT ====================
    
    @abstractmethod
    def _generate_upsert(self, query: UpsertQuery) -> str:
        """Generate UPSERT statement (dialect-specific)."""
        pass
