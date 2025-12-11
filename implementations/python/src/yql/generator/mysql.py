"""MySQL SQL Generator."""

from ..ast import SelectQuery, UpsertQuery
from .base import BaseGenerator


class MySQLGenerator(BaseGenerator):
    """MySQL-specific SQL generator."""
    
    def _generate_limit(self, limit: int | str) -> str:
        """Generate LIMIT clause for MySQL."""
        return f"LIMIT {limit}"
    
    def _generate_offset(self, offset: int | str) -> str:
        """Generate OFFSET clause for MySQL.
        
        Note: MySQL requires LIMIT when using OFFSET.
        """
        return f"OFFSET {offset}"
    
    def _generate_pagination(self, query: SelectQuery) -> str:
        """Generate pagination for MySQL.
        
        Converts pagination settings to LIMIT/OFFSET.
        """
        if query.pagination is None:
            return ""
        
        page = query.pagination.page
        per_page = query.pagination.per_page
        
        limit_expr = per_page
        
        # Calculate offset expression
        if "#{" in str(page):
            # Parameter format - output for template engine
            offset_expr = f"(({page} - 1) * {per_page})"
        else:
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
        """Generate UPSERT statement for MySQL (INSERT ... ON DUPLICATE KEY UPDATE)."""
        if not query.on_duplicate_key:
            raise ValueError("MySQL UPSERT requires 'on_duplicate_key' clause")
        
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
        
        # ON DUPLICATE KEY UPDATE
        duplicate = query.on_duplicate_key
        if not duplicate.update:
            raise ValueError("MySQL ON DUPLICATE KEY UPDATE requires 'update' clause")
        
        update_parts = []
        for col, val in duplicate.update.items():
            update_parts.append(f"{col} = {val}")
        
        parts.append("ON DUPLICATE KEY UPDATE\n" + ",\n".join(f"  {u}" for u in update_parts))
        
        return "\n".join(parts)
