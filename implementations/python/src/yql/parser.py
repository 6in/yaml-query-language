"""YQL Parser - Parses YAML into AST."""

from pathlib import Path
from typing import Any

import yaml

from .ast import (
    Column,
    DeleteQuery,
    FromClause,
    InsertQuery,
    JoinClause,
    JoinType,
    OnConflictClause,
    OnDuplicateKeyClause,
    OperationType,
    OrderByClause,
    Pagination,
    SelectQuery,
    SortDirection,
    UpdateQuery,
    UpsertQuery,
    WhenMatchedClause,
    WhenNotMatchedClause,
    WithClause,
    YQLQuery,
)


class ParseError(Exception):
    """YQL parse error.
    
    Attributes:
        message: Error message
        category: Error category (syntax_error, security_error, logic_error)
        details: Additional error details (file path, line number, etc.)
    """
    def __init__(
        self,
        message: str,
        category: str = "syntax_error",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.category = category
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message


def parse(yql_content: str, base_path: Path | None = None) -> YQLQuery:
    """Parse YQL string into AST.
    
    Args:
        yql_content: YQL content as string (YAML format)
        base_path: Base path for resolving relative imports (optional)
        
    Returns:
        YQLQuery AST
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        data = yaml.safe_load(yql_content)
    except yaml.YAMLError as e:
        raise ParseError(f"YAML parse error: {e}") from e
    
    if not isinstance(data, dict):
        raise ParseError("YQL must be a YAML mapping")
    
    return _parse_yql(data, base_path)


def parse_file(path: str | Path) -> YQLQuery:
    """Parse YQL file into AST.
    
    Args:
        path: Path to YQL file
        
    Returns:
        YQLQuery AST
        
    Raises:
        ParseError: If parsing fails
        FileNotFoundError: If file not found
    """
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    base_path = path.parent
    return parse(content, base_path)


def _parse_yql(data: dict[str, Any], base_path: Path | None = None) -> YQLQuery:
    """Parse top-level YQL structure.
    
    Args:
        data: Parsed YAML data
        base_path: Base path for resolving relative imports (optional)
    """
    # Handle imports first
    imports = data.get("imports", [])
    imported_definitions = {}
    if imports:
        if base_path is None:
            # If no base_path provided, try to use current working directory
            base_path = Path.cwd()
        imported_definitions = _load_imports(imports, base_path, current_file=base_path)
    
    # Determine operation type
    operation_str = data.get("operation", "").lower()
    
    # Check for DML operations
    if operation_str == "upsert" or "on_conflict" in data or "on_duplicate_key" in data or ("using" in data and "match_on" in data):
        return _parse_upsert_yql(data, imported_definitions)
    elif operation_str == "insert" or "values" in data:
        return _parse_insert_yql(data, imported_definitions)
    elif operation_str == "update" or ("set" in data and "select" not in data):
        return _parse_update_yql(data, imported_definitions)
    elif operation_str == "delete" or (operation_str == "delete" and "table" in data):
        return _parse_delete_yql(data, imported_definitions)
    
    # Default to SELECT
    if "query" in data:
        query_data = data["query"]
    elif "select" in data or "with_clauses" in data:
        query_data = data
    else:
        raise ParseError("YQL must have 'query', 'select', or DML operation")
    
    query = _parse_select_query(query_data, imported_definitions)
    
    return YQLQuery(
        operation=OperationType.SELECT,
        select_query=query,
        raw=data,
    )


def _parse_upsert_yql(data: dict[str, Any], imported_definitions: dict[str, Any] | None = None) -> YQLQuery:
    """Parse UPSERT YQL."""
    table = data.get("table", "")
    if not table:
        raise ParseError("UPSERT must have 'table'")
    
    # Parse table alias if present (for SQL Server/Oracle MERGE)
    # Format: "alias: table_name" (per spec: table: target: table_name)
    # When parsed as YAML string: "target: table_name"
    alias = None
    if ":" in table:
        parts = table.split(":", 1)
        if len(parts) == 2:
            # Per spec: "alias: table_name" format
            alias = parts[0].strip()
            table = parts[1].strip()
    
    columns = data.get("columns", [])
    values_data = data.get("values", [])
    returning = data.get("returning", [])
    
    # Parse values
    values = []
    if isinstance(values_data, list):
        for item in values_data:
            if isinstance(item, dict):
                values.append(item)
            else:
                raise ParseError(f"Invalid values format: {item}")
    elif isinstance(values_data, dict):
        values = [values_data]
    
    # Parse from_query (INSERT ... SELECT)
    from_query = None
    if "from_query" in data:
        from_query = _parse_select_query(data["from_query"])
    
    # Parse PostgreSQL: on_conflict
    on_conflict = None
    if "on_conflict" in data:
        conflict_data = data["on_conflict"]
        # Support both 'columns' and 'target' for compatibility
        target = conflict_data.get("target") or conflict_data.get("columns")
        on_conflict = OnConflictClause(
            target=target,
            unique_constraint=conflict_data.get("unique_constraint"),
            action=conflict_data.get("action", "update"),
            update=conflict_data.get("update", {}),
            where=conflict_data.get("where"),
        )
    
    # Parse MySQL: on_duplicate_key
    on_duplicate_key = None
    if "on_duplicate_key" in data:
        duplicate_data = data["on_duplicate_key"]
        on_duplicate_key = OnDuplicateKeyClause(
            update=duplicate_data.get("update", {}),
        )
    
    # Parse SQL Server/Oracle: using, match_on, when_matched, when_not_matched
    using = None
    if "using" in data:
        using = _parse_select_query(data["using"])
    
    match_on = data.get("match_on", [])
    
    when_matched = None
    if "when_matched" in data:
        matched_data = data["when_matched"]
        when_matched = WhenMatchedClause(
            update=matched_data.get("update", {}),
            where=matched_data.get("where"),
            delete=matched_data.get("delete", False),
        )
    
    when_not_matched = None
    if "when_not_matched" in data:
        not_matched_data = data["when_not_matched"]
        when_not_matched = WhenNotMatchedClause(
            insert=not_matched_data.get("insert", {}),
        )
    
    upsert_query = UpsertQuery(
        table=table,
        alias=alias,
        columns=columns,
        values=values,
        from_query=from_query,
        on_conflict=on_conflict,
        on_duplicate_key=on_duplicate_key,
        using=using,
        match_on=match_on,
        when_matched=when_matched,
        when_not_matched=when_not_matched,
        returning=returning if isinstance(returning, list) else [returning],
    )
    
    return YQLQuery(
        operation=OperationType.UPSERT,
        upsert_query=upsert_query,
        raw=data,
    )


def _parse_insert_yql(data: dict[str, Any], imported_definitions: dict[str, Any] | None = None) -> YQLQuery:
    """Parse INSERT YQL."""
    table = data.get("table", "")
    if not table:
        raise ParseError("INSERT must have 'table'")
    
    columns = data.get("columns", [])
    values_data = data.get("values", [])
    returning = data.get("returning", [])
    
    # Parse values
    values = []
    if isinstance(values_data, list):
        for item in values_data:
            if isinstance(item, dict):
                values.append(item)
            else:
                raise ParseError(f"Invalid values format: {item}")
    elif isinstance(values_data, dict):
        values = [values_data]
    
    # Parse from_query (INSERT ... SELECT)
    from_query = None
    if "from_query" in data:
        from_query = _parse_select_query(data["from_query"])
    
    insert_query = InsertQuery(
        table=table,
        columns=columns,
        values=values,
        from_query=from_query,
        returning=returning if isinstance(returning, list) else [returning],
    )
    
    return YQLQuery(
        operation=OperationType.INSERT,
        insert_query=insert_query,
        raw=data,
    )


def _parse_update_yql(data: dict[str, Any], imported_definitions: dict[str, Any] | None = None) -> YQLQuery:
    """Parse UPDATE YQL."""
    table_data = data.get("table", "")
    
    # Parse table with optional alias
    if isinstance(table_data, dict):
        alias, table = next(iter(table_data.items()))
    elif isinstance(table_data, str):
        table = table_data
        alias = None
    else:
        raise ParseError(f"Invalid table format: {table_data}")
    
    if not table:
        raise ParseError("UPDATE must have 'table'")
    
    set_values = data.get("set", {})
    where = _parse_where_clause(data.get("where", []))
    returning = data.get("returning", [])
    
    # Parse joins
    joins = []
    if "joins" in data:
        joins = _parse_joins(data["joins"])
    
    update_query = UpdateQuery(
        table=table,
        alias=alias,
        set_values=set_values,
        joins=joins,
        where=where,
        returning=returning if isinstance(returning, list) else [returning],
    )
    
    return YQLQuery(
        operation=OperationType.UPDATE,
        update_query=update_query,
        raw=data,
    )


def _parse_delete_yql(data: dict[str, Any], imported_definitions: dict[str, Any] | None = None) -> YQLQuery:
    """Parse DELETE YQL."""
    table_data = data.get("table", "")
    
    # Parse table with optional alias
    if isinstance(table_data, dict):
        alias, table = next(iter(table_data.items()))
    elif isinstance(table_data, str):
        table = table_data
        alias = None
    else:
        raise ParseError(f"Invalid table format: {table_data}")
    
    if not table:
        raise ParseError("DELETE must have 'table'")
    
    where = _parse_where_clause(data.get("where", []))
    returning = data.get("returning", [])
    
    # Parse joins
    joins = []
    if "joins" in data:
        joins = _parse_joins(data["joins"])
    
    delete_query = DeleteQuery(
        table=table,
        alias=alias,
        joins=joins,
        where=where,
        returning=returning if isinstance(returning, list) else [returning],
    )
    
    return YQLQuery(
        operation=OperationType.DELETE,
        delete_query=delete_query,
        raw=data,
    )


def _parse_select_query(data: dict[str, Any], imported_definitions: dict[str, Any] | None = None) -> SelectQuery:
    """Parse SELECT query.
    
    Args:
        data: SELECT query data
        imported_definitions: Imported definitions dictionary (optional)
    """
    query = SelectQuery()
    
    # Parse WITH clauses
    if "with_clauses" in data:
        query.with_clauses = _parse_with_clauses(data["with_clauses"], imported_definitions)
    
    # Parse SELECT clause
    if "select" in data:
        query.select = _parse_select_clause(data["select"])
    
    # Parse FROM clause
    if "from" in data:
        query.from_clause = _parse_from_clause(data["from"])
    
    # Parse JOINs
    if "joins" in data:
        query.joins = _parse_joins(data["joins"])
    
    # Parse WHERE clause
    if "where" in data:
        query.where = _parse_where_clause(data["where"])
    
    # Parse GROUP BY
    if "group_by" in data:
        query.group_by = _parse_group_by(data["group_by"])
    
    # Parse HAVING
    if "having" in data:
        query.having = _parse_having(data["having"])
    
    # Parse ORDER BY
    if "order_by" in data:
        query.order_by = _parse_order_by(data["order_by"])
    
    # Parse LIMIT/OFFSET
    if "limit" in data:
        query.limit = data["limit"]
    if "offset" in data:
        query.offset = data["offset"]
    
    # Parse pagination
    if "pagination" in data:
        query.pagination = _parse_pagination(data["pagination"])
    
    return query


def _parse_select_clause(data: list[Any]) -> list[Column]:
    """Parse SELECT clause columns.
    
    Format: 
      - alias: expression
      - alias: column_name
    """
    columns = []
    
    for item in data:
        if isinstance(item, dict):
            # Format: {alias: expression}
            for alias, expr in item.items():
                columns.append(Column(alias=str(alias), expression=str(expr)))
        elif isinstance(item, str):
            # Simple column name (should have alias per spec, but handle gracefully)
            columns.append(Column(alias=item, expression=item))
        else:
            raise ParseError(f"Invalid SELECT column format: {item}")
    
    return columns


def _parse_from_clause(data: Any) -> FromClause:
    """Parse FROM clause.
    
    Format: alias: table_name
    """
    if isinstance(data, dict):
        # Format: {alias: table_name}
        if len(data) != 1:
            raise ParseError(f"FROM clause must have exactly one alias: {data}")
        alias, table = next(iter(data.items()))
        return FromClause(alias=str(alias), table=str(table))
    elif isinstance(data, str):
        # Legacy format: "table_name" (alias same as table)
        return FromClause(alias=data, table=data)
    else:
        raise ParseError(f"Invalid FROM clause format: {data}")


def _parse_joins(data: list[Any]) -> list[JoinClause]:
    """Parse JOIN clauses."""
    joins = []
    
    for item in data:
        if not isinstance(item, dict):
            raise ParseError(f"JOIN must be a mapping: {item}")
        
        join_type_str = item.get("type", "INNER").upper()
        try:
            join_type = JoinType[join_type_str]
        except KeyError:
            valid_types = ", ".join([jt.value for jt in JoinType])
            raise ParseError(
                f"Invalid JOIN type '{item.get('type')}'. "
                f"Valid types are: {valid_types}"
            )
        alias = item.get("alias", "")
        table = item.get("table", "")
        # YAML 1.1 parses "on:" as True (boolean), so check both "on" and True keys
        on = item.get("on") or item.get(True, "")
        additional = item.get("additional_conditions", [])
        
        if not alias or not table:
            raise ParseError(f"JOIN must have 'alias' and 'table': {item}")
        
        # Handle on conditions
        if isinstance(on, list):
            on_conditions = on
        elif on:
            on_conditions = [on]
        else:
            on_conditions = []
        
        # Handle additional conditions
        if isinstance(additional, list):
            add_conditions = additional
        elif additional:
            add_conditions = [additional]
        else:
            add_conditions = []
        
        joins.append(JoinClause(
            type=join_type,
            alias=alias,
            table=table,
            on=on_conditions,
            additional_conditions=add_conditions,
        ))
    
    return joins


def _parse_where_clause(data: list[Any] | str) -> list[str]:
    """Parse WHERE clause.
    
    Format: Array of conditions (AND-joined)
    """
    if isinstance(data, str):
        return [data]
    elif isinstance(data, list):
        conditions = []
        for item in data:
            if isinstance(item, str):
                conditions.append(item)
            elif isinstance(item, dict):
                # Complex condition (field, operator, subquery, etc.)
                conditions.append(_format_complex_condition(item))
            else:
                conditions.append(str(item))
        return conditions
    else:
        return [str(data)]


def _format_complex_condition(item: dict[str, Any]) -> str:
    """Format complex WHERE condition."""
    if "field" in item and "operator" in item:
        field = item["field"]
        operator = item["operator"]
        
        if "subquery" in item:
            # Subquery condition - return placeholder
            return f"{field} {operator} (SUBQUERY)"
        elif "value" in item:
            return f"{field} {operator} {item['value']}"
    
    # Return as string representation
    return str(item)


def _parse_group_by(data: list[Any] | str) -> list[str]:
    """Parse GROUP BY clause."""
    if isinstance(data, str):
        return [data]
    elif isinstance(data, list):
        return [str(item) for item in data]
    else:
        return [str(data)]


def _parse_having(data: list[Any] | str) -> list[str]:
    """Parse HAVING clause."""
    if isinstance(data, str):
        return [data]
    elif isinstance(data, list):
        return [str(item) for item in data]
    else:
        return [str(data)]


def _parse_order_by(data: list[Any]) -> list[OrderByClause]:
    """Parse ORDER BY clause.
    
    Supports multiple formats:
    1. Full form: {field: "name", direction: "ASC"}
    2. Short form: {name: "DESC"}
    3. String: "name" (defaults to ASC)
    """
    order_by = []
    
    for item in data:
        if isinstance(item, dict):
            # Check if it's short form: {field_name: "DESC"}
            # Short form has exactly one key that is not "field" or "direction"
            keys = list(item.keys())
            if "field" in keys:
                # Full form: {field: "name", direction: "ASC"}
                field = item.get("field", "")
                direction_str = item.get("direction", "ASC").upper()
            elif len(keys) == 1 and keys[0] not in ("field", "direction"):
                # Short form: {field_name: "DESC"}
                field = keys[0]
                direction_str = str(item[field]).upper()
            else:
                # Invalid format
                raise ParseError(f"Invalid ORDER BY format: {item}. Use {{field: 'name', direction: 'ASC'}} or {{name: 'DESC'}}")
            
            try:
                direction = SortDirection[direction_str]
            except KeyError:
                valid_directions = ", ".join([sd.value for sd in SortDirection])
                raise ParseError(
                    f"Invalid sort direction '{direction_str}'. "
                    f"Valid directions are: {valid_directions}"
                )
            order_by.append(OrderByClause(
                field=field,
                direction=direction,
            ))
        elif isinstance(item, str):
            # Simple field name (ASC by default)
            order_by.append(OrderByClause(field=item, direction=SortDirection.ASC))
        else:
            raise ParseError(f"Invalid ORDER BY format: {item}")
    
    return order_by


def _load_imports(
    imports: list[str],
    base_path: Path,
    current_file: Path | None = None,
    depth: int = 0,
    max_depth: int = 3,
    max_imports: int = 10,
    visited: set[str] | None = None,
    import_chain: list[str] | None = None,
) -> dict[str, Any]:
    """Load imported YQL files with limits and circular dependency detection.
    
    Args:
        imports: List of import paths (relative to fixtures directory)
        base_path: Base path for resolving relative imports
        current_file: Current file being parsed (for error reporting)
        depth: Current import depth (default: 0)
        max_depth: Maximum import depth (default: 3)
        max_imports: Maximum number of imports per file (default: 10)
        visited: Set of visited import paths (for circular dependency detection)
        import_chain: List of import paths in current chain (for error reporting)
        
    Returns:
        Dictionary mapping import names to their definitions
        
    Raises:
        ParseError: If import limits are exceeded or circular dependency is detected
    """
    if visited is None:
        visited = set()
    if import_chain is None:
        import_chain = []
    
    # Check import count limit
    if len(imports) > max_imports:
        raise ParseError(
            f"Too many imports: {len(imports)} (maximum: {max_imports})",
            category="logic_error",
            details={"file": str(current_file) if current_file else None, "import_count": len(imports)},
        )
    
    # Check depth limit
    # depth starts at 0, so with max_depth=3:
    # depth 0 (root) -> 1 -> 2 -> 3 (max allowed) -> 4 (should fail)
    # depth >= max_depth でエラー（depth=3, max_depth=3ならエラー）
    if depth >= max_depth:
        raise ParseError(
            f"Import depth exceeds maximum ({max_depth})",
            category="logic_error",
            details={
                "file": str(current_file) if current_file else None,
                "depth": depth,
                "max_depth": max_depth,
                "import_chain": import_chain,
            },
        )
    
    imported_definitions = {}
    
    # Find fixtures directory (parent of base_path if base_path is in a test fixture directory)
    fixtures_dir = base_path.parent if base_path.name != "fixtures" else base_path
    
    for import_path in imports:
        # Resolve import path
        if import_path.startswith("/"):
            # Absolute path
            full_path = Path(import_path)
        else:
            # Relative path: try fixtures_dir first, then base_path
            # Check if import_path is a directory name (e.g., "test_import_customer_summary")
            candidate_path = fixtures_dir / import_path
            if candidate_path.is_dir():
                # If it's a directory, look for before.yql inside it
                full_path = candidate_path / "before.yql"
            else:
                # Otherwise, treat it as a file path
                full_path = candidate_path
                if not full_path.exists():
                    # Fallback to base_path
                    full_path = base_path / import_path
        
        # Add .yql extension if not present and it's not already a directory with before.yql
        if not full_path.suffix and not full_path.name.endswith(".yql"):
            full_path = full_path.with_suffix(".yql")
        
        if not full_path.exists():
            raise ParseError(
                f"Import file not found: {full_path}",
                category="logic_error",
                details={
                    "file": str(current_file) if current_file else None,
                    "import_path": import_path,
                    "import_chain": import_chain,
                },
            )
        
        # Check depth limit before loading the file
        # This ensures we check before processing nested imports
        if depth >= max_depth:
            raise ParseError(
                f"Import depth exceeds maximum ({max_depth})",
                category="logic_error",
                details={
                    "file": str(current_file) if current_file else None,
                    "depth": depth,
                    "max_depth": max_depth,
                    "import_chain": import_chain,
                    "import_path": import_path,
                },
            )
        
        # Check for circular dependency
        full_path_str = str(full_path.resolve())
        if full_path_str in visited:
            cycle = import_chain + [full_path_str]
            raise ParseError(
                f"Circular dependency detected: {' -> '.join(cycle)} -> {full_path_str}",
                category="logic_error",
                details={
                    "file": str(current_file) if current_file else None,
                    "import_path": import_path,
                    "import_chain": import_chain,
                    "circular_path": cycle + [full_path_str],
                },
            )
        
        # Mark as visited and add to chain
        visited.add(full_path_str)
        new_chain = import_chain + [full_path_str]
        
        # Load and parse imported file
        try:
            content = full_path.read_text(encoding="utf-8")
            imported_data = yaml.safe_load(content)
            
            if not isinstance(imported_data, dict):
                raise ParseError(
                    f"Imported file must be a YAML mapping: {full_path}",
                    category="syntax_error",
                    details={"file": str(full_path), "import_chain": new_chain},
                )
            
            # Extract name from imported file
            name = imported_data.get("name", full_path.stem)
            
            # Recursively load nested imports
            nested_imports = imported_data.get("imports", [])
            if nested_imports:
                # Recursive call with depth+1 (depth limit is checked at the start of _load_imports)
                nested_definitions = _load_imports(
                    nested_imports,
                    full_path.parent,
                    current_file=full_path,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_imports=max_imports,
                    visited=visited.copy(),  # Copy to allow parallel imports
                    import_chain=new_chain,
                )
                # Merge nested definitions (with name collision check)
                for nested_name, nested_def in nested_definitions.items():
                    if nested_name in imported_definitions:
                        raise ParseError(
                            f"Duplicate import name '{nested_name}' in import chain",
                            category="logic_error",
                            details={
                                "file": str(current_file) if current_file else None,
                                "import_chain": new_chain,
                                "duplicate_name": nested_name,
                            },
                        )
                    imported_definitions[nested_name] = nested_def
            
            imported_definitions[name] = imported_data
            
        except yaml.YAMLError as e:
            raise ParseError(
                f"Failed to parse import file {full_path}: {e}",
                category="syntax_error",
                details={"file": str(full_path), "import_chain": new_chain},
            ) from e
        except ParseError:
            # Re-raise ParseError with updated context
            raise
        except Exception as e:
            raise ParseError(
                f"Error loading import file {full_path}: {e}",
                category="logic_error",
                details={"file": str(full_path), "import_chain": new_chain},
            ) from e
    
    return imported_definitions


def _apply_parameters(data: Any, provided_params: dict[str, Any], default_params: dict[str, Any] | None = None) -> Any:
    """Apply parameters to YQL data structure.
    
    Replaces parameter placeholders like #{paramName} with provided values.
    
    Args:
        data: YQL data structure (dict, list, str, etc.)
        provided_params: Parameters provided by the user
        default_params: Default parameters from the definition (optional)
    
    Returns:
        Data structure with parameters applied
    """
    if default_params is None:
        default_params = {}
    
    # Merge default and provided parameters (provided takes precedence)
    params = {**default_params, **provided_params}
    
    if isinstance(data, dict):
        # Recursively apply to dictionary values
        return {key: _apply_parameters(value, provided_params, default_params) for key, value in data.items()}
    elif isinstance(data, list):
        # Recursively apply to list items
        return [_apply_parameters(item, provided_params, default_params) for item in data]
    elif isinstance(data, str):
        # Replace parameter placeholders in strings
        result = data
        for param_name, param_value in params.items():
            # Replace #{paramName} with the value
            placeholder = f"#{{{param_name}}}"
            if placeholder in result:
                # Format the value appropriately
                if isinstance(param_value, str):
                    # String literal - add quotes
                    formatted_value = f"'{param_value}'"
                else:
                    # Number, bool, etc. - convert to string as-is
                    formatted_value = str(param_value)
                result = result.replace(placeholder, formatted_value)
        
        # Also handle ${paramArray} for array expansion (pass through as-is for now)
        # This will be handled by SQL libraries later
        for param_name, param_value in params.items():
            placeholder = f"${{{param_name}}}"
            if placeholder in result and isinstance(param_value, list):
                # Array expansion - pass through as-is (will be handled by SQL libraries)
                pass
        
        # Also handle @{macro} for macro expansion (pass through as-is for now)
        # This will be handled by SQL libraries later
        return result
    else:
        # For other types (int, bool, etc.), return as-is
        return data


def _parse_with_clauses(data: dict[str, Any], imported_definitions: dict[str, Any] | None = None) -> list[WithClause]:
    """Parse WITH clauses (CTEs).
    
    Args:
        data: WITH clauses data
        imported_definitions: Imported definitions dictionary (optional)
    """
    if imported_definitions is None:
        imported_definitions = {}
    
    with_clauses = []
    
    for name, definition in data.items():
        if isinstance(definition, dict):
            if "using" in definition:
                # Reference to imported definition
                import_name = definition["using"]
                if import_name not in imported_definitions:
                    raise ParseError(f"Imported definition '{import_name}' not found. Available: {list(imported_definitions.keys())}")
                
                imported_def = imported_definitions[import_name]
                if "select_definition" not in imported_def:
                    raise ParseError(f"Imported definition '{import_name}' does not contain 'select_definition'")
                
                # Get parameters if provided
                parameters = definition.get("parameters", {})
                
                # Parse the imported SELECT definition
                select_def = imported_def["select_definition"]
                
                # Apply parameters if any
                if parameters:
                    select_def = _apply_parameters(select_def, parameters, imported_def.get("parameters", {}))
                
                query = _parse_select_query(select_def)
                with_clauses.append(WithClause(name=name, query=query))
            else:
                # Inline definition
                query = _parse_select_query(definition)
                with_clauses.append(WithClause(name=name, query=query))
        else:
            raise ParseError(f"Invalid WITH clause definition: {definition}")
    
    return with_clauses


def _parse_pagination(data: dict[str, Any]) -> Pagination:
    """Parse pagination settings."""
    page = data.get("page", "#{page:1}")
    per_page = data.get("per_page", "#{per_page:20}")
    
    return Pagination(page=str(page), per_page=str(per_page))

