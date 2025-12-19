# YQL DELETE文 変換ルール仕様書

## 1. 概要

このドキュメントは、YQLのDELETE文を各データベース方言のSQLに変換する際のルールを定義します。

### 1.1 対応データベース

- PostgreSQL
- MySQL
- SQL Server (MSSQL)
- Oracle (将来対応)

### 1.2 変換の基本方針

- YQLの抽象構文を各DBの標準SQL構文に変換
- 可能な限り標準SQL準拠の構文を使用
- DB固有の最適化は最小限に留める
- パラメーターバインディングは必ずPreparedStatement形式を使用
- **WHERE句がない場合はエラーを発生（安全のため）**

## 2. 基本DELETE文の変換

### 2.1 単一テーブルのDELETE

#### YQL構文
```yaml
operation: delete
table: table_name
where:
  - "condition1"
  - "condition2"
```

#### 変換ルール

**全DB共通:**
```sql
DELETE FROM table_name
WHERE condition1
  AND condition2
```

**生成例:**
```sql
-- YQL:
-- operation: delete
-- table: customers
-- where:
--   - "status = 'deleted'"
--   - "deleted_at < DATE('now', '-1 year')"

-- PostgreSQL/MySQL/SQL Server:
DELETE FROM customers
WHERE status = 'deleted'
  AND deleted_at < DATE('now', '-1 year')
```

**注意事項:**
- WHERE句は`specs/select.md`の6.1章と同じ形式
- **WHERE句がない場合はエラーを発生（安全のため）**
- 論理削除を推奨（物理削除は慎重に）

### 2.2 サブクエリを使ったDELETE

#### YQL構文
```yaml
operation: delete
table: table_name
where:
  - field: id
    operator: IN
    subquery:
      select:
        - id: o.id
      from: o: other_table
      where:
        - "condition"
```

#### 変換ルール

**全DB共通:**
```sql
DELETE FROM table_name
WHERE id IN (
  SELECT id AS id
  FROM other_table
  WHERE condition
)
```

**注意事項:**
- サブクエリは`specs/select.md`の仕様に従う
- EXISTS句も使用可能

## 3. JOINを使ったDELETE

JOINを使ったDELETEは、YQLでは統一的な`joins:`構文を使用し、パーサーがDB方言の違いを吸収します。

### 3.1 YQL構文（統一形式）

```yaml
operation: delete
table: t1: table1
joins:
  - type: INNER
    alias: t2
    table: table2
    on: "t1.id = t2.id"
where:
  - "t2.status = 'inactive'"
```

### 3.2 変換ルール（DB方言別）

**MySQL:**
```sql
DELETE t1
FROM table1 t1
INNER JOIN table2 t2 ON t1.id = t2.id
WHERE t2.status = 'inactive'
```

**SQL Server:**
```sql
DELETE t1
FROM table1 t1
INNER JOIN table2 t2 ON t1.id = t2.id
WHERE t2.status = 'inactive'
```

**PostgreSQL:**
```sql
DELETE FROM table1 t1
USING table2 t2
WHERE t1.id = t2.id
  AND t2.status = 'inactive'
```

### 3.3 複数テーブルのJOIN

#### YQL構文
```yaml
operation: delete
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
where:
  - "t2.status = 'inactive'"
  - "t3.id IS NULL"
```

**注意事項:**
- YQLでは`joins:`構文に統一
- パーサーがDB方言に応じて適切なSQLを生成
- PostgreSQLではUSING句に変換、JOIN条件はWHERE句に移動
- テーブルエイリアスは`specs/select.md`と同じ形式（`alias: table_name`）
- MySQLでは複数テーブルを削除する場合は`DELETE t1, t2`の形式に変換

## 4. LIMIT句の変換

### 4.1 MySQL: LIMIT句

#### YQL構文
```yaml
operation: delete
table: table_name
where:
  - "status = 'deleted'"
limit: 100
```

#### 変換ルール

**MySQL:**
```sql
DELETE FROM table_name
WHERE status = 'deleted'
LIMIT 100
```

**注意事項:**
- MySQLのみサポート
- PostgreSQL、SQL Serverでは使用不可（ORDER BYと組み合わせて実現）

## 5. ORDER BY句の変換（LIMITと組み合わせ）

### 5.1 MySQL: ORDER BY + LIMIT

#### YQL構文
```yaml
operation: delete
table: table_name
where:
  - "status = 'deleted'"
order_by:
  - field: created_at
    direction: ASC
limit: 10
```

#### 変換ルール

**MySQL:**
```sql
DELETE FROM table_name
WHERE status = 'deleted'
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
operation: delete
table: table_name
where:
  - "id = #{id}"
returning: [id, name, deleted_at]
```

#### 変換ルール

**PostgreSQL:**
```sql
DELETE FROM table_name
WHERE id = ?
RETURNING id, name, deleted_at
```

**注意事項:**
- PostgreSQLのみサポート
- MySQL、SQL Serverでは使用不可（別途SELECT文が必要）

## 7. import機能の利用

DELETE文でもimport機能を利用できます。詳細は`specs/import.md`を参照してください。

### 7.1 スキーマ定義のimport

スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照できます。

#### YQL構文
```yaml
imports:
  - "schemas/ecommerce.yql"

operation: delete
table: customers  # importしたスキーマ定義からテーブルを参照
where:
  - "id = #{id}"
  - "status = 'deleted'"
```

**注意事項:**
- スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照可能
- 型チェックやバリデーションに使用
- SQL生成時には直接的な変換は不要（型チェックに使用）

### 7.2 SELECT定義のimport（サブクエリとして使用）

DELETE文のWHERE句で、importしたSELECT定義をサブクエリとして使用できます。

#### 定義ファイル（`queries/inactive_customer_ids.yql`）
```yaml
name: "inactive_customer_ids"
description: "非アクティブな顧客IDを取得するSELECT定義"

select_definition:
  select:
    - customer_id: c.customer_id
  from: c: customers
  where:
    - "c.status = 'inactive'"
    - "c.last_login_date < DATE('now', '-1 year')"
```

#### 使用ファイル
```yaml
imports:
  - "queries/inactive_customer_ids.yql"

operation: delete
table: orders
where:
  - field: customer_id
    operator: IN
    subquery:
      using: "inactive_customer_ids"  # importしたSELECT定義を参照
```

**注意事項:**
- SELECT定義はサブクエリとして展開される
- WHERE句のIN句やEXISTS句で使用可能
- 詳細は`specs/import.md`を参照

## 8. 論理削除（推奨）

### 8.1 論理削除の実装

#### YQL構文
```yaml
operation: update  # DELETEではなくUPDATEを使用
table: table_name
set:
  deleted_at: "CURRENT_TIMESTAMP"
  deleted_by: "#{userId}"
  status: "deleted"
where:
  - "id = #{id}"
  - "deleted_at IS NULL"  # 既に削除されていないことを確認
```

#### 変換ルール

**全DB共通:**
```sql
UPDATE table_name
SET
  deleted_at = CURRENT_TIMESTAMP,
  deleted_by = ?,
  status = 'deleted'
WHERE id = ?
  AND deleted_at IS NULL
```

**注意事項:**
- 論理削除を推奨（物理削除は慎重に）
- `deleted_at`カラムで削除状態を管理
- SELECT文では`WHERE deleted_at IS NULL`を条件に追加

## 9. パラメータバインディング

### 9.1 パラメータ記法

#### YQL構文
```yaml
operation: delete
table: table_name
where:
  - "id = #{id}"                     # 単一値パラメータ
  - "status = #{status}"
  - "id IN (${ids})"                 # 配列パラメータ
```

#### 変換ルール

**パラメータ記法の使い分け:**

1. **`#{paramName}` - 単一値パラメータ（値のバインド）**
   - `#{paramName}` → `?` (PreparedStatement)
   - パラメータ名はキャメルケースからスネークケースに変換
   - SQL文内で値として使用されるパラメータ

2. **`${paramArray}` - 配列パラメータ（配列の展開）**
   - `IN (${paramArray})` → `IN (?, ?, ?)` (要素数に応じて展開)
   - 配列をIN句などで展開する場合に使用

**注意事項:**
- `#{paramName}`は必ずPreparedStatement形式でバインド
- `${paramArray}`は配列を展開して複数の`?`に変換
- SQLインジェクション対策のため、文字列連結は禁止

## 10. エラーハンドリング

### 10.1 変換エラー

以下の場合にエラーを発生:

1. **未定義テーブル/カラム**
   - スキーマ定義に存在しないテーブル/カラムを参照

2. **WHERE句なし**
   - **WHERE句がない場合はエラーを発生（安全のため）**

3. **構文エラー**
   - YQL構文が不正

4. **外部キー制約違反**
   - 参照されているレコードを削除しようとした場合

### 10.2 警告

以下の場合に警告を出力:

1. **大量データの削除**
   - 影響行数が大きすぎる場合

2. **パフォーマンスに影響する可能性のある操作**
   - インデックスが使用されない可能性のある条件

3. **物理削除の使用**
   - 論理削除を推奨

## 11. 実装時の注意事項

### 11.1 安全なDELETE

- **WHERE句がない場合はエラーを発生（安全のため）**
- 実装時に`require_where`オプションで強制
- 論理削除を推奨

### 11.2 トランザクション

- DELETEは1つのトランザクションで処理
- エラー時はロールバック

### 11.3 ロック

- 必要に応じて行ロックを取得
- デッドロックを避けるため、削除順序を考慮

### 11.4 カスケード削除

- 外部キー制約のカスケード削除に注意
- 実装時にカスケード削除の動作を確認

### 11.5 import機能の詳細

import機能の詳細については、`specs/import.md`を参照してください。

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト
