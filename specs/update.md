# YQL UPDATE文 変換ルール仕様書

## 1. 概要

このドキュメントは、YQLのUPDATE文を各データベース方言のSQLに変換する際のルールを定義します。

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
- WHERE句がない場合は警告を出力（安全のため）

## 2. 基本UPDATE文の変換

### 2.1 単一テーブルのUPDATE

#### YQL構文
```yaml
operation: update
table: table_name
set:
  column1: value1
  column2: "expression"
  column3: "#{paramName}"
where:
  - "condition1"
  - "condition2"
```

#### 変換ルール

**全DB共通:**
```sql
UPDATE table_name
SET
  column1 = value1,
  column2 = expression,
  column3 = ?
WHERE condition1
  AND condition2
```

**生成例:**
```sql
-- YQL:
-- operation: update
-- table: customers
-- set:
--   status: "inactive"
--   updated_at: "CURRENT_TIMESTAMP"
-- where:
--   - "last_login_date < DATE('now', '-6 months')"

-- PostgreSQL/MySQL/SQL Server/Oracle:
UPDATE customers
SET
  status = 'inactive',
  updated_at = CURRENT_TIMESTAMP
WHERE last_login_date < DATE('now', '-6 months')
```

**注意事項:**
- `set`句はYAMLのマッピング形式で記述
- 式は文字列として記述（例: `"CURRENT_TIMESTAMP"`）
- WHERE句は`specs/select.md`の6.1章と同じ形式
- WHERE句がない場合は警告を出力（安全のため）

### 2.2 式を使ったUPDATE

#### YQL構文
```yaml
operation: update
table: table_name
set:
  quantity: "quantity - #{decrement}"
  total: "quantity * unit_price"
  updated_at: "CURRENT_TIMESTAMP"
where:
  - "id = #{id}"
```

#### 変換ルール

**全DB共通:**
```sql
UPDATE table_name
SET
  quantity = quantity - ?,
  total = quantity * unit_price,
  updated_at = CURRENT_TIMESTAMP
WHERE id = ?
```

**注意事項:**
- 式内で既存のカラム値を参照可能
- パラメータは`#{paramName}`形式で記述

### 2.3 サブクエリを使ったUPDATE

#### YQL構文
```yaml
operation: update
table: table_name
set:
  last_order_date: "(SELECT MAX(order_date) FROM orders WHERE customer_id = table_name.id)"
where:
  - "id = #{customerId}"
```

#### 変換ルール

**全DB共通:**
```sql
UPDATE table_name
SET
  last_order_date = (SELECT MAX(order_date) FROM orders WHERE customer_id = table_name.id)
WHERE id = ?
```

**注意事項:**
- サブクエリはスカラー値を返す必要がある
- 相関サブクエリとして使用可能

## 3. JOINを使ったUPDATE

JOINを使ったUPDATEは、YQLでは統一的な`joins:`構文を使用し、パーサーがDB方言の違いを吸収します。

### 3.1 YQL構文（統一形式）

```yaml
operation: update
table: t1: table1
joins:
  - type: INNER
    alias: t2
    table: table2
    on: "t1.id = t2.id"
set:
  t1.column1: "t2.column2"
  t1.updated_at: "CURRENT_TIMESTAMP"
where:
  - "t2.status = 'active'"
```

### 3.2 変換ルール（DB方言別）

**MySQL:**
```sql
UPDATE table1 t1
INNER JOIN table2 t2 ON t1.id = t2.id
SET
  t1.column1 = t2.column2,
  t1.updated_at = CURRENT_TIMESTAMP
WHERE t2.status = 'active'
```

**SQL Server:**
```sql
UPDATE t1
SET
  t1.column1 = t2.column2,
  t1.updated_at = CURRENT_TIMESTAMP
FROM table1 t1
INNER JOIN table2 t2 ON t1.id = t2.id
WHERE t2.status = 'active'
```

**PostgreSQL:**
```sql
UPDATE table1 t1
SET
  column1 = t2.column2,
  updated_at = CURRENT_TIMESTAMP
FROM table2 t2
WHERE t1.id = t2.id
  AND t2.status = 'active'
```

### 3.3 複数テーブルのJOIN

#### YQL構文
```yaml
operation: update
table: t1: table1
joins:
  - type: INNER
    alias: t2
    table: table2
    on: "t1.id = t2.id"
  - type: LEFT
    alias: t3
    table: table3
    on: "t2.ref_id = t3.id"
set:
  t1.column1: "t2.column2"
  t1.column2: "COALESCE(t3.column3, 'default')"
where:
  - "t2.status = 'active'"
```

**注意事項:**
- YQLでは`joins:`構文に統一
- パーサーがDB方言に応じて適切なSQLを生成
- PostgreSQLではFROM句に変換、JOIN条件はWHERE句に移動
- テーブルエイリアスは`specs/select.md`と同じ形式（`alias: table_name`）

## 4. LIMIT句の変換

### 4.1 MySQL: LIMIT句

#### YQL構文
```yaml
operation: update
table: table_name
set:
  status: "processed"
where:
  - "status = 'pending'"
limit: 100
```

#### 変換ルール

**MySQL:**
```sql
UPDATE table_name
SET status = 'processed'
WHERE status = 'pending'
LIMIT 100
```

**注意事項:**
- MySQLのみサポート
- PostgreSQL、SQL Serverでは使用不可（ORDER BYと組み合わせて実現）

## 5. ORDER BY句の変換（LIMITと組み合わせ）

### 5.1 MySQL: ORDER BY + LIMIT

#### YQL構文
```yaml
operation: update
table: table_name
set:
  priority: 1
where:
  - "status = 'pending'"
order_by:
  - field: created_at
    direction: ASC
limit: 10
```

#### 変換ルール

**MySQL:**
```sql
UPDATE table_name
SET priority = 1
WHERE status = 'pending'
ORDER BY created_at ASC
LIMIT 10
```

**注意事項:**
- MySQLのみサポート
- PostgreSQL、SQL Serverでは使用不可

## 6. RETURNING句の変換

### 6.1 PostgreSQL: RETURNING句

#### YQL構文
```yaml
operation: update
table: table_name
set:
  status: "inactive"
where:
  - "id = #{id}"
returning: [id, name, status, updated_at]
```

#### 変換ルール

**PostgreSQL:**
```sql
UPDATE table_name
SET status = 'inactive'
WHERE id = ?
RETURNING id, name, status, updated_at
```

**注意事項:**
- PostgreSQLのみサポート
- MySQL、SQL Server、Oracleでは使用不可（別途SELECT文が必要）
- Oracleでは`RETURNING INTO`を使用可能だが、ストアドプロシージャ内での使用が一般的なため、YQLではサポートしない

## 7. import機能の利用

UPDATE文でもimport機能を利用できます。詳細は`specs/import.md`を参照してください。

### 7.1 スキーマ定義のimport

スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照できます。

#### YQL構文
```yaml
imports:
  - "schemas/ecommerce.yql"

operation: update
table: customers  # importしたスキーマ定義からテーブルを参照
set:
  name: "#{customerName}"
  email: "#{customerEmail}"
  status: "#{status:active}"
where:
  - "id = #{id}"
```

**注意事項:**
- スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照可能
- 型チェックやバリデーションに使用
- SQL生成時には直接的な変換は不要（型チェックに使用）

### 7.2 マクロ（カラム定義）のimport

複雑な式をマクロとして定義し、SET句で使用できます。

#### 定義ファイル（`macros/updated_timestamp.yql`）
```yaml
name: "updated_timestamp"
description: "更新時刻を取得するマクロ"

column_definition:
  expression: "CURRENT_TIMESTAMP"
  parameters: {}
```

#### 使用ファイル
```yaml
imports:
  - "macros/updated_timestamp.yql"

operation: update
table: customers
set:
  name: "#{customerName}"
  email: "#{customerEmail}"
  updated_at: "@updated_timestamp"  # マクロを参照
where:
  - "id = #{id}"
```

**注意事項:**
- マクロは式として展開される
- SET句で式として使用可能
- パラメータ付きマクロも使用可能（詳細は`specs/import.md`を参照）

### 7.3 SELECT定義のimport（サブクエリとして使用）

UPDATE文のWHERE句で、importしたSELECT定義をサブクエリとして使用できます。

#### 定義ファイル（`queries/active_customer_ids.yql`）
```yaml
name: "active_customer_ids"
description: "アクティブな顧客IDを取得するSELECT定義"

select_definition:
  select:
    - customer_id: c.customer_id
  from: c: customers
  where:
    - "c.status = 'active'"
```

#### 使用ファイル
```yaml
imports:
  - "queries/active_customer_ids.yql"

operation: update
table: orders
set:
  status: "processed"
where:
  - field: customer_id
    operator: IN
    subquery:
      using: "active_customer_ids"  # importしたSELECT定義を参照
```

**注意事項:**
- SELECT定義はサブクエリとして展開される
- WHERE句のIN句やEXISTS句で使用可能
- 詳細は`specs/import.md`を参照

## 8. パラメータ

### 8.1 パラメータによる条件付きUPDATE

**重要:** パラメータによる分岐は、テンプレートエンジン（MyBatis、JinjaSQL等）の形式として出力されます。動的SQLの生成はテンプレートエンジンに任せます。

#### YQL構文
```yaml
operation: update
table: table_name
set:
  status: "#{status}"
  - if: "${updateName}"
    then:
      name: "#{name}"
  - if: "${updateEmail}"
    then:
      email: "#{email}"
where:
  - "id = #{id}"
```

#### 変換ルール

**MyBatis XML生成例:**
```xml
<update id="updateCustomer">
  UPDATE table_name
  SET
    status = #{status}
    <if test="updateName != null and updateName">
      , name = #{name}
    </if>
    <if test="updateEmail != null and updateEmail">
      , email = #{email}
    </if>
  WHERE id = #{id}
</update>
```

**注意事項:**
- パラメータによる分岐はSET句でも許可
- **動的SQLの生成はテンプレートエンジンに任せます**（YQLパーサーはテンプレート形式を出力するのみ）

### 8.2 パラメータバインディング

#### YQL構文
```yaml
operation: update
table: table_name
set:
  name: "#{customerName}"           # 単一値パラメータ
  email: "#{customerEmail}"
  status: "#{status:active}"        # デフォルト値付き
  - if: "${updateName}"              # 条件分岐用パラメータ
    then:
      name: "#{name}"
where:
  - "id = #{customerId}"
```

#### 変換ルール

**パラメータ記法の使い分け:**

1. **`#{paramName}` - 単一値パラメータ（値のバインド）**
   - `#{paramName}` → `?` (PreparedStatement)
   - パラメータ名はキャメルケースからスネークケースに変換
   - SQL文内で値として使用されるパラメータ

2. **`#{paramName:defaultValue}` - デフォルト値付きパラメータ**
   - パラメータがnullの場合、デフォルト値を使用
   - 例: `status: "#{status:active}"`

3. **`${paramName}` - 条件分岐用パラメータ（テンプレートエンジン用）**
   - 条件分岐（if句など）で使用
   - テンプレートエンジン（MyBatis、JinjaSQL等）の形式として出力
   - 値のバインドには使用しない
   - 例: `if: "${updateName}"`

**注意事項:**
- `#{paramName}`は必ずPreparedStatement形式でバインド
- `${paramName}`は条件分岐用で、値のバインドには使用しない
- SQLインジェクション対策のため、文字列連結は禁止

## 9. エラーハンドリング

### 9.1 変換エラー

以下の場合にエラーを発生:

1. **未定義テーブル/カラム**
   - スキーマ定義に存在しないテーブル/カラムを参照

2. **型不一致**
   - 値の型がカラムの型と一致しない

3. **制約違反**
   - NOT NULL制約、CHECK制約、UNIQUE制約の違反

4. **構文エラー**
   - YQL構文が不正

5. **WHERE句なし**
   - WHERE句がない場合は警告を出力（安全のため）

### 9.2 警告

以下の場合に警告を出力:

1. **WHERE句がない**
   - 全件更新の可能性がある場合

2. **大量データの更新**
   - 影響行数が大きすぎる場合

3. **パフォーマンスに影響する可能性のある操作**
   - インデックスが使用されない可能性のある条件

## 10. 実装時の注意事項

### 10.1 安全なUPDATE

- WHERE句がない場合は警告を出力
- 実装時に`require_where`オプションで強制可能

### 10.2 トランザクション

- UPDATEは1つのトランザクションで処理
- エラー時はロールバック

### 10.3 ロック

- 必要に応じて行ロックを取得
- デッドロックを避けるため、更新順序を考慮

### 10.4 import機能の詳細

import機能の詳細については、`specs/import.md`を参照してください。

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト
