"""PostgreSQL SQL Generator."""

from ..ast import SelectQuery
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

