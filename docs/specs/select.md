# YQL SELECT文 変換ルール仕様書

## 1. 概要

このドキュメントは、YQLのSELECT文を各データベース方言のSQLに変換する際のルールを定義します。

### 1.1 対応データベース

- PostgreSQL
- MySQL
- SQL Server (MSSQL)
- Oracle

### 1.2 変換の基本方針

- YQLの抽象構文を各DBの標準SQL構文に変換
- 可能な限り標準SQL準拠の構文を使用
- DB固有の最適化は最小限に留める
- パラメーターバインディングは必ずPreparedStatement形式を使用
- **FROM句でのサブクエリは禁止。WITH句（CTE）を使用することで可読性と再利用性を向上**
- WHERE句やSELECT句内のサブクエリ（EXISTS、IN、スカラーサブクエリ等）は許可

## 2. SELECT句の変換

### 2.1 基本カラム選択

#### YQL構文
```yaml
select:
  - alias_name: column_name        # エイリアス付きカラム（エイリアス必須）
  - alias_name: table_alias.column # エイリアス付きテーブル.カラム（エイリアス必須）
  - alias_name: "*"                # 全カラム選択（エイリアス必須）
  - alias_name: "table_alias.*"    # 特定テーブルの全カラム（エイリアス必須）
  - alias_name: "expression"       # エイリアス付き式（エイリアス必須）
```

#### 変換ルール

| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `alias_name: column_name` | `column_name AS alias_name` | `column_name AS alias_name` | `column_name AS alias_name` | `column_name AS alias_name` |
| `alias_name: table_alias.column` | `table_alias.column AS alias_name` | `table_alias.column AS alias_name` | `table_alias.column AS alias_name` | `table_alias.column AS alias_name` |
| `alias_name: "*"` | `* AS alias_name` | `* AS alias_name` | `* AS alias_name` | `* AS alias_name` |
| `alias_name: "table_alias.*"` | `table_alias.* AS alias_name` | `table_alias.* AS alias_name` | `table_alias.* AS alias_name` | `table_alias.* AS alias_name` |
| `alias_name: "expression"` | `expression AS alias_name` | `expression AS alias_name` | `expression AS alias_name` | `expression AS alias_name` |

**生成例:**
```sql
-- YQL: alias_name: column_name
-- PostgreSQL/MySQL/SQL Server: column_name AS alias_name

-- YQL: total_sales: "SUM(amount)"
-- PostgreSQL/MySQL/SQL Server: SUM(amount) AS total_sales

-- YQL: customer_name: c.name
-- PostgreSQL/MySQL/SQL Server: c.name AS customer_name
```

**注意事項:**
- **エイリアスは必須です**（パーサーの実装を簡素化するため）
- カラム名は引用符で囲まない（識別子として扱う）
- 予約語の場合は必要に応じて引用符で囲む（DB依存）
- エイリアス名に予約語を使用する場合は引用符で囲む
- エイリアス名にスペースや特殊文字を含む場合は引用符で囲む
- エイリアスは先頭に記述する形式（`alias_name: value`）

### 2.1.1 SELECT句内のスカラーサブクエリ

**SELECT句内のスカラーサブクエリ（相関サブクエリ）は許可されています。**

#### YQL構文
```yaml
select:
  - customer_id: customer_id
  - name: name
  - avg_order_amount: "(SELECT AVG(total_amount) FROM orders WHERE customer_id = c.customer_id)"
  - last_order_date: "(SELECT MAX(order_date) FROM orders WHERE customer_id = c.customer_id)"
```

#### 変換ルール

**全DB共通:**
```sql
SELECT 
  customer_id AS customer_id,
  name AS name,
  (SELECT AVG(total_amount) FROM orders WHERE customer_id = c.customer_id) AS avg_order_amount,
  (SELECT MAX(order_date) FROM orders WHERE customer_id = c.customer_id) AS last_order_date
FROM customers c
```

**注意事項:**
- SELECT句内のスカラーサブクエリは許可されています
- 相関サブクエリ（外側のクエリのカラムを参照するサブクエリ）として使用可能
- 単一行を返すサブクエリのみ使用可能
- パフォーマンスに注意が必要な場合があります

### 2.2 式の記述

#### YQL構文
```yaml
select:
  - total: "column1 + column2"            # エイリアス付き算術演算（エイリアス必須）
  - full_name: "CONCAT(first_name, ' ', last_name)"  # エイリアス付き関数呼び出し（エイリアス必須）
  - result: "CASE WHEN condition THEN value END"  # エイリアス付きCASE式（エイリアス必須）
  - text_value: "column::text"            # エイリアス付き型キャスト（エイリアス必須）
```

#### 変換ルール

**エイリアス付き式の変換:**
| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `alias: "expression"` | `expression AS alias` | `expression AS alias` | `expression AS alias` | `expression AS alias` |
| `full_name: "CONCAT(a, b)"` | `CONCAT(a, b) AS full_name` | `CONCAT(a, b) AS full_name` | `CONCAT(a, b) AS full_name` | `CONCAT(a, b) AS full_name` |
| `total: "column1 + column2"` | `column1 + column2 AS total` | `column1 + column2 AS total` | `column1 + column2 AS total` | `column1 + column2 AS total` |

**算術演算子:**
- `+`, `-`, `*`, `/`, `%` は全DB共通

**文字列結合:**
| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` |
| `a \|\| b` | `a \|\| b` | `CONCAT(a, b)` | `a + b` | `a \|\| b` |

**型キャスト:**
| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `column::text` | `column::text` | `CAST(column AS CHAR)` | `CAST(column AS VARCHAR)` | `CAST(column AS VARCHAR2)` |
| `column::integer` | `column::integer` | `CAST(column AS SIGNED)` | `CAST(column AS INT)` | `CAST(column AS NUMBER)` |
| `column::decimal` | `column::decimal` | `CAST(column AS DECIMAL)` | `CAST(column AS DECIMAL)` | `CAST(column AS NUMBER)` |

**注意事項:**
- **エイリアスは必須です**（パーサーの実装を簡素化するため）
- カラム句での分岐条件は禁止（WHERE句のみで使用可能）
- 式内でパラメータを使用する場合は `#{paramName}` 形式
- エイリアス付き式は `alias_name: "expression"` 形式で記述（エイリアスを先頭に記述）

### 2.3 集計関数

#### YQL構文
```yaml
select:
  - count_all: "COUNT(*)"                           # エイリアス付き集計関数
  - count_col: "COUNT(column_name)"                 # エイリアス付き集計関数
  - count_distinct: "COUNT(DISTINCT column_name)"   # エイリアス付き集計関数
  - sum_col: "SUM(column_name)"                    # エイリアス付き集計関数
  - avg_col: "AVG(column_name)"                    # エイリアス付き集計関数
  - min_col: "MIN(column_name)"                    # エイリアス付き集計関数
  - max_col: "MAX(column_name)"                    # エイリアス付き集計関数
  - order_count: "COUNT(order_id)"                  # エイリアス付き集計関数
  - total_amount: "SUM(amount)"                     # エイリアス付き集計関数
```

#### 変換ルール

**エイリアス付き集計関数の変換:**
| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `alias: "COUNT(*)"` | `COUNT(*) AS alias` | `COUNT(*) AS alias` | `COUNT(*) AS alias` | `COUNT(*) AS alias` |
| `alias: "SUM(column)"` | `SUM(column) AS alias` | `SUM(column) AS alias` | `SUM(column) AS alias` | `SUM(column) AS alias` |
| `order_count: "COUNT(order_id)"` | `COUNT(order_id) AS order_count` | `COUNT(order_id) AS order_count` | `COUNT(order_id) AS order_count` | `COUNT(order_id) AS order_count` |
| `total_amount: "SUM(amount)"` | `SUM(amount) AS total_amount` | `SUM(amount) AS total_amount` | `SUM(amount) AS total_amount` | `SUM(amount) AS total_amount` |

**集計関数の構文（全DB共通）:**
| 関数 | PostgreSQL | MySQL | SQL Server | Oracle |
|------|-----------|-------|------------|--------|
| `COUNT(*)` | `COUNT(*)` | `COUNT(*)` | `COUNT(*)` | `COUNT(*)` |
| `COUNT(column)` | `COUNT(column)` | `COUNT(column)` | `COUNT(column)` | `COUNT(column)` |
| `COUNT(DISTINCT column)` | `COUNT(DISTINCT column)` | `COUNT(DISTINCT column)` | `COUNT(DISTINCT column)` | `COUNT(DISTINCT column)` |
| `SUM(column)` | `SUM(column)` | `SUM(column)` | `SUM(column)` | `SUM(column)` |
| `AVG(column)` | `AVG(column)` | `AVG(column)` | `AVG(column)` | `AVG(column)` |
| `MIN(column)` | `MIN(column)` | `MIN(column)` | `MIN(column)` | `MIN(column)` |
| `MAX(column)` | `MAX(column)` | `MAX(column)` | `MAX(column)` | `MAX(column)` |

**注意事項:**
- 集計関数を使用する場合はGROUP BY句が必須（集計対象カラム以外）
- エイリアス付き集計関数は `alias_name: "FUNCTION(...)"` 形式で記述（エイリアスを先頭に記述）

### 2.4 CASE式

#### YQL構文
```yaml
select:
  - customer_segment:                              # エイリアスを先頭に記述
      case_when:
        - condition: "annual_sales >= 1000000"
          then: "Enterprise"
        - condition: "annual_sales >= 100000"
          then: "Business"
        - condition: "annual_sales >= 10000"
          then: "Professional"
        - default: "Starter"
```

#### 変換ルール

**全DB共通:**
```sql
CASE
  WHEN annual_sales >= 1000000 THEN 'Enterprise'
  WHEN annual_sales >= 100000 THEN 'Business'
  WHEN annual_sales >= 10000 THEN 'Professional'
  ELSE 'Starter'
END AS customer_segment
```

**注意事項:**
- CASE式内の条件はWHERE句と同じ形式で記述
- THEN句とELSE句の型は統一する必要がある

## 3. FROM句の変換

### 3.1 テーブル（駆動表）

#### YQL構文
```yaml
from: alias: table_name            # エイリアス必須（エイリアスを先頭に記述）
from: alias: "schema.table_name"   # スキーマ付き（エイリアス必須）
```

**注意: FROM句ではエイリアスが必須です。**

#### 変換ルール

| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `alias: table_name` | `table_name alias` | `table_name alias` | `table_name alias` | `table_name alias` |
| `alias: "schema.table"` | `schema.table alias` | `schema.table alias` | `schema.table alias` | `schema.table alias` |

**生成例:**
```sql
-- YQL: from: c: customers
-- PostgreSQL/MySQL/SQL Server: FROM customers c

-- YQL: from: o: "sales.orders"
-- PostgreSQL/MySQL/SQL Server: FROM sales.orders o
```

**注意事項:**
- **エイリアスは必須です**（パーサー実装の一貫性のため）
- テーブル名に予約語を使用する場合は引用符で囲む
- スキーマ名は必要に応じて引用符で囲む
- エイリアスは先頭に記述する形式（`alias: table_name`）

### 3.2 FROM句でのサブクエリ（禁止）

**FROM句でのサブクエリは禁止されています。代わりにWITH句（CTE）を使用してください。**

**注意事項:**
- FROM句でのサブクエリは使用不可
- 代わりにWITH句（CTE）を使用することで、クエリの可読性と再利用性が向上します
- **WITH句（CTE）の詳細な構文と変換ルールについては、11章を参照してください**

## 4. JOIN句の変換

### 4.1 JOINタイプ

#### YQL構文
```yaml
joins:
  - type: INNER | LEFT | RIGHT | FULL | CROSS
    alias: alias_name              # エイリアス（推奨：先頭に記述）
    table: table_name              # テーブル名
    on: "from_alias.from_column = alias_name.join_column"              # 単一条件（文字列形式、テーブルエイリアス必須）
    # または
    on:                              # 複数条件（配列形式）
      - "from_alias.from_column = alias_name.join_column"
      - "from_alias.from_column2 = alias_name.join_column2"
      - "alias_name.join_column3 > value"
    additional_conditions:           # 追加条件（オプション、テーブルエイリアス推奨）
      - "alias_name.column_name != 'value'"      # フィルタリング条件の例
      - "alias_name.column_name2 > 0"            # 複数の条件を配列で記述
```

#### 変換ルール

| YQL JOINタイプ | PostgreSQL | MySQL | SQL Server |
|---------------|-----------|-------|------------|--------|
| `INNER` | `INNER JOIN` | `INNER JOIN` | `INNER JOIN` | `INNER JOIN` |
| `LEFT` | `LEFT JOIN` | `LEFT JOIN` | `LEFT JOIN` | `LEFT JOIN` |
| `RIGHT` | `RIGHT JOIN` | `RIGHT JOIN` | `RIGHT JOIN` | `RIGHT JOIN` |
| `FULL` | `FULL OUTER JOIN` | `FULL OUTER JOIN` | `FULL OUTER JOIN` | `FULL OUTER JOIN` |
| `CROSS` | `CROSS JOIN` | `CROSS JOIN` | `CROSS JOIN` | `CROSS JOIN` |

**生成例:**

**単一条件:**
```sql
-- YQL:
-- joins:
--   - type: LEFT
--     alias: o
--     table: orders
--     on: "c.customer_id = o.customer_id"

-- PostgreSQL/MySQL/SQL Server:
LEFT JOIN orders o
  ON c.customer_id = o.customer_id
```

**複数条件（配列形式）:**
```sql
-- YQL:
-- joins:
--   - type: LEFT
--     alias: o
--     table: orders
--     on:
--       - "c.customer_id = o.customer_id"
--       - "c.region = o.region"
--       - "o.status = 'active'"

-- PostgreSQL/MySQL/SQL Server:
LEFT JOIN orders o
  ON c.customer_id = o.customer_id
  AND c.region = o.region
  AND o.status = 'active'
```

**追加条件との組み合わせ:**
```sql
-- YQL:
-- joins:
--   - type: LEFT
--     alias: o
--     table: orders
--     on: "c.customer_id = o.customer_id"
--     additional_conditions:
--       - "o.status != 'cancelled'"
--       - "o.total_amount > 0"

-- PostgreSQL/MySQL/SQL Server:
LEFT JOIN orders o
  ON c.customer_id = o.customer_id
  AND o.status != 'cancelled'
  AND o.total_amount > 0
```

**`additional_conditions`の用途:**
- `on`句：テーブル間の結合条件（主に等価結合や比較条件）
- `additional_conditions`：結合時のフィルタリング条件（結合する行を制限する条件）
- 実質的には`on`句の配列形式と同じ動作ですが、意図を明確にするために使い分け可能
- 例：結合条件（`on`）は`c.customer_id = o.customer_id`、フィルタ条件（`additional_conditions`）は`o.status != 'cancelled'`

**注意事項:**
- `on`句は必須（CROSS JOINを除く）
- `on`句は文字列形式（単一条件）または配列形式（複数条件）で記述可能
- `on`句の配列内の条件は`AND`で結合される
- `additional_conditions`は`AND`で結合され、`on`句の条件に追加される
- `additional_conditions`は`on`句の配列形式で代用可能（`on`句にすべての条件を記述しても可）
- **JOIN条件ではテーブルエイリアスを付けることを強く推奨**（例: `c.customer_id = o.customer_id`）
- テーブルエイリアスを付けることで、どのテーブルのカラムかが明確になり、可読性と保守性が向上します
- JOINの順序はYQLの記述順序を保持
- エイリアスは先頭に記述する形式（`alias: alias_name, table: table_name`）

### 4.2 複数JOIN

#### YQL構文
```yaml
joins:
  - type: INNER
    alias: o
    table: orders
    on: "c.customer_id = o.customer_id"
  - type: LEFT
    alias: oi
    table: order_items
    on:
      - "o.order_id = oi.order_id"
      - "oi.quantity > 0"
  - type: LEFT
    alias: p
    table: products
    on: "oi.product_id = p.product_id"
```

#### 変換ルール

**全DB共通:**
```sql
INNER JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.product_id
```

## 6. WHERE句の変換

### 6.1 基本条件

#### YQL構文
```yaml
where:
  - "condition1"                     # 基本条件（ANDで結合）
  - "condition2"                     # AND条件として結合
  - "condition3 OR condition4"       # OR条件（文字列内で記述）
  - "condition5 AND (condition6 OR condition7)"  # 複雑な条件も文字列内で記述
```

#### 変換ルール

**全DB共通:**
```sql
-- YQL:
-- where:
--   - "c.status = 'active'"
--   - "c.created_at >= DATE('now', '-1 year')"
--   - "c.customer_type = 'premium' OR c.annual_revenue >= 1000000"
--   - "c.region = 'tokyo' OR c.region = 'osaka'"

-- PostgreSQL/MySQL/SQL Server:
WHERE c.status = 'active'
  AND c.created_at >= DATE('now', '-1 year')
  AND (c.customer_type = 'premium' OR c.annual_revenue >= 1000000)
  AND (c.region = 'tokyo' OR c.region = 'osaka')
```

**結合ルール:**
- 配列内の条件は、すべて`AND`で結合されます
- `OR`条件を記述する場合は、文字列内で`OR`を使用します
- 複雑な条件（括弧を含む）も文字列内で記述します
- パーサーの実装を簡素化するため、この形式を採用しています

**注意事項:**
- 複数の条件はデフォルトで`AND`で結合されます
- `OR`条件を記述する場合は、文字列内で`OR`を使用します
- 括弧を含む複雑な条件も文字列内で記述可能です

### 6.2 パラメータによる分岐条件

**重要:** パラメータによる分岐は、テンプレートエンジン（MyBatis、JinjaSQL等）の形式として出力されます。動的SQLの生成はテンプレートエンジンに任せます。

#### YQL構文
```yaml
where:
  - "c.status = 'active'"            # 固定条件
  - if: "${name_filter}"
    then: "c.name ILIKE #{nameFilter}"
  - if: "${customer_type} == 'premium'"
    then: "c.annual_revenue >= 1000000"
```

#### 変換ルール

**MyBatis XML生成例:**
```xml
<where>
  c.status = 'active'
  <if test="nameFilter != null">
    AND c.name ILIKE #{nameFilter}
  </if>
  <if test="customerType != null and customerType == 'premium'">
    AND c.annual_revenue >= 1000000
  </if>
</where>
```

**JinjaSQL生成例:**
```sql
WHERE c.status = 'active'
{% if name_filter %}
  AND c.name ILIKE {{ name_filter }}
{% endif %}
{% if customer_type == 'premium' %}
  AND c.annual_revenue >= 1000000
{% endif %}
```

**注意事項:**
- パラメータによる分岐はWHERE句でのみ許可
- カラム句（SELECT）での分岐は禁止
- パラメータは`#{paramName}`形式でバインド
- **動的SQLの生成はテンプレートエンジンに任せます**（YQLパーサーはテンプレート形式を出力するのみ）

### 6.3 比較演算子

#### YQL構文
```yaml
where:
  - "column = value"
  - "column != value"
  - "column > value"
  - "column >= value"
  - "column < value"
  - "column <= value"
  - "column IN (value1, value2)"
  - "column NOT IN (value1, value2)"
  - "column IS NULL"
  - "column IS NOT NULL"
  - "column LIKE 'pattern'"
  - "column BETWEEN value1 AND value2"
```

#### 変換ルール

| 演算子 | PostgreSQL | MySQL | SQL Server |
|--------|-----------|-------|------------|
| `=` | `=` | `=` | `=` |
| `!=` | `!=` | `!=` | `!=` |
| `>` | `>` | `>` | `>` |
| `>=` | `>=` | `>=` | `>=` |
| `<` | `<` | `<` | `<` |
| `<=` | `<=` | `<=` | `<=` |
| `IN (...)` | `IN (...)` | `IN (...)` | `IN (...)` |
| `NOT IN (...)` | `NOT IN (...)` | `NOT IN (...)` | `NOT IN (...)` |
| `IS NULL` | `IS NULL` | `IS NULL` | `IS NULL` |
| `IS NOT NULL` | `IS NOT NULL` | `IS NOT NULL` | `IS NOT NULL` |
| `LIKE` | `LIKE` | `LIKE` | `LIKE` |
| `BETWEEN` | `BETWEEN` | `BETWEEN` | `BETWEEN` |

**文字列比較（大文字小文字を区別しない）:**
| YQL | PostgreSQL | MySQL | SQL Server |
|-----|-----------|-------|------------|
| `column ILIKE 'pattern'` | `column ILIKE 'pattern'` | `column LIKE 'pattern' COLLATE utf8_general_ci` | `column LIKE 'pattern'` |
| `column CONTAINS 'text'` | `column ILIKE '%text%'` | `column LIKE '%text%' COLLATE utf8_general_ci` | `column LIKE '%text%'` |

### 6.4 WHERE句でのサブクエリ条件

**WHERE句でのサブクエリは許可されています。相関サブクエリやEXISTS句など、適切なケースで使用できます。**

#### EXISTS/NOT EXISTS句

**YQL構文:**
```yaml
query:
  select:
    - customer_id: customer_id
    - name: name
    - email: email
  from: c: customers
  where:
    - "EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.order_date >= DATE('now', '-30 days'))"
```

**変換ルール（全DB共通）:**
```sql
SELECT c.customer_id AS customer_id, c.name AS name, c.email AS email
FROM customers c
WHERE EXISTS (
  SELECT 1
  FROM orders o
  WHERE o.customer_id = c.customer_id
    AND o.order_date >= DATE('now', '-30 days')
)
```

#### IN/NOT IN句

**YQL構文:**
```yaml
query:
  select:
    - customer_id: customer_id
    - name: name
    - email: email
  from: c: customers
  where:
    - field: customer_id
      operator: IN
      subquery:
        select:
          - customer_id: o.customer_id
        from: o: orders
        where:
          - "o.order_date >= DATE('now', '-30 days')"
        group_by: [o.customer_id]
        having: ["COUNT(*) >= 3"]
```

**変換ルール（全DB共通）:**
```sql
SELECT customer_id AS customer_id, name AS name, email AS email
FROM customers c
WHERE customer_id IN (
  SELECT customer_id AS customer_id
  FROM orders
  WHERE order_date >= DATE('now', '-30 days')
  GROUP BY customer_id
  HAVING COUNT(*) >= 3
)
```

**対応演算子:**
- `IN`
- `NOT IN`
- `EXISTS`
- `NOT EXISTS`
- `=` (単一行サブクエリ)
- `!=` (単一行サブクエリ)
- `>`, `>=`, `<`, `<=` (単一行サブクエリ)

**注意事項:**
- WHERE句でのサブクエリは許可されています
- 相関サブクエリ（EXISTS等）は適切なケースで使用可能
- 単純なIN句の場合は、WITH句+JOINの方が可読性が高い場合があります

## 7. GROUP BY句の変換

### 7.1 基本GROUP BY

#### YQL構文
```yaml
group_by: [column1, column2]
group_by: ["table_alias.column1", "column2"]
```

#### 変換ルール

**全DB共通:**
```sql
GROUP BY column1, column2
GROUP BY table_alias.column1, column2
```

**注意事項:**
- SELECT句に集計関数以外のカラムがある場合、GROUP BYに含める必要がある
- エイリアス名ではなく元のカラム名を使用

### 7.2 パラメータによる条件付きGROUP BY

#### YQL構文
```yaml
group_by:
  - column1
  - if: "${group_by_region}"
    then: "region_code"
```

#### 変換ルール

**MyBatis XML生成例:**
```xml
GROUP BY column1
<if test="groupByRegion != null and groupByRegion">
  , region_code
</if>
```

**注意事項:**
- 条件付きGROUP BYは可能だが、SELECT句にも対応する条件分岐が必要

## 8. HAVING句の変換

### 8.1 基本HAVING

#### YQL構文
```yaml
having:
  - "COUNT(*) > 10"
  - "SUM(amount) > 1000"
  - "COUNT(*) > 10 OR SUM(amount) > 1000"  # OR条件は文字列内で記述
```

#### 変換ルール

**全DB共通:**
```sql
HAVING COUNT(*) > 10
  AND SUM(amount) > 1000
  AND (COUNT(*) > 10 OR SUM(amount) > 1000)
```

**注意事項:**
- HAVING句はGROUP BY句とセットで使用
- 集計関数を使用した条件のみ記述可能
- 複数の条件はデフォルトで`AND`で結合されます
- `OR`条件を記述する場合は、文字列内で`OR`を使用します
- WHERE句と異なり、`and:`/`or:`の明示的な記述は不要です（文字列形式で十分です）

## 9. ORDER BY句の変換

### 9.1 基本ORDER BY

#### YQL構文
```yaml
order_by:
  - field: column_name
    direction: ASC | DESC
  - column_name: DESC  # 短縮形
```

#### 変換ルール

**全DB共通:**
```sql
ORDER BY column_name ASC, column_name DESC
```

### 9.2 パラメータによる動的ORDER BY

#### YQL構文
```yaml
order_by:
  - if: "${sort_by} == 'name'"
    then:
      field: name
      direction: "${sort_direction:ASC}"
  - if: "${sort_by} == 'created_at'"
    then:
      field: created_at
      direction: DESC
```

#### 変換ルール

**MyBatis XML生成例:**
```xml
ORDER BY
<if test="sortBy != null and sortBy == 'name'">
  name ${sortDirection != null ? sortDirection : 'ASC'}
</if>
<if test="sortBy != null and sortBy == 'created_at'">
  created_at DESC
</if>
```

**注意事項:**
- デフォルト値は`${param:defaultValue}`形式で指定

## 10. LIMIT/OFFSET句の変換

### 10.1 基本LIMIT/OFFSET

#### YQL構文
```yaml
limit: 10
offset: 20
```

#### 変換ルール

| YQL | PostgreSQL | MySQL | SQL Server | Oracle |
|-----|-----------|-------|------------|--------|
| `limit: 10, offset: 20` | `LIMIT 10 OFFSET 20` | `LIMIT 20, 10` | `OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY` | `SELECT * FROM (SELECT ..., ROW_NUMBER() OVER (ORDER BY ...) AS rn FROM ...) WHERE rn > 20 AND rn <= 30` |

**注意事項:**
- SQL ServerではORDER BY句が必須
- Oracleでは`offset`がある場合は`ROW_NUMBER() OVER()`を使用（ORDER BY句が必須）
- Oracleで`offset: 0`の場合は`ROWNUM <= limit`を使用可能

### 10.2 パラメータによるLIMIT/OFFSET

#### YQL構文
```yaml
limit: "${per_page:20}"
offset: "$((${page:1} - 1) * ${per_page:20})"
```

#### 変換ルール

**PostgreSQL:**
```sql
LIMIT #{perPage} OFFSET #{offset}
```

**MySQL:**
```sql
LIMIT #{offset}, #{perPage}
```

**SQL Server:**
```sql
OFFSET #{offset} ROWS FETCH NEXT #{perPage} ROWS ONLY
```

**Oracle:**
```sql
SELECT * FROM (
  SELECT ..., ROW_NUMBER() OVER (ORDER BY ...) AS rn FROM ...
) WHERE rn > #{offset} AND rn <= #{offset + perPage}
```

**注意事項:**
- 計算式はコンパイル時に評価される
- パラメータは`#{paramName}`形式でバインド
- Oracleでは`offset`がある場合は`ROW_NUMBER() OVER()`を使用（ORDER BY句が必須）
- Oracleで`offset: 0`の場合は`WHERE ROWNUM <= #{perPage}`を使用可能

### 10.3 pagination構文（ページング自動化）

ページング処理を簡潔に記述するための`pagination`構文を提供します。`pagination`構文は、内部的に`limit`と`offset`に展開されます。

#### YQL構文
```yaml
query:
  pagination:
    page: "#{page:1}"           # ページ番号（デフォルト: 1）
    per_page: "#{per_page:20}"  # 1ページあたりの件数（デフォルト: 20）
  select:
    - id: c.id
    - name: c.name
  from: c: customers
  order_by:
    - field: c.created_at
      direction: DESC
```

#### 変換ルール

`pagination`構文は、内部的に以下のように展開されます：

```yaml
# pagination構文
pagination:
  page: "#{page:1}"
  per_page: "#{per_page:20}"

# 内部的に以下に展開される:
limit: "#{per_page:20}"
offset: "$((${page:1} - 1) * ${per_page:20})"
```

**PostgreSQL:**
```sql
LIMIT #{per_page} OFFSET #{(page - 1) * per_page}
```

**MySQL:**
```sql
LIMIT #{(page - 1) * per_page}, #{per_page}
```

**SQL Server:**
```sql
OFFSET #{(page - 1) * per_page} ROWS FETCH NEXT #{per_page} ROWS ONLY
```

**Oracle:**
```sql
SELECT * FROM (
  SELECT ..., ROW_NUMBER() OVER (ORDER BY ...) AS rn FROM ...
) WHERE rn > #{(page - 1) * per_page} AND rn <= #{page * per_page}
```

**注意事項:**
- SQL Serverでは`ORDER BY`が必須です。`pagination`が定義されている場合、`order_by`が存在しない場合はエラーを発生させます
- Oracleでは`ORDER BY`が必須です。`pagination`が定義されている場合、`order_by`が存在しない場合はエラーを発生させます
- 計算式（`offset = (page - 1) * per_page`）は、テンプレートエンジンで評価されます
- パラメータが渡されない場合、デフォルト値を使用します

#### パラメータのカスタマイズ

パラメータ名はカスタマイズ可能です：

```yaml
query:
  pagination:
    page: "#{current_page:1}"
    per_page: "#{items_per_page:20}"
  # ...
```

#### paginationが定義されていない場合

`pagination`が定義されていない場合、ページングは適用されません（LIMIT/OFFSETなし）。

```yaml
query:
  select:
    - id: c.id
    - name: c.name
  from: c: customers
  # paginationなし = LIMIT/OFFSETなし（全件取得）
```

**注意**: `pagination: false`のような明示的な無効化は不要です。`pagination`が定義されていない = ページングなし（デフォルト）と判断します。

#### 明示的なLIMIT/OFFSETとの関係

`pagination`と明示的な`limit`/`offset`が同時に定義されている場合、エラーを発生させます。

```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  limit: 100  # エラー: paginationとlimit/offsetは同時に使用できません
```

**理由**: 意図の明確化のため。どちらを使うか明確に判断できるようにする。

#### 推奨パターン

- **ページング**: `pagination`構文を使用
- **上限付き取得**: 既存の`limit`を使用（例: `limit: "#{max_rows:100}"`）
- **単一レコード取得**: 既存の`limit: 1`を使用
- **全件取得**: `limit`/`offset`なし（デフォルト）

#### 使用例

**基本的なページング:**
```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  select:
    - id: c.id
    - name: c.name
  from: c: customers
  order_by:
    - field: c.created_at
      direction: DESC
```

**カスタムパラメータ名:**
```yaml
query:
  pagination:
    page: "#{current_page:1}"
    per_page: "#{items_per_page:20}"
  select:
    - id: c.id
    - name: c.name
  from: c: customers
  order_by:
    - field: c.created_at
      direction: DESC
```

## 11. WITH句（CTE）の変換

**重要:** CTE（Common Table Expression）内のSELECT文は、本仕様書の2章（SELECT句）から10章（LIMIT/OFFSET句）までの基礎定義に従って記述されます。

**パーサーの実装方針:**
- CTE内のSELECT文は再帰的に解析します
- テーブル/カラムの存在チェックと依存関係のチェックを行います
- 動的SQLの生成はテンプレートエンジンに任せます（テンプレート形式を出力するのみ）

### 11.1 基本CTE

#### YQL構文
```yaml
with_clauses:
  cte_name:
    select:
      - column1: column1
      - column2: column2
    from: t: table_name
    where: ["condition"]
    group_by: [column1]
```

#### 変換ルール

**全DB共通:**
```sql
WITH cte_name AS (
  SELECT column1 AS column1, column2 AS column2
  FROM table_name
  WHERE condition
  GROUP BY column1
)
```

**注意事項:**
- CTE内のSELECT文は、2章（SELECT句）から10章（LIMIT/OFFSET句）までの基礎定義に従って記述されます
- SELECT句、FROM句、JOIN句、WHERE句、GROUP BY句、HAVING句、ORDER BY句、LIMIT/OFFSET句のすべての構文が使用可能です

### 11.2 複数CTE

#### YQL構文
```yaml
with_clauses:
  cte1:
    select:
      - column1: column1
    from: table1
  cte2:
    select:
      - column2: column2
    from: cte1
```

#### 変換ルール

**全DB共通:**
```sql
WITH cte1 AS (
  SELECT column1 AS column1
  FROM table1
),
cte2 AS (
  SELECT column2 AS column2
  FROM cte1
)
```

**注意事項:**
- CTEはカンマ区切りで連結
- 後続のCTEは前のCTEを参照可能
- 各CTE内のSELECT文は、2章（SELECT句）から10章（LIMIT/OFFSET句）までの基礎定義に従って記述されます

## 12. 関数の変換マッピング

### 12.1 日付関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|-----------|-------|------------|
| `DATE('now')` | `CURRENT_DATE` | `CURDATE()` | `CAST(GETDATE() AS DATE)` |
| `DATE('now', '-1 day')` | `CURRENT_DATE - INTERVAL '1 day'` | `DATE_SUB(CURDATE(), INTERVAL 1 DAY)` | `DATEADD(DAY, -1, CAST(GETDATE() AS DATE))` |
| `DATE_TRUNC('month', date)` | `DATE_TRUNC('month', date)` | `DATE_FORMAT(date, '%Y-%m-01')` | `DATEFROMPARTS(YEAR(date), MONTH(date), 1)` |
| `EXTRACT(YEAR FROM date)` | `EXTRACT(YEAR FROM date)` | `YEAR(date)` | `YEAR(date)` |
| `DATEDIFF(date1, date2)` | `date1 - date2` | `DATEDIFF(date1, date2)` | `DATEDIFF(DAY, date2, date1)` |

### 12.2 文字列関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|-----------|-------|------------|
| `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` |
| `SUBSTRING(str, start, length)` | `SUBSTRING(str, start, length)` | `SUBSTRING(str, start, length)` | `SUBSTRING(str, start, length)` |
| `LENGTH(str)` | `LENGTH(str)` | `LENGTH(str)` | `LEN(str)` |
| `UPPER(str)` | `UPPER(str)` | `UPPER(str)` | `UPPER(str)` |
| `LOWER(str)` | `LOWER(str)` | `LOWER(str)` | `LOWER(str)` |
| `TRIM(str)` | `TRIM(str)` | `TRIM(str)` | `LTRIM(RTRIM(str))` |

### 12.3 数値関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|-----------|-------|------------|
| `ROUND(value, digits)` | `ROUND(value, digits)` | `ROUND(value, digits)` | `ROUND(value, digits)` |
| `CEIL(value)` | `CEIL(value)` | `CEIL(value)` | `CEILING(value)` |
| `FLOOR(value)` | `FLOOR(value)` | `FLOOR(value)` | `FLOOR(value)` |
| `ABS(value)` | `ABS(value)` | `ABS(value)` | `ABS(value)` |

### 12.4 NULL処理関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|-----------|-------|------------|
| `COALESCE(value1, value2)` | `COALESCE(value1, value2)` | `COALESCE(value1, value2)` | `COALESCE(value1, value2)` |
| `IFNULL(value, default)` | `COALESCE(value, default)` | `IFNULL(value, default)` | `ISNULL(value, default)` |

## 13. include定義の変換

### 13.1 スキーマインクルード

#### YQL構文
```yaml
includes:
  - "schemas/common.yql"
  - "schemas/sales.yql"
```

#### 変換ルール

- コンパイル時にスキーマ定義を読み込み
- テーブル名、カラム名、型情報を解決
- SQL生成時には直接的な変換は不要（型チェックに使用）

### 13.2 SELECTブロックインクルード

#### YQL構文
```yaml
includes:
  - "queries/common_selects.yql"

query:
  select:
    - include: "customer_summary"  # 共通SELECTブロックを参照
```

#### 変換ルール

- コンパイル時に共通SELECTブロックを展開
- インライン展開されるため、SQL生成時には変換不要

### 13.3 マクロインクルード

#### YQL構文
```yaml
includes:
  - "macros/date_functions.yql"

query:
  select:
    - last_month: "DATE_TRUNC_MONTH(CURRENT_DATE - 1)"  # マクロ関数
```

#### 変換ルール

- コンパイル時にマクロを展開
- 展開後の式を通常の式として処理

## 14. パラメータバインディング

### 14.1 パラメータ記法

#### YQL構文
```yaml
where:
  - "column = #{paramName}"           # 単一値パラメータ
  - "column IN (${paramArray})"       # 配列パラメータ
  - if: "${conditionParam}"           # 条件分岐用パラメータ
    then: "column = #{valueParam}"
```

#### 変換ルール

**パラメータ記法の使い分け:**

1. **`#{paramName}` - 単一値パラメータ（値のバインド）**
   - `#{paramName}` → `?` (PreparedStatement)
   - パラメータ名はキャメルケースからスネークケースに変換
   - SQL文内で値として使用されるパラメータ
   - 例: `WHERE id = #{id}`, `SET name = #{name}`

2. **`${paramArray}` - 配列パラメータ（配列の展開）**
   - `IN (${paramArray})` → `IN (?, ?, ?)` (要素数に応じて展開)
   - 配列をIN句などで展開する場合に使用
   - 例: `WHERE id IN (${ids})`

3. **`${paramName}` - 条件分岐用パラメータ（テンプレートエンジン用）**
   - 条件分岐（if句など）で使用
   - テンプレートエンジン（MyBatis、JinjaSQL等）の形式として出力
   - 値のバインドには使用しない
   - 例: `if: "${nameFilter}"`, `if: "${sortBy} == 'name'"`

**注意事項:**
- `#{paramName}`は必ずPreparedStatement形式でバインド
- `${paramArray}`は配列を展開して複数の`?`に変換
- `${paramName}`は条件分岐用で、値のバインドには使用しない
- SQLインジェクション対策のため、文字列連結は禁止

## 15. エラーハンドリング

### 15.1 変換エラー

以下の場合にエラーを発生:

1. **未定義テーブル/カラム**
   - スキーマ定義に存在しないテーブル/カラムを参照

2. **型不一致**
   - 比較演算子で互換性のない型を比較

3. **GROUP BY違反**
   - SELECT句の非集計カラムがGROUP BYに含まれていない

4. **構文エラー**
   - YQL構文が不正
   - FROM句でのサブクエリの使用（WITH句を使用してください）

### 15.2 警告

以下の場合に警告を出力:

1. **パフォーマンスに影響する可能性のあるクエリ**
2. **インデックスが使用されない可能性のある条件**

## 16. 実装時の注意事項

### 16.1 カラム句での分岐禁止

**禁止:**
```yaml
select:
  - if: "${include_sales}"
    then: total_sales: "SUM(amount)"
```

**許可:**
```yaml
select:
  - total_sales: "SUM(amount)"  # 常に含める
where:
  - if: "${include_sales}"
    then: "amount > 0"  # WHERE句で条件分岐
```

### 16.2 パラメータのスコープ

- パラメータはクエリ全体で有効
- WITH句（CTE）内でもパラメータを参照可能
- パラメータはWITH句で定義したCTE内でも使用可能

### 16.3 識別子の引用

- 予約語や特殊文字を含む識別子は引用符で囲む
- 引用符の種類はDB依存:
  - PostgreSQL: ダブルクォート `"identifier"`
  - MySQL: バッククォート `` `identifier` ``
  - SQL Server: 角括弧 `[identifier]`

---

**バージョン**: 1.0.0  
**最終更新**: 2024-12-04  
**ステータス**: ドラフト


