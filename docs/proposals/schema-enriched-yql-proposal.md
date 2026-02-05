---
layout: default
title: Schema Enriched Yql Proposal
---

# スキーマ情報付与YQL提案

## 概要

SQL→YQL変換時に、関連するテーブルのスキーマ定義情報をYQLに付与することで、AIがより高精度な解析を行えるようにする提案。

## 背景

現在のSQL→YQL変換では、クエリの構造のみが変換される。しかし、AIがクエリを解析する際には以下の情報があると有利：

- **型情報**: カラムのデータ型（integer, string, timestamp等）
- **制約情報**: NOT NULL, PRIMARY KEY, FOREIGN KEY等
- **リレーションシップ**: テーブル間の関連性
- **インデックス情報**: パフォーマンス最適化のヒント
- **ビジネスルール**: CHECK制約、ENUM値等

これらの情報をYQLに付与することで、AIは：
1. **型チェック**: カラムの型を理解し、適切な演算子・関数を推奨
2. **依存関係の把握**: 外部キー関係を理解し、JOIN条件の妥当性を検証
3. **最適化提案**: インデックス情報からクエリ最適化を提案
4. **エラー検出**: 制約違反の可能性を早期に検出
5. **意味理解**: ビジネスルールを理解し、より適切なクエリを生成

## 提案するYQL構造

### 基本構造

```yaml
# スキーマ情報付与YQL
metadata:
  source_sql: "SELECT c.id, c.name, o.id as order_id FROM customers c INNER JOIN orders o ON c.id = o.customer_id"
  converted_at: "2024-12-20T10:00:00Z"
  converter_version: "1.0.0"

# スキーマ情報（使用されているテーブルの定義）
schema:
  tables:
    customers:
      description: "顧客情報マスタテーブル"
      columns:
        id:
          type: integer
          constraints:
            not_null: true
            primary_key: true
            auto_increment: true
        name:
          type: string
          constraints:
            not_null: true
            max_length: 100
        status:
          type: enum
          values: ["active", "inactive", "suspended"]
          default: "active"
      indexes:
        - name: "idx_customers_id"
          columns: ["id"]
          unique: true
        - name: "idx_customers_status"
          columns: ["status"]
      foreign_keys:
        - column: "user_id"
          references:
            table: "users"
            column: "user_id"
    
    orders:
      description: "注文ヘッダーテーブル"
      columns:
        id:
          type: integer
          constraints:
            not_null: true
            primary_key: true
            auto_increment: true
        customer_id:
          type: integer
          constraints:
            not_null: true
            foreign_key:
              table: "customers"
              column: "id"
        order_date:
          type: timestamp
          constraints:
            not_null: true
          default: "CURRENT_TIMESTAMP"
        amount:
          type: decimal
          precision: 12
          scale: 2
          constraints:
            not_null: true
            check: "amount >= 0"
      indexes:
        - name: "idx_orders_customer"
          columns: ["customer_id"]
        - name: "idx_orders_date"
          columns: ["order_date"]
      foreign_keys:
        - column: "customer_id"
          references:
            table: "customers"
            column: "id"

# クエリ本体（既存のYQL構造）
query:
  select:
    - id: c.id
    - name: c.name
    - order_id: o.id
    - order_date: o.order_date
    - amount: o.amount
  from: c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
```

## 利点

### 1. AI解析の精度向上

**型情報による推論**
```yaml
# スキーマ情報がある場合
schema:
  tables:
    customers:
      columns:
        age:
          type: integer
          constraints:
            check: "age >= 0 AND age <= 150"

# AIは以下を理解できる：
# - ageは整数型なので、文字列比較は不適切
# - 範囲チェックが可能（0-150）
# - 算術演算が可能
```

**リレーションシップの理解**
```yaml
# スキーマ情報がある場合
schema:
  tables:
    orders:
      foreign_keys:
        - column: "customer_id"
          references:
            table: "customers"
            column: "id"

# AIは以下を理解できる：
# - customers.id = orders.customer_id のJOIN条件が正しい
# - 外部キー制約により、存在しないcustomer_idは参照できない
# - JOINの方向性（LEFT/RIGHT/INNER）の妥当性を検証可能
```

### 2. エラー検出の早期化

```yaml
# 例：型不一致の検出
query:
  select:
    - full_name: "CONCAT(c.first_name, c.age)"  # ageはinteger型
  from: c: customers

# スキーマ情報があれば、AIは以下を検出：
# - CONCATは文字列結合関数だが、ageはinteger型
# - 型キャストが必要: CONCAT(c.first_name, CAST(c.age AS VARCHAR))
```

### 3. 最適化提案

```yaml
# インデックス情報から最適化を提案
schema:
  tables:
    customers:
      indexes:
        - name: "idx_customers_status_created"
          columns: ["status", "created_at"]

# AIは以下を提案できる：
# - WHERE句でstatusとcreated_atを同時に使用すると効率的
# - ORDER BY created_atはインデックスを活用できる
```

### 4. ビジネスルールの理解

```yaml
# ENUM値やCHECK制約からビジネスルールを理解
schema:
  tables:
    orders:
      columns:
        status:
          type: enum
          values: ["draft", "pending", "confirmed", "shipped", "delivered", "cancelled"]
        amount:
          type: decimal
          constraints:
            check: "amount >= 0"

# AIは以下を理解できる：
# - statusの有効な値は定義済みの6つ
# - amountは負の値にならない
# - ステータス遷移の妥当性を検証可能
```

## 実装方針

### 1. スキーマ情報の取得

**方法A: 既存のYQLスキーマ定義から取得**
- `schemas/*.yql` ファイルから該当テーブルの定義を抽出
- 変換時に自動的に付与

**方法B: データベースから直接取得**
- INFORMATION_SCHEMAやシステムカタログから取得
- リアルタイムで最新のスキーマ情報を取得

**方法C: ハイブリッド**
- まずYQLスキーマ定義を参照
- 見つからない場合はデータベースから取得
- キャッシュして再利用

### 2. スキーマ情報の最小化

使用されているテーブルのみスキーマ情報を付与することで、ファイルサイズを抑制：

```yaml
# 使用されているテーブルのみ
schema:
  tables:
    customers: { ... }  # FROM句で使用
    orders: { ... }      # JOIN句で使用
    # products: 使用されていないので含めない
```

### 3. オプション化

スキーマ情報の付与をオプション化：

```yaml
# 変換オプション
convert_options:
  include_schema: true   # スキーマ情報を含める
  schema_level: "full"  # "full" | "minimal" | "none"
  schema_source: "yql"   # "yql" | "database" | "hybrid"
```

## 使用例

### 例1: 型チェック

```yaml
# 元のSQL
# SELECT CONCAT(name, age) FROM customers

# スキーマ情報付与YQL
schema:
  tables:
    customers:
      columns:
        name: { type: string }
        age: { type: integer }

query:
  select:
    - full_info: "CONCAT(c.name, c.age)"  # 型不一致

# AI解析結果：
# - 警告: CONCATは文字列結合関数だが、ageはinteger型
# - 推奨: CONCAT(c.name, CAST(c.age AS VARCHAR))
```

### 例2: JOIN条件の検証

```yaml
# 元のSQL
# SELECT * FROM customers c JOIN orders o ON c.id = o.customer_id

schema:
  tables:
    customers:
      columns:
        id: { type: integer, primary_key: true }
    orders:
      columns:
        customer_id: { type: integer }
      foreign_keys:
        - column: "customer_id"
          references: { table: "customers", column: "id" }

query:
  from: c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"

# AI解析結果：
# - JOIN条件が正しい（外部キー関係と一致）
# - 型も一致（両方integer）
# - インデックスが存在するため、パフォーマンス良好
```

### 例3: 制約違反の検出

```yaml
# 元のSQL
# SELECT * FROM orders WHERE amount < 0

schema:
  tables:
    orders:
      columns:
        amount:
          type: decimal
          constraints:
            check: "amount >= 0"

query:
  select:
    - "*": "*"
  from: orders
  where:
    - "amount < 0"

# AI解析結果：
# - 警告: amountにはCHECK制約（amount >= 0）があるため、この条件は常にfalse
# - 推奨: このWHERE条件は不要（制約により保証されている）
```

## 課題と対策

### 課題1: ファイルサイズの増大

**対策**:
- 使用されているテーブルのみスキーマ情報を付与
- 必要最小限の情報のみ含める（`schema_level: "minimal"`）
- スキーマ情報を別ファイルに分離し、参照のみ含める

### 課題2: スキーマ情報の更新

**対策**:
- スキーマ情報にバージョン情報を含める
- 変換時にスキーマ情報の整合性をチェック
- スキーマ情報のキャッシュと更新メカニズム

### 課題3: パフォーマンス

**対策**:
- スキーマ情報の取得を非同期化
- スキーマ情報のキャッシュ
- 必要に応じてスキーマ情報を省略可能にする

## まとめ

SQL→YQL変換時にスキーマ情報を付与することで：

1. **AI解析の精度向上**: 型情報、制約、リレーションシップを理解
2. **エラー検出の早期化**: 型不一致、制約違反を事前に検出
3. **最適化提案**: インデックス情報から最適化を提案
4. **意味理解**: ビジネスルールを理解し、より適切なクエリを生成

このアプローチにより、YQLは単なるクエリ構造だけでなく、**データベースの意味情報を含む包括的なドキュメント**として機能するようになります。

