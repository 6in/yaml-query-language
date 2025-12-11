"""Oracle SQL Generator."""

from ..ast import SelectQuery, UpsertQuery
from .base import BaseGenerator


class OracleGenerator(BaseGenerator):
    """Oracle-specific SQL generator."""
    
    def _generate_limit(self, limit: int | str) -> str:
        """Generate LIMIT clause for Oracle.
        
        Oracle doesn't have LIMIT clause. This should be used with offset=0
        and will generate ROWNUM <= limit in WHERE clause.
        """
        # This is a fallback - normally we use ROWNUM in WHERE clause
        # or ROW_NUMBER() OVER() for offset > 0
        return f"WHERE ROWNUM <= {limit}"
    
    def _generate_offset(self, offset: int | str) -> str:
        """Generate OFFSET clause for Oracle.
        
        Oracle doesn't have OFFSET clause. This requires ROW_NUMBER() OVER()
        which is handled in _generate_pagination or when both limit and offset are present.
        """
        # This shouldn't be called directly - offset is handled via ROW_NUMBER()
        raise NotImplementedError("Oracle offset must be used with limit via ROW_NUMBER() OVER()")
    
    def _generate_pagination(self, query: SelectQuery) -> str:
        """Generate pagination for Oracle.
        
        Oracle uses ROW_NUMBER() OVER() for pagination with offset.
        If offset is 0, uses ROWNUM <= limit.
        """
        if query.pagination is None:
            return ""
        
        page = query.pagination.page
        per_page = query.pagination.per_page
        
        # Oracle requires ORDER BY for ROW_NUMBER() OVER()
        if not query.order_by:
            raise ValueError("Oracle pagination requires ORDER BY clause")
        
        # Extract parameter names or use as-is
        limit_expr = per_page
        
        # Calculate offset expression
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
        
        # Generate ORDER BY fields for ROW_NUMBER()
        order_by_fields = ", ".join(f"{ob.field} {ob.direction.value}" for ob in query.order_by)
        
        # Generate inner query (without pagination)
        inner_query = SelectQuery(
            select=query.select,
            from_clause=query.from_clause,
            joins=query.joins,
            where=query.where,
            group_by=query.group_by,
            having=query.having,
            order_by=query.order_by,
            with_clauses=query.with_clauses
        )
        inner_sql = super()._generate_select(inner_query)
        
        # Generate column list for outer SELECT
        if query.select:
            column_list = ", ".join(f"{col.expression} AS {col.alias}" if col.alias != col.expression else col.expression for col in query.select)
        else:
            column_list = "*"
        
        # Generate outer query with ROW_NUMBER() and WHERE clause
        return f"""SELECT {column_list} FROM (
  SELECT {column_list}, ROW_NUMBER() OVER (ORDER BY {order_by_fields}) AS rn
  FROM ({inner_sql}) subquery
) WHERE rn > {offset_expr} AND rn <= ({offset_expr} + {limit_expr})"""
    
    def _generate_select(self, query: SelectQuery) -> str:
        """Generate SELECT statement for Oracle.
        
        Handles LIMIT/OFFSET conversion to ROWNUM or ROW_NUMBER() OVER().
        """
        # If we have both limit and offset, use ROW_NUMBER() OVER()
        if query.limit is not None and query.offset is not None and query.offset != 0:
            return self._generate_select_with_row_number(query)
        
        # If we have only limit with offset=0, use ROWNUM
        if query.limit is not None and (query.offset is None or query.offset == 0):
            return self._generate_select_with_rownum(query)
        
        # Otherwise, use standard SELECT
        return super()._generate_select(query)
    
    def _generate_select_with_rownum(self, query: SelectQuery) -> str:
        """Generate SELECT with ROWNUM for simple limit (offset=0)."""
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
        where_conditions = list(query.where) if query.where else []
        # Add ROWNUM condition
        where_conditions.append(f"ROWNUM <= {query.limit}")
        if where_conditions:
            parts.append(self._generate_where_clause(where_conditions))
        
        # GROUP BY
        if query.group_by:
            parts.append(self._generate_group_by(query.group_by))
        
        # HAVING
        if query.having:
            parts.append(self._generate_having(query.having))
        
        # ORDER BY
        if query.order_by:
            parts.append(self._generate_order_by(query.order_by))
        
        return "\n".join(parts)
    
    def _generate_select_with_row_number(self, query: SelectQuery) -> str:
        """Generate SELECT with ROW_NUMBER() OVER() for limit with offset."""
        # Oracle requires ORDER BY for ROW_NUMBER() OVER()
        if not query.order_by:
            raise ValueError("Oracle LIMIT with OFFSET requires ORDER BY clause")
        
        # Build inner query (without LIMIT/OFFSET)
        inner_query = SelectQuery(
            select=query.select,
            from_clause=query.from_clause,
            joins=query.joins,
            where=query.where,
            group_by=query.group_by,
            having=query.having,
            order_by=query.order_by,
            with_clauses=query.with_clauses
        )
        
        # Generate ORDER BY fields for ROW_NUMBER()
        order_by_fields = ", ".join(f"{ob.field} {ob.direction.value}" for ob in query.order_by)
        
        # Generate inner query SQL
        inner_sql = super()._generate_select(inner_query)
        
        # Generate column list for outer SELECT
        if query.select:
            column_list = ", ".join(f"{col.expression} AS {col.alias}" if col.alias != col.expression else col.expression for col in query.select)
        else:
            column_list = "*"
        
        # Calculate offset and limit
        offset_val = query.offset if isinstance(query.offset, (int, str)) else str(query.offset)
        limit_val = query.limit if isinstance(query.limit, (int, str)) else str(query.limit)
        
        # Generate outer query with ROW_NUMBER()
        return f"""SELECT {column_list} FROM (
  SELECT {column_list}, ROW_NUMBER() OVER (ORDER BY {order_by_fields}) AS rn
  FROM ({inner_sql}) subquery
) WHERE rn > {offset_val} AND rn <= ({offset_val} + {limit_val})"""
    
    def _generate_returning(self, columns: list[str]) -> str:
        """Generate RETURNING clause for Oracle.
        
        Oracle doesn't support RETURNING in INSERT/UPDATE/DELETE.
        This should not be called for Oracle.
        """
        raise NotImplementedError("Oracle does not support RETURNING clause. Use RETURNING INTO in stored procedures.")
    
    def _generate_upsert(self, query: UpsertQuery) -> str:
        """Generate UPSERT statement for Oracle (MERGE)."""
        if not query.using or not query.match_on:
            raise ValueError("Oracle UPSERT requires 'using' and 'match_on' clauses")
        
        parts = []
        
        # MERGE table AS target
        target_alias = query.alias or "target"
        parts.append(f"MERGE {query.table} AS {target_alias}")
        
        # USING clause
        # Check if using query needs FROM DUAL (constant values)
        using_sql = self._generate_select(query.using)
        # For Oracle, if using has no FROM clause, add FROM DUAL
        if "FROM" not in using_sql.upper():
            # This is a simplified check - in practice, we'd need to parse the SELECT
            # For now, assume if it's a simple SELECT with constants, add FROM DUAL
            using_sql = using_sql.rstrip() + "\nFROM DUAL"
        
        parts.append(f"USING ({using_sql}) AS source")
        
        # ON clause (match_on) - Oracle requires parentheses
        match_conditions = [f"{target_alias}.{col} = source.{col}" for col in query.match_on]
        parts.append(f"ON ({' AND '.join(match_conditions)})")
        
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
        
        # Add semicolon for Oracle
        return "\n".join(parts) + ";"

