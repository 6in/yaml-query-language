"""SQL Server SQL Generator."""

from ..ast import OrderByClause, SelectQuery, UpsertQuery
from .base import BaseGenerator


class SQLServerGenerator(BaseGenerator):
    """SQL Server-specific SQL generator."""
    
    def _generate_limit(self, limit: int | str) -> str:
        """Generate TOP clause for SQL Server.
        
        Note: SQL Server uses TOP instead of LIMIT (without OFFSET).
        When OFFSET is needed, use OFFSET-FETCH instead.
        """
        # This is called when only LIMIT is specified (no OFFSET)
        return ""  # Handled in _generate_select_clause
    
    def _generate_offset(self, offset: int | str) -> str:
        """Generate OFFSET clause for SQL Server."""
        return ""  # Handled in _generate_select
    
    def _generate_select(self, query: SelectQuery) -> str:
        """Generate SELECT statement for SQL Server.
        
        Overrides base to handle TOP and OFFSET-FETCH syntax.
        """
        parts = []
        
        # WITH clauses
        if query.with_clauses:
            parts.append(self._generate_with_clauses(query.with_clauses))
        
        # SELECT clause (with TOP if only LIMIT, no OFFSET)
        if query.limit is not None and query.offset is None and query.pagination is None:
            parts.append(self._generate_select_clause_with_top(query.select, query.limit))
        else:
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
        
        # ORDER BY (required for OFFSET-FETCH)
        if query.order_by:
            parts.append(self._generate_order_by(query.order_by))
        elif (query.offset is not None or query.pagination is not None):
            # SQL Server requires ORDER BY for OFFSET-FETCH
            # Add a dummy ORDER BY if not specified
            parts.append("ORDER BY (SELECT NULL)")
        
        # OFFSET-FETCH (when both LIMIT and OFFSET, or pagination)
        if query.pagination:
            parts.append(self._generate_pagination(query))
        elif query.limit is not None and query.offset is not None:
            parts.append(self._generate_offset_fetch(query.offset, query.limit))
        
        return "\n".join(parts)
    
    def _generate_select_clause_with_top(self, columns: list, limit: int | str) -> str:
        """Generate SELECT clause with TOP for SQL Server."""
        if not columns:
            return f"SELECT TOP {limit} *"
        
        column_strs = []
        for col in columns:
            if col.alias == col.expression:
                column_strs.append(col.expression)
            else:
                column_strs.append(f"{col.expression} AS {col.alias}")
        
        return f"SELECT TOP {limit}\n" + ",\n".join(f"{self._indent}{c}" for c in column_strs)
    
    def _generate_offset_fetch(self, offset: int | str, limit: int | str) -> str:
        """Generate OFFSET-FETCH clause for SQL Server."""
        return f"OFFSET {offset} ROWS\nFETCH NEXT {limit} ROWS ONLY"
    
    def _generate_pagination(self, query: SelectQuery) -> str:
        """Generate pagination for SQL Server.
        
        Uses OFFSET-FETCH syntax.
        """
        if query.pagination is None:
            return ""
        
        page = query.pagination.page
        per_page = query.pagination.per_page
        
        # Calculate offset expression
        if "#{" in str(page):
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
        
        return f"OFFSET {offset_expr} ROWS\nFETCH NEXT {per_page} ROWS ONLY"
    
    def _generate_upsert(self, query: UpsertQuery) -> str:
        """Generate UPSERT statement for SQL Server (MERGE)."""
        if not query.using or not query.match_on:
            raise ValueError("SQL Server UPSERT requires 'using' and 'match_on' clauses")
        
        parts = []
        
        # MERGE table AS target
        target_alias = query.alias or "target"
        parts.append(f"MERGE {query.table} AS {target_alias}")
        
        # USING clause
        using_sql = self._generate_select(query.using)
        parts.append(f"USING ({using_sql}) AS source")
        
        # ON clause (match_on)
        match_conditions = [f"{target_alias}.{col} = source.{col}" for col in query.match_on]
        parts.append(f"ON {' AND '.join(match_conditions)}")
        
        # WHEN MATCHED
        if query.when_matched:
            matched = query.when_matched
            if matched.delete:
                parts.append("WHEN MATCHED THEN DELETE")
            elif matched.update:
                update_parts = []
                for col, val in matched.update.items():
                    update_parts.append(f"{col} = {val}")
                
                matched_clause = "WHEN MATCHED"
                if matched.where:
                    matched_clause += f" AND {matched.where}"
                matched_clause += " THEN\n  UPDATE SET\n" + ",\n".join(f"    {u}" for u in update_parts)
                parts.append(matched_clause)
        
        # WHEN NOT MATCHED
        if query.when_not_matched:
            not_matched = query.when_not_matched
            if not_matched.insert:
                insert_cols = list(not_matched.insert.keys())
                insert_vals = [not_matched.insert[col] for col in insert_cols]
                
                parts.append(f"WHEN NOT MATCHED THEN\n  INSERT ({', '.join(insert_cols)})\n  VALUES ({', '.join(insert_vals)})")
        
        # Add semicolon for SQL Server
        return "\n".join(parts) + ";"

