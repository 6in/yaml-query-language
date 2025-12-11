"""MySQL SQL Generator."""

from ..ast import SelectQuery
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

