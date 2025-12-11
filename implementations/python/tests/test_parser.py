"""Tests for YQL Parser."""

import pytest

from yql import parse
from yql.ast import JoinType, OperationType, SortDirection


class TestParseBasic:
    """Basic parsing tests."""
    
    def test_parse_simple_select(self):
        """Test parsing simple SELECT."""
        yql = """
query:
  select:
    - id: c.id
    - name: c.name
  from:
    c: customers
"""
        result = parse(yql)
        
        assert result.operation == OperationType.SELECT
        assert result.query is not None
        assert len(result.query.select) == 2
        assert result.query.select[0].alias == "id"
        assert result.query.select[0].expression == "c.id"
        assert result.query.from_clause.alias == "c"
        assert result.query.from_clause.table == "customers"
    
    def test_parse_direct_query_format(self):
        """Test parsing direct query format (without 'query' wrapper)."""
        yql = """
select:
  - id: c.id
from:
  c: customers
"""
        result = parse(yql)
        
        assert result.operation == OperationType.SELECT
        assert result.query is not None
        assert len(result.query.select) == 1


class TestParseWhere:
    """WHERE clause parsing tests."""
    
    def test_parse_single_condition(self):
        """Test parsing single WHERE condition."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  where:
    - "c.status = 'active'"
"""
        result = parse(yql)
        
        assert len(result.query.where) == 1
        assert result.query.where[0] == "c.status = 'active'"
    
    def test_parse_multiple_conditions(self):
        """Test parsing multiple WHERE conditions (AND)."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  where:
    - "c.status = 'active'"
    - "c.age > 18"
"""
        result = parse(yql)
        
        assert len(result.query.where) == 2


class TestParseJoin:
    """JOIN clause parsing tests."""
    
    def test_parse_inner_join(self):
        """Test parsing INNER JOIN."""
        yql = """
query:
  select:
    - customer_id: c.id
    - order_id: o.id
  from:
    c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
"""
        result = parse(yql)
        
        assert len(result.query.joins) == 1
        assert result.query.joins[0].type == JoinType.INNER
        assert result.query.joins[0].alias == "o"
        assert result.query.joins[0].table == "orders"
    
    def test_parse_left_join(self):
        """Test parsing LEFT JOIN."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.id = o.customer_id"
"""
        result = parse(yql)
        
        assert result.query.joins[0].type == JoinType.LEFT


class TestParseGroupBy:
    """GROUP BY parsing tests."""
    
    def test_parse_group_by(self):
        """Test parsing GROUP BY."""
        yql = """
query:
  select:
    - customer_id: c.customer_id
    - order_count: "COUNT(*)"
  from:
    c: customers
  group_by:
    - c.customer_id
"""
        result = parse(yql)
        
        assert len(result.query.group_by) == 1
        assert result.query.group_by[0] == "c.customer_id"


class TestParseOrderBy:
    """ORDER BY parsing tests."""
    
    def test_parse_order_by_asc(self):
        """Test parsing ORDER BY ASC."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  order_by:
    - field: c.created_at
      direction: ASC
"""
        result = parse(yql)
        
        assert len(result.query.order_by) == 1
        assert result.query.order_by[0].field == "c.created_at"
        assert result.query.order_by[0].direction == SortDirection.ASC
    
    def test_parse_order_by_desc(self):
        """Test parsing ORDER BY DESC."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  order_by:
    - field: c.created_at
      direction: DESC
"""
        result = parse(yql)
        
        assert result.query.order_by[0].direction == SortDirection.DESC


class TestParseLimitOffset:
    """LIMIT/OFFSET parsing tests."""
    
    def test_parse_limit(self):
        """Test parsing LIMIT."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  limit: 10
"""
        result = parse(yql)
        
        assert result.query.limit == 10
    
    def test_parse_limit_offset(self):
        """Test parsing LIMIT and OFFSET."""
        yql = """
query:
  select:
    - id: c.id
  from:
    c: customers
  limit: 10
  offset: 20
"""
        result = parse(yql)
        
        assert result.query.limit == 10
        assert result.query.offset == 20


class TestParsePagination:
    """Pagination parsing tests."""
    
    def test_parse_pagination(self):
        """Test parsing pagination."""
        yql = """
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  select:
    - id: c.id
  from:
    c: customers
"""
        result = parse(yql)
        
        assert result.query.pagination is not None
        assert result.query.pagination.page == "#{page:1}"
        assert result.query.pagination.per_page == "#{per_page:20}"


class TestParseWithClause:
    """WITH clause (CTE) parsing tests."""
    
    def test_parse_single_cte(self):
        """Test parsing single CTE."""
        yql = """
query:
  with_clauses:
    active_customers:
      select:
        - id: c.id
        - name: c.name
      from:
        c: customers
      where:
        - "c.status = 'active'"
  select:
    - id: ac.id
    - name: ac.name
  from:
    ac: active_customers
"""
        result = parse(yql)
        
        assert len(result.query.with_clauses) == 1
        assert result.query.with_clauses[0].name == "active_customers"
        assert result.query.with_clauses[0].query is not None

