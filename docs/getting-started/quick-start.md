---
layout: default
title: Quick Start
---

# 🚀 クイックスタート

YQLの基本的な書き方を学びます。

## 基本的なSELECTクエリ

```yaml
# customer_analysis.yql
query:
  select:
    - customer_id: c.customer_id
    - name: c.name
    - total_sales: "SUM(o.order_amount)"
    - order_count: "COUNT(o.order_id)"
  
  from: c: customers
  
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  
  where:
    - "c.status = 'active'"
    - "o.order_date >= DATE('now', '-1 month')"
  
  group_by: [c.customer_id, c.name]
  
  order_by:
    - field: total_sales
      direction: DESC
  
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
```

## 生成されるSQL

### PostgreSQL

```sql
SELECT 
  c.customer_id AS customer_id,
  c.name AS name,
  SUM(o.order_amount) AS total_sales,
  COUNT(o.order_id) AS order_count
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE c.status = 'active'
  AND o.order_date >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY c.customer_id, c.name
ORDER BY total_sales DESC
LIMIT 20 OFFSET 0;
```

### MySQL

```sql
SELECT 
  c.customer_id AS customer_id,
  c.name AS name,
  SUM(o.order_amount) AS total_sales,
  COUNT(o.order_id) AS order_count
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE c.status = 'active'
  AND o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
GROUP BY c.customer_id, c.name
ORDER BY total_sales DESC
LIMIT 20 OFFSET 0;
```

## 自然言語からの変換フロー

```
Input: "今月アクティブな顧客の売上ランキングを見たい"
    ↓ AI処理
Output: YQL (上記のような構造化されたYAML)
    ↓ YQLコンパイラ
SQL: PostgreSQL/MySQL/SQL Server 固有の最適化されたSQL
```

## YQLの構文要素

### SELECT句

エイリアス（AS）を先に書きます：

```yaml
select:
  - alias_name: column_or_expression
  - customer_id: c.customer_id        # カラム
  - total: "SUM(o.amount)"            # 集計関数
  - status_label: "CASE WHEN ..."     # 式
```

### FROM句

テーブルエイリアスを先に書きます：

```yaml
from: c: customers    # c は customers のエイリアス
```

### JOIN句

```yaml
joins:
  - type: INNER           # INNER / LEFT / RIGHT / FULL / CROSS
    alias: o              # テーブルエイリアス（先頭に記述推奨）
    table: orders         # テーブル名
    on: "c.customer_id = o.customer_id"  # 結合条件
```

### WHERE句

配列で条件を列挙（ANDで結合）：

```yaml
where:
  - "c.status = 'active'"
  - "o.order_date >= '2024-01-01'"
  - "c.region = 'tokyo' OR c.region = 'osaka'"  # ORは文字列内で
```

### GROUP BY / ORDER BY

```yaml
group_by: [c.customer_id, c.name]

order_by:
  - field: total_sales
    direction: DESC   # ASC / DESC
```

### LIMIT / OFFSET / PAGINATION

```yaml
# 方法1: 直接指定
limit: 10
offset: 20

# 方法2: ページネーション
pagination:
  page: "#{page:1}"        # デフォルト値付きパラメータ
  per_page: "#{per_page:20}"
```

## パラメータバインディング

```yaml
where:
  - "c.customer_id = #{customer_id}"    # 単一値
  - "c.status IN (${statuses})"         # 配列展開
```

| 記法 | 用途 |
|------|------|
| `#{name}` | 単一値のバインド |
| `${name}` | 配列展開、条件分岐 |

## 次のステップ

- [SELECT仕様書](../specs/select.md) - 詳細な仕様
- [INSERT仕様書](../specs/insert.md) - INSERT文の書き方
- [UPDATE仕様書](../specs/update.md) - UPDATE文の書き方
- [DELETE仕様書](../specs/delete.md) - DELETE文の書き方
- [ユースケース](../guides/yql-use-cases-overview.md) - 活用方法
