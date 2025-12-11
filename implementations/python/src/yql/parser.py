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
    OperationType,
    OrderByClause,
    Pagination,
    SelectQuery,
    SortDirection,
    UpdateQuery,
    WithClause,
    YQLQuery,
)


class ParseError(Exception):
    """YQL parse error."""
    pass


def parse(yql_content: str) -> YQLQuery:
    """Parse YQL string into AST.
    
    Args:
        yql_content: YQL content as string (YAML format)
        
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
    
    return _parse_yql(data)


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
    return parse(content)


def _parse_yql(data: dict[str, Any]) -> YQLQuery:
    """Parse top-level YQL structure."""
    # Determine operation type
    operation_str = data.get("operation", "").lower()
    
    # Check for DML operations
    if operation_str == "insert" or "values" in data:
        return _parse_insert_yql(data)
    elif operation_str == "update" or ("set" in data and "select" not in data):
        return _parse_update_yql(data)
    elif operation_str == "delete" or (operation_str == "delete" and "table" in data):
        return _parse_delete_yql(data)
    
    # Default to SELECT
    if "query" in data:
        query_data = data["query"]
    elif "select" in data or "with_clauses" in data:
        query_data = data
    else:
        raise ParseError("YQL must have 'query', 'select', or DML operation")
    
    query = _parse_select_query(query_data)
    
    return YQLQuery(
        operation=OperationType.SELECT,
        select_query=query,
        raw=data,
    )


def _parse_insert_yql(data: dict[str, Any]) -> YQLQuery:
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


def _parse_update_yql(data: dict[str, Any]) -> YQLQuery:
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


def _parse_delete_yql(data: dict[str, Any]) -> YQLQuery:
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


def _parse_select_query(data: dict[str, Any]) -> SelectQuery:
    """Parse SELECT query."""
    query = SelectQuery()
    
    # Parse WITH clauses
    if "with_clauses" in data:
        query.with_clauses = _parse_with_clauses(data["with_clauses"])
    
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
        
        join_type = JoinType[item.get("type", "INNER").upper()]
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
    """Parse ORDER BY clause."""
    order_by = []
    
    for item in data:
        if isinstance(item, dict):
            field = item.get("field", "")
            direction = item.get("direction", "ASC").upper()
            order_by.append(OrderByClause(
                field=field,
                direction=SortDirection[direction],
            ))
        elif isinstance(item, str):
            # Simple field name (ASC by default)
            order_by.append(OrderByClause(field=item, direction=SortDirection.ASC))
        else:
            raise ParseError(f"Invalid ORDER BY format: {item}")
    
    return order_by


def _parse_with_clauses(data: dict[str, Any]) -> list[WithClause]:
    """Parse WITH clauses (CTEs)."""
    with_clauses = []
    
    for name, definition in data.items():
        if isinstance(definition, dict):
            if "using" in definition:
                # Reference to imported definition - not implemented yet
                raise ParseError("'using' import reference not yet implemented")
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

