"""PostgreSQL SQL Generator."""

from ..ast import SelectQuery, UpsertQuery
from .base import BaseGenerator


class PostgreSQLGenerator(BaseGenerator):
    """PostgreSQL-specific SQL generator."""
    
    def _generate_limit(self, limit: int | str) -> str:
        """Generate LIMIT clause for PostgreSQL."""
        return f"LIMIT {limit}"
    
    def _generate_offset(self, offset: int | str) -> str:
        """Generate OFFSET clause for PostgreSQL."""
        return f"OFFSET {offset}"
    
    def _generate_pagination(self, query: SelectQuery) -> str:
        """Generate pagination for PostgreSQL.
        
        Converts pagination settings to LIMIT/OFFSET.
        """
        if query.pagination is None:
            return ""
        
        page = query.pagination.page
        per_page = query.pagination.per_page
        
        # For PostgreSQL, we generate:
        # LIMIT per_page OFFSET (page - 1) * per_page
        # But since these are parameters, we output them as-is for template engines
        
        # Extract parameter names or use as-is
        limit_expr = per_page
        
        # Calculate offset expression
        # If page is a parameter like "#{page:1}", we need to handle it
        if "#{" in str(page):
            # Parameter format - output for template engine
            offset_expr = f"(({page} - 1) * {per_page})"
        else:
            # Literal value
            try:
                page_val = int(page)
                per_page_val = int(per_page) if isinstance(per_page, (int, str)) and str(per_page).isdigit() else per_page
                if isinstance(per_page_val, int):
                    offset_expr = str((page_val - 1) * per_page_val)
                else:
                    offset_expr = f"(({page} - 1) * {per_page})"
            except ValueError:
                offset_expr = f"(({page} - 1) * {per_page})"
        
        return f"LIMIT {limit_expr}\nOFFSET {offset_expr}"
    
    def _generate_upsert(self, query: UpsertQuery) -> str:
        """Generate UPSERT statement for PostgreSQL (INSERT ... ON CONFLICT)."""
        if not query.on_conflict:
            raise ValueError("PostgreSQL UPSERT requires 'on_conflict' clause")
        
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
        elif query.from_query:
            # INSERT ... SELECT
            if query.columns:
                cols = ", ".join(query.columns)
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
        
        # ON CONFLICT
        conflict = query.on_conflict
        if conflict.target:
            parts.append(f"ON CONFLICT ({', '.join(conflict.target)})")
        elif conflict.unique_constraint:
            parts.append(f"ON CONFLICT ON CONSTRAINT {conflict.unique_constraint}")
        else:
            raise ValueError("PostgreSQL ON CONFLICT requires 'target' or 'unique_constraint'")
        
        # Action
        if conflict.action == "ignore":
            parts.append("DO NOTHING")
        elif conflict.action == "update":
            if not conflict.update:
                raise ValueError("PostgreSQL ON CONFLICT UPDATE requires 'update' clause")
            
            update_parts = []
            for col, val in conflict.update.items():
                update_parts.append(f"{col} = {val}")
            
            update_clause = "DO UPDATE SET\n" + ",\n".join(f"  {u}" for u in update_parts)
            
            # Conditional update
            if conflict.where:
                update_clause += f"\nWHERE {conflict.where}"
            
            parts.append(update_clause)
        
        # RETURNING
        if query.returning:
            parts.append(self._generate_returning(query.returning))
        
        return "\n".join(parts)
