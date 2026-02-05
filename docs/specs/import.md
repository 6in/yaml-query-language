---
layout: default
title: Import
---

# YQL import機能 仕様書（ドラフト）

## 1. 概要

このドキュメントは、YQLのimport機能を定義します。import機能により、スキーマ定義、SELECT定義、カラム定義（マクロ）などを再利用可能な形で定義し、他のYQLファイルから参照できます。

### 1.1 目的

- **再利用性の向上**: 共通のSELECT定義やカラム定義を再利用
- **保守性の向上**: 定義を1箇所に集約し、変更時の影響範囲を最小化
- **可読性の向上**: 複雑な定義を別ファイルに分離し、メインクエリを簡潔に

### 1.2 対応するimportタイプ

1. **SELECT定義のimport**: WITH句やサブクエリとして使用
2. **カラム定義（マクロ）のimport**: SELECT句や式として使用
3. **スキーマ定義のimport**: テーブル定義、型定義などの参照

### 1.3 パラメータ記法の使い分け

- **`#{paramName}`**: PreparedStatement用のパラメータバインディング（実行時に`?`に変換）
- **`${paramArray}`**: 配列パラメータの展開（IN句など）
- **`${paramName}`**: 条件分岐用パラメータ（テンプレートエンジン用）
- **`@{parameter_name}`**: マクロ定義内でのパラメータ参照（マクロ呼び出し時に式に置き換えられる）

## 2. SELECT定義のimport

### 2.1 基本構文

#### 定義ファイル（`queries/customer_summary.yql`）
```yaml
# 再利用可能なSELECT定義
name: "customer_summary"
description: "顧客サマリー取得用のSELECT定義"

select_definition:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - order_count: "COUNT(o.order_id)"
    - total_amount: "SUM(o.amount)"
    - last_order_date: "MAX(o.order_date)"
  from: c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  where:
    - "c.status = 'active'"
  group_by: [c.customer_id, c.name]
```

#### 使用ファイル（`queries/active_customers.yql`）
```yaml
imports:
  - "queries/customer_summary.yql"

query:
  with_clauses:
    customer_summary:
      using: "customer_summary"  # importしたSELECT定義を参照
  select:
    - customer_id: cs.customer_id
    - customer_name: cs.customer_name
    - order_count: cs.order_count
    - total_amount: cs.total_amount
  from: cs: customer_summary
  where:
    - "cs.order_count > 0"
  order_by:
    - field: total_amount
      direction: DESC
```

#### 変換ルール

**PostgreSQL/MySQL/SQL Server:**
```sql
WITH customer_summary AS (
  SELECT 
    c.customer_id AS customer_id,
    c.name AS customer_name,
    COUNT(o.order_id) AS order_count,
    SUM(o.amount) AS total_amount,
    MAX(o.order_date) AS last_order_date
  FROM customers c
  LEFT JOIN orders o ON c.customer_id = o.customer_id
  WHERE c.status = 'active'
  GROUP BY c.customer_id, c.name
)
SELECT 
  cs.customer_id AS customer_id,
  cs.customer_name AS customer_name,
  cs.order_count AS order_count,
  cs.total_amount AS total_amount
FROM customer_summary cs
WHERE cs.order_count > 0
ORDER BY total_amount DESC
```

**注意事項:**
- `using: "customer_summary"`は、importしたSELECT定義をWITH句として展開
- importしたSELECT定義は、`specs/select.md`の仕様に従う必要がある
- WITH句の名前（`customer_summary`）は、import定義の名前と一致させる必要がある

### 2.2 パラメータ付きSELECT定義

#### 定義ファイル（`queries/customer_orders.yql`）
```yaml
name: "customer_orders"
description: "顧客の注文一覧取得用のSELECT定義（パラメータ付き）"

select_definition:
  parameters:
    customer_status: "active"  # デフォルト値
    min_order_amount: 0        # デフォルト値
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - order_id: o.order_id
    - order_date: o.order_date
    - amount: o.amount
  from: c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  where:
    - "c.status = #{customerStatus}"
    - "o.amount >= #{minOrderAmount}"
```

#### 使用ファイル（`queries/premium_customers.yql`）
```yaml
imports:
  - "queries/customer_orders.yql"

query:
  with_clauses:
    premium_orders:
      using: "customer_orders"
      parameters:
        customer_status: "premium"
        min_order_amount: 10000
  select:
    - customer_id: po.customer_id
    - customer_name: po.customer_name
    - order_count: "COUNT(po.order_id)"
    - total_amount: "SUM(po.amount)"
  from: po: premium_orders
  group_by: [po.customer_id, po.customer_name]
```

#### 変換ルール

**PostgreSQL/MySQL/SQL Server:**
```sql
WITH premium_orders AS (
  SELECT 
    c.customer_id AS customer_id,
    c.name AS customer_name,
    o.order_id AS order_id,
    o.order_date AS order_date,
    o.amount AS amount
  FROM customers c
  INNER JOIN orders o ON c.customer_id = o.customer_id
  WHERE c.status = ?  -- 'premium'
    AND o.amount >= ?  -- 10000
)
SELECT 
  po.customer_id AS customer_id,
  po.customer_name AS customer_name,
  COUNT(po.order_id) AS order_count,
  SUM(po.amount) AS total_amount
FROM premium_orders po
GROUP BY po.customer_id, po.customer_name
```

**注意事項:**
- importしたSELECT定義にパラメータがある場合、`parameters`で値を指定
- パラメータが指定されない場合は、定義ファイルのデフォルト値を使用
- パラメータは`#{paramName}`形式でバインド

### 2.3 複数のSELECT定義のimport

#### 定義ファイル（`queries/common_definitions.yql`）
```yaml
select_definitions:
  customer_summary:
    select:
      - customer_id: c.customer_id
      - customer_name: c.name
      - order_count: "COUNT(o.order_id)"
    from: c: customers
    joins:
      - type: LEFT
        alias: o
        table: orders
        on: "c.customer_id = o.customer_id"
    group_by: [c.customer_id, c.name]
  
  product_sales:
    select:
      - product_id: p.product_id
      - product_name: p.name
      - total_sales: "SUM(oi.quantity * oi.unit_price)"
    from: p: products
    joins:
      - type: LEFT
        alias: oi
        table: order_items
        on: "p.product_id = oi.product_id"
    group_by: [p.product_id, p.name]
```

#### 使用ファイル（`queries/dashboard.yql`）
```yaml
imports:
  - "queries/common_definitions.yql"

query:
  with_clauses:
    customers:
      using: "customer_summary"
    products:
      using: "product_sales"
  select:
    - customer_id: c.customer_id
    - customer_name: c.customer_name
    - product_name: p.product_name
    - total_sales: p.total_sales
  from: c: customers
  joins:
    - type: CROSS
      alias: p
      table: products
```

## 3. カラム定義（マクロ）のimport

### 3.1 基本構文（デフォルト値を使用）

#### 定義ファイル（`macros/customer_segment.yql`）
```yaml
# 再利用可能なカラム定義（マクロ）
name: "customer_segment"
description: "顧客セグメント判定用のCASE式"

column_definition:
  expression: |
    CASE
      WHEN annual_sales >= 1000000 THEN 'Enterprise'
      WHEN annual_sales >= 100000 THEN 'Business'
      WHEN annual_sales >= 10000 THEN 'Professional'
      ELSE 'Starter'
    END
  parameters:
    annual_sales: "SUM(o.amount)"  # デフォルト値（式）
```

**注意事項:**
- マクロ定義内でパラメータを参照する場合は、`@{parameter_name}`形式を使用
- `@{parameter_name}`は、マクロ呼び出し時に渡された式に置き換えられる
- 既存のパラメータバインディング（`#{paramName}`: PreparedStatement用）とは異なる記法

#### 使用ファイル（`queries/customer_analysis.yql`）
```yaml
imports:
  - "macros/customer_segment.yql"

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - segment: "@customer_segment"  # マクロを参照
    - annual_sales: "SUM(o.amount)"
  from: c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  group_by: [c.customer_id, c.name]
```

#### 変換ルール

**PostgreSQL/MySQL/SQL Server:**
```sql
SELECT 
  c.customer_id AS customer_id,
  c.name AS customer_name,
  CASE
    WHEN SUM(o.amount) >= 1000000 THEN 'Enterprise'
    WHEN SUM(o.amount) >= 100000 THEN 'Business'
    WHEN SUM(o.amount) >= 10000 THEN 'Professional'
    ELSE 'Starter'
  END AS segment,
  SUM(o.amount) AS annual_sales
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
```

**注意事項:**
- `@customer_segment`は、importしたカラム定義（マクロ）を参照
- マクロ内のパラメータは、デフォルト値が使用される
- マクロは式として展開される

### 3.1.1 パラメータを使用したマクロ呼び出し

#### 定義ファイル（`macros/customer_segment.yql`）
```yaml
name: "customer_segment"
description: "顧客セグメント判定用のCASE式"

column_definition:
  expression: |
    CASE
      WHEN @{annual_sales} >= 1000000 THEN 'Enterprise'
      WHEN @{annual_sales} >= 100000 THEN 'Business'
      WHEN @{annual_sales} >= 10000 THEN 'Professional'
      ELSE 'Starter'
    END
  parameters:
    annual_sales: null  # 必須パラメータ
```

#### 使用ファイル（`queries/customer_analysis.yql`）
```yaml
imports:
  - "macros/customer_segment.yql"

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - segment:
        macro: "customer_segment"
        parameters:
          annual_sales: "SUM(o.amount)"  # パラメータ名を指定して値を渡す
    - annual_sales: "SUM(o.amount)"
  from: c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  group_by: [c.customer_id, c.name]
```

#### 変換ルール

**PostgreSQL/MySQL/SQL Server:**
```sql
SELECT 
  c.customer_id AS customer_id,
  c.name AS customer_name,
  CASE
    WHEN SUM(o.amount) >= 1000000 THEN 'Enterprise'
    WHEN SUM(o.amount) >= 100000 THEN 'Business'
    WHEN SUM(o.amount) >= 10000 THEN 'Professional'
    ELSE 'Starter'
  END AS segment,
  SUM(o.amount) AS annual_sales
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
```

**注意事項:**
- `parameters`は名前付きで、パラメータ名を指定して値を渡す
- パラメータ名はマクロ定義の`parameters`で定義された名前を使用
- パラメータは式（カラム名、関数呼び出し等）として記述
- デフォルト値があるパラメータは省略可能
- マクロ定義内でパラメータを参照する場合は、`@{parameter_name}`形式を使用（既存の`#{paramName}`: PreparedStatement用とは異なる）

### 3.2 複数引数を持つマクロ

#### 定義ファイル（`macros/price_range.yql`）
```yaml
name: "price_range"
description: "価格帯判定用のCASE式"

column_definition:
  expression: |
    CASE
      WHEN @{price} >= @{highThreshold} THEN 'High'
      WHEN @{price} >= @{lowThreshold} THEN 'Medium'
      ELSE 'Low'
    END
  parameters:
    price: null  # 必須パラメータ
    highThreshold: 10000  # デフォルト値あり
    lowThreshold: 1000    # デフォルト値あり
```

#### 使用ファイル（`queries/product_analysis.yql`）
```yaml
imports:
  - "macros/price_range.yql"

query:
  select:
    - product_id: p.product_id
    - product_name: p.name
    - price_range:
        macro: "price_range"
        parameters:
          price: "p.unit_price"    # 必須パラメータ
          highThreshold: 50000     # デフォルト値（10000）を上書き
          lowThreshold: 5000       # デフォルト値（1000）を上書き
  from: p: products
```

**デフォルト値を使用する場合:**
```yaml
imports:
  - "macros/price_range.yql"

query:
  select:
    - product_id: p.product_id
    - product_name: p.name
    - price_range:
        macro: "price_range"
        parameters:
          price: "p.unit_price"    # 必須パラメータのみ指定
          # highThresholdとlowThresholdはデフォルト値（10000, 1000）を使用
  from: p: products
```

#### 変換ルール

**PostgreSQL/MySQL/SQL Server:**
```sql
SELECT 
  p.product_id AS product_id,
  p.name AS product_name,
  CASE
    WHEN p.unit_price >= 50000 THEN 'High'
    WHEN p.unit_price >= 5000 THEN 'Medium'
    ELSE 'Low'
  END AS price_range
FROM products p
```

**注意事項:**
- `parameters`は名前付きで、パラメータ名を指定して値を渡す
- パラメータ名はマクロ定義の`parameters`で定義された名前を使用
- デフォルト値があるパラメータは省略可能
- 必須パラメータ（デフォルト値がnull）は必ず指定する必要がある

### 3.3 複雑な式のマクロ（複数引数）

#### 定義ファイル（`macros/rfm_analysis.yql`）
```yaml
name: "rfm_segment"
description: "RFM分析による顧客セグメント判定"

column_definition:
  expression: |
    CASE
      WHEN @{recency} <= 30 AND @{frequency} >= 10 AND @{monetary} >= 100000 THEN 'Champion'
      WHEN @{recency} <= 60 AND @{frequency} >= 5 AND @{monetary} >= 50000 THEN 'Loyal'
      WHEN @{recency} <= 90 AND @{frequency} >= 3 AND @{monetary} >= 20000 THEN 'Potential'
      WHEN @{recency} <= 180 AND @{frequency} >= 1 AND @{monetary} >= 10000 THEN 'At Risk'
      ELSE 'Lost'
    END
  parameters:
    recency: null    # 必須パラメータ
    frequency: null  # 必須パラメータ
    monetary: null   # 必須パラメータ
```

#### 使用ファイル（`queries/customer_segmentation.yql`）
```yaml
imports:
  - "macros/rfm_analysis.yql"

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - rfm_segment:
        macro: "rfm_segment"
        parameters:
          recency: "DATEDIFF(CURRENT_DATE, MAX(o.order_date))"    # 必須パラメータ
          frequency: "COUNT(DISTINCT o.order_id)"                # 必須パラメータ
          monetary: "SUM(o.amount)"                               # 必須パラメータ
  from: c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  group_by: [c.customer_id, c.name]
```

#### 変換ルール

**PostgreSQL/MySQL/SQL Server:**
```sql
SELECT 
  c.customer_id AS customer_id,
  c.name AS customer_name,
  CASE
    WHEN DATEDIFF(CURRENT_DATE, MAX(o.order_date)) <= 30 
         AND COUNT(DISTINCT o.order_id) >= 10 
         AND SUM(o.amount) >= 100000 THEN 'Champion'
    WHEN DATEDIFF(CURRENT_DATE, MAX(o.order_date)) <= 60 
         AND COUNT(DISTINCT o.order_id) >= 5 
         AND SUM(o.amount) >= 50000 THEN 'Loyal'
    WHEN DATEDIFF(CURRENT_DATE, MAX(o.order_date)) <= 90 
         AND COUNT(DISTINCT o.order_id) >= 3 
         AND SUM(o.amount) >= 20000 THEN 'Potential'
    WHEN DATEDIFF(CURRENT_DATE, MAX(o.order_date)) <= 180 
         AND COUNT(DISTINCT o.order_id) >= 1 
         AND SUM(o.amount) >= 10000 THEN 'At Risk'
    ELSE 'Lost'
  END AS rfm_segment
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
```

**注意事項:**
- `parameters`は名前付きで、パラメータ名を指定して値を渡す
- パラメータ名はマクロ定義の`parameters`で定義された名前を使用
- パラメータは式（カラム名、関数呼び出し等）として記述
- 必須パラメータ（デフォルト値がnull）は必ず指定する必要がある

## 4. スキーマ定義のimport

### 4.1 基本構文

#### 定義ファイル（`schemas/ecommerce.yql`）
```yaml
# スキーマ定義
schema_version: "1.0.0"
namespace: "ecommerce"

tables:
  customers:
    columns:
      customer_id:
        type: integer
        constraints:
          primary_key: true
      name:
        type: string
        constraints:
          not_null: true
      status:
        type: enum
        values: ["active", "inactive", "suspended"]
  
  orders:
    columns:
      order_id:
        type: integer
        constraints:
          primary_key: true
      customer_id:
        type: integer
        constraints:
          foreign_key:
            table: "customers"
            column: "customer_id"
      amount:
        type: decimal
        precision: 12
        scale: 2
```

#### 使用ファイル（`queries/customer_orders.yql`）
```yaml
imports:
  - "schemas/ecommerce.yql"

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - order_count: "COUNT(o.order_id)"
  from: c: customers  # importしたスキーマ定義からテーブルを参照
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  group_by: [c.customer_id, c.name]
```

**注意事項:**
- スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照可能
- 型チェックやバリデーションに使用
- SQL生成時には直接的な変換は不要（型チェックに使用）

## 5. importの解決順序

### 5.1 解決順序

1. **相対パス**: `./queries/customer_summary.yql`
2. **絶対パス**: `/project/queries/customer_summary.yql`
3. **パスエイリアス**: `@queries/customer_summary.yql`（設定ファイルで定義）

### 5.2 循環参照の検出

- importの循環参照を検出し、エラーを発生
- 例: `A.yql` → `B.yql` → `A.yql`（循環参照エラー）

## 6. セキュリティに関する注意事項

### 6.1 マクロパラメータの安全な使用

マクロパラメータ `@{paramName}` は、渡された式をそのままSQL内に埋め込みます。以下の点に注意してください。

#### 6.1.1 ユーザー入力を直接渡さない

**❌ 危険なパターン:**
```yaml
# ユーザー入力をマクロパラメータに直接渡す（禁止）
parameters:
  annual_sales: "#{userInput}"  # ユーザー入力がそのまま式として埋め込まれる
```

**✅ 安全なパターン:**
```yaml
# マクロパラメータには固定の式を使用
parameters:
  annual_sales: "SUM(o.amount)"  # 開発者が定義した固定の式

# ユーザー入力は #{paramName} でバインド
where:
  - "c.customer_id = #{customerId}"  # PreparedStatementでバインド
```

#### 6.1.2 許可された式のみ使用

マクロパラメータには、以下のみを使用してください:

| 許可される式 | 例 |
|--------------|-----|
| カラム名 | `c.customer_id`, `o.amount` |
| 関数呼び出し | `SUM(o.amount)`, `COUNT(*)` |
| 定数 | `100`, `'active'` |
| 算術演算 | `o.quantity * o.unit_price` |

**禁止される式:**
- 動的に構築された文字列
- ユーザー入力を含む式
- セミコロン（`;`）を含む式
- SQLコメント（`--`, `/* */`）を含む式

#### 6.1.3 コードレビューの実施

- マクロ定義ファイル（`macros/*.yql`）は、必ずコードレビューを行ってください
- マクロを使用するYQLファイルも、パラメータの内容を確認してください
- 不審な式がマクロパラメータに渡されていないか確認してください

### 6.2 パラメータ記法の使い分け

| 記法 | 用途 | セキュリティ | 使用場面 |
|------|------|--------------|----------|
| `#{paramName}` | PreparedStatement | ✅ 安全 | **ユーザー入力**を受け取る場合 |
| `${paramArray}` | 配列展開 | ✅ 安全 | IN句での配列展開 |
| `${paramName}` | 条件分岐 | ⚠️ 要注意 | テンプレートエンジン用 |
| `@{paramName}` | マクロパラメータ | ⚠️ 要注意 | **開発者が定義した式**のみ |

**重要:** ユーザー入力は必ず `#{paramName}` を使用してください。`@{paramName}` にユーザー入力を渡さないでください。

### 6.3 パーサーでの検証（実装推奨）

パーサー実装時には、以下の検証を推奨します:

1. **禁止パターンの検出**: マクロパラメータに禁止パターン（`;`, `--`, `UNION`, `DROP` 等）が含まれている場合に警告
2. **ユーザー入力混入の検出**: マクロパラメータ内に `#{paramName}` が含まれている場合に警告
3. **生成SQLのログ出力**: デバッグ目的で生成されたSQLをログ出力し、監視可能にする

## 7. 実装時の注意事項

### 7.1 名前空間

- importした定義は、定義ファイルの`name`フィールドで識別
- 同じ名前の定義が複数ある場合は、エラーを発生

### 7.2 パラメータのスコープ

- importしたSELECT定義のパラメータは、その定義内でのみ有効
- 親クエリのパラメータとは独立

### 7.3 エラーハンドリング

以下の場合にエラーを発生:

1. **未定義のimport**: 指定されたファイルが存在しない
2. **未定義の定義名**: importしたファイルに指定された定義名が存在しない
3. **型不一致**: パラメータの型が一致しない
4. **循環参照**: importの循環参照が検出された

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト

