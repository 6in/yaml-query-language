# YQL UPSERT文 変換ルール仕様書

## 1. 概要

このドキュメントは、YQLのUPSERT文（INSERT ... ON CONFLICT / ON DUPLICATE KEY UPDATE / MERGE）を各データベース方言のSQLに変換する際のルールを定義します。

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
- UPSERTは「存在すれば更新、存在しなければ挿入」の操作

## 2. PostgreSQL: INSERT ... ON CONFLICT

### 2.1 基本構文

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  id: 1
  name: "John Doe"
  email: "john@example.com"
on_conflict:
  target: [id]  # または unique_constraint: "constraint_name"
  action: update  # または ignore
  update:
    name: "EXCLUDED.name"
    email: "EXCLUDED.email"
    updated_at: "CURRENT_TIMESTAMP"
```

#### 変換ルール

**PostgreSQL:**
```sql
INSERT INTO table_name (id, name, email)
VALUES (1, 'John Doe', 'john@example.com')
ON CONFLICT (id)
DO UPDATE SET
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  updated_at = CURRENT_TIMESTAMP
```

**action: ignore の場合:**
```sql
INSERT INTO table_name (id, name, email)
VALUES (1, 'John Doe', 'john@example.com')
ON CONFLICT (id)
DO NOTHING
```

**注意事項:**
- `target`は競合を検出するカラムまたはUNIQUE制約名
- `EXCLUDED`は挿入しようとした値にアクセスするためのキーワード
- `action: ignore`の場合は更新しない（挿入のみ）

### 2.2 条件付きUPDATE

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  id: 1
  name: "John Doe"
  version: 2
on_conflict:
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
    version: "EXCLUDED.version"
  where: "table_name.version < EXCLUDED.version"  # 条件付き更新
```

#### 変換ルール

**PostgreSQL:**
```sql
INSERT INTO table_name (id, name, version)
VALUES (1, 'John Doe', 2)
ON CONFLICT (id)
DO UPDATE SET
  name = EXCLUDED.name,
  version = EXCLUDED.version
WHERE table_name.version < EXCLUDED.version
```

**注意事項:**
- `where`句で更新条件を指定可能
- 条件が満たされない場合は更新しない

## 3. MySQL: INSERT ... ON DUPLICATE KEY UPDATE

### 3.1 基本構文

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  id: 1
  name: "John Doe"
  email: "john@example.com"
on_duplicate_key:
  update:
    name: "VALUES(name)"
    email: "VALUES(email)"
    updated_at: "CURRENT_TIMESTAMP"
```

#### 変換ルール

**MySQL:**
```sql
INSERT INTO table_name (id, name, email)
VALUES (1, 'John Doe', 'john@example.com')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  email = VALUES(email),
  updated_at = CURRENT_TIMESTAMP
```

**注意事項:**
- MySQL 8.0.20以降では`VALUES()`の代わりに`NEW.column_name`を使用可能
- 実装時はMySQLのバージョンを考慮
- PRIMARY KEYまたはUNIQUE制約に違反した場合に更新が実行される

### 3.2 複数行のUPSERT

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  - id: 1
    name: "John Doe"
    email: "john@example.com"
  - id: 2
    name: "Jane Smith"
    email: "jane@example.com"
on_duplicate_key:
  update:
    name: "VALUES(name)"
    email: "VALUES(email)"
    updated_at: "CURRENT_TIMESTAMP"
```

#### 変換ルール

**MySQL:**
```sql
INSERT INTO table_name (id, name, email)
VALUES (1, 'John Doe', 'john@example.com'), (2, 'Jane Smith', 'jane@example.com')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  email = VALUES(email),
  updated_at = CURRENT_TIMESTAMP
```

**注意事項:**
- 複数行を1つのINSERT文で処理可能
- 各行に対して個別にUPSERTが実行される

## 4. SQL Server: MERGE文

### 4.1 基本構文

#### YQL構文
```yaml
operation: upsert
table: target: table_name
using:
  select:
    - id: 1
    - name: "John Doe"
    - email: "john@example.com"
  from: dual  # または実際のテーブル
match_on: [id]
when_matched:
  update:
    name: "source.name"
    email: "source.email"
    updated_at: "CURRENT_TIMESTAMP"
when_not_matched:
  insert:
    id: "source.id"
    name: "source.name"
    email: "source.email"
```

#### 変換ルール

**SQL Server:**
```sql
MERGE table_name AS target
USING (SELECT 1 AS id, 'John Doe' AS name, 'john@example.com' AS email) AS source
ON target.id = source.id
WHEN MATCHED THEN
  UPDATE SET
    name = source.name,
    email = source.email,
    updated_at = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
  INSERT (id, name, email)
  VALUES (source.id, source.name, source.email);
```

**注意事項:**
- SQL ServerではMERGE文を使用
- `using`句内のSELECT文は、`specs/select.md`の仕様に従う
- `match_on`は結合条件を指定

### 4.2 条件付きUPDATE/DELETE

#### YQL構文
```yaml
operation: upsert
table: target: table_name
using:
  select:
    - id: 1
    - name: "John Doe"
  from: s: source_table
match_on: [id]
when_matched:
  update:
    name: "source.name"
  where: "target.version < source.version"  # 条件付き更新
when_not_matched:
  insert:
    id: "source.id"
    name: "source.name"
```

#### 変換ルール

**SQL Server:**
```sql
MERGE table_name AS target
USING source_table AS source
ON target.id = source.id
WHEN MATCHED AND target.version < source.version THEN
  UPDATE SET name = source.name
WHEN NOT MATCHED THEN
  INSERT (id, name)
  VALUES (source.id, source.name);
```

**注意事項:**
- `when_matched`に`where`句で条件を指定可能
- 条件が満たされない場合は更新しない

## 5. バッチUPSERT

### 5.1 複数行のUPSERT

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  - id: 1
    name: "John Doe"
    email: "john@example.com"
  - id: 2
    name: "Jane Smith"
    email: "jane@example.com"
on_conflict:  # PostgreSQL
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
    email: "EXCLUDED.email"
```

#### 変換ルール

**PostgreSQL:**
```sql
INSERT INTO table_name (id, name, email)
VALUES (1, 'John Doe', 'john@example.com'), (2, 'Jane Smith', 'jane@example.com')
ON CONFLICT (id)
DO UPDATE SET
  name = EXCLUDED.name,
  email = EXCLUDED.email
```

**MySQL:**
```sql
INSERT INTO table_name (id, name, email)
VALUES (1, 'John Doe', 'john@example.com'), (2, 'Jane Smith', 'jane@example.com')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  email = VALUES(email)
```

**SQL Server:**
```sql
MERGE table_name AS target
USING (VALUES (1, 'John Doe', 'john@example.com'), (2, 'Jane Smith', 'jane@example.com')) AS source (id, name, email)
ON target.id = source.id
WHEN MATCHED THEN
  UPDATE SET name = source.name, email = source.email
WHEN NOT MATCHED THEN
  INSERT (id, name, email) VALUES (source.id, source.name, source.email);
```

**注意事項:**
- バッチサイズは実装時に調整可能
- 大量データの場合は、バッチに分割して処理

## 6. SELECT句からのUPSERT

### 6.1 PostgreSQL/MySQL

#### YQL構文
```yaml
operation: upsert
table: table_name
columns: [id, name, email]
from_query:
  select:
    - id: s.source_id
    - name: s.source_name
    - email: s.source_email
  from: s: source_table
  where:
    - "condition"
on_conflict:  # PostgreSQL
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
    email: "EXCLUDED.email"
```

#### 変換ルール

**PostgreSQL:**
```sql
INSERT INTO table_name (id, name, email)
SELECT source_id AS id, source_name AS name, source_email AS email
FROM source_table
WHERE condition
ON CONFLICT (id)
DO UPDATE SET
  name = EXCLUDED.name,
  email = EXCLUDED.email
```

**MySQL:**
```sql
INSERT INTO table_name (id, name, email)
SELECT source_id AS id, source_name AS name, source_email AS email
FROM source_table
WHERE condition
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  email = VALUES(email)
```

**注意事項:**
- `from_query`内のSELECT文は、`specs/select.md`の仕様に従う

## 7. RETURNING句の変換

### 7.1 PostgreSQL: RETURNING句

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  id: 1
  name: "John Doe"
on_conflict:
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
returning: [id, name, updated_at]
```

#### 変換ルール

**PostgreSQL:**
```sql
INSERT INTO table_name (id, name)
VALUES (1, 'John Doe')
ON CONFLICT (id)
DO UPDATE SET name = EXCLUDED.name
RETURNING id, name, updated_at
```

**注意事項:**
- PostgreSQLのみサポート
- MySQL、SQL Serverでは使用不可（別途SELECT文が必要）

## 8. import機能の利用

UPSERT文でもimport機能を利用できます。詳細は`specs/import.md`を参照してください。

### 8.1 スキーマ定義のimport

スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照できます。

#### YQL構文
```yaml
imports:
  - "schemas/ecommerce.yql"

operation: upsert
table: customers  # importしたスキーマ定義からテーブルを参照
values:
  id: "#{id}"
  name: "#{customerName}"
  email: "#{customerEmail}"
on_conflict:
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
    email: "EXCLUDED.email"
```

**注意事項:**
- スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照可能
- 型チェックやバリデーションに使用
- SQL生成時には直接的な変換は不要（型チェックに使用）

### 8.2 マクロ（カラム定義）のimport

複雑な式をマクロとして定義し、VALUES句やUPDATE句で使用できます。

#### 定義ファイル（`macros/timestamp_macros.yql`）
```yaml
name: "current_timestamp"
description: "現在時刻を取得するマクロ"

column_definition:
  expression: "CURRENT_TIMESTAMP"
  parameters: {}
```

#### 使用ファイル
```yaml
imports:
  - "macros/timestamp_macros.yql"

operation: upsert
table: customers
values:
  id: "#{id}"
  name: "#{customerName}"
  created_at: "@current_timestamp"  # マクロを参照
on_conflict:
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
    updated_at: "@current_timestamp"  # マクロを参照
```

**注意事項:**
- マクロは式として展開される
- VALUES句やUPDATE句で式として使用可能
- パラメータ付きマクロも使用可能（詳細は`specs/import.md`を参照）

### 8.3 SELECT定義のimport（from_queryとして使用）

UPSERT文の`from_query`で、importしたSELECT定義を使用できます。

#### 定義ファイル（`queries/customer_summary.yql`）
```yaml
name: "customer_summary"
description: "顧客サマリーを取得するSELECT定義"

select_definition:
  select:
    - customer_id: c.customer_id
    - total_orders: "COUNT(o.order_id)"
    - total_amount: "SUM(o.amount)"
  from: c: customers
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  group_by:
    - c.customer_id
```

#### 使用ファイル
```yaml
imports:
  - "queries/customer_summary.yql"

operation: upsert
table: customer_stats
columns: [customer_id, total_orders, total_amount]
from_query:
  using: "customer_summary"  # importしたSELECT定義を参照
on_conflict:
  target: [customer_id]
  action: update
  update:
    total_orders: "EXCLUDED.total_orders"
    total_amount: "EXCLUDED.total_amount"
    updated_at: "CURRENT_TIMESTAMP"
```

**注意事項:**
- SELECT定義は`from_query`として展開される
- INSERT ... SELECT ... ON CONFLICT の形式に変換
- 詳細は`specs/import.md`を参照

## 9. パラメータバインディング

### 9.1 パラメータ記法

#### YQL構文
```yaml
operation: upsert
table: table_name
values:
  id: "#{id}"                        # 単一値パラメータ
  name: "#{name}"
  email: "#{email}"
on_conflict:
  target: [id]
  action: update
  update:
    name: "EXCLUDED.name"
    email: "EXCLUDED.email"
```

#### 変換ルール

**パラメータ記法の使い分け:**

1. **`#{paramName}` - 単一値パラメータ（値のバインド）**
   - `#{paramName}` → `?` (PreparedStatement)
   - パラメータ名はキャメルケースからスネークケースに変換
   - SQL文内で値として使用されるパラメータ

2. **`${paramArray}` - 配列パラメータ（バッチUPSERT）**
   - 配列を複数行のUPSERTに展開
   - 例: `values: "${customers}"` → 複数行のVALUES句に展開

**注意事項:**
- `#{paramName}`は必ずPreparedStatement形式でバインド
- `${paramArray}`は配列を展開して複数行のUPSERTに変換
- SQLインジェクション対策のため、文字列連結は禁止

## 10. エラーハンドリング

### 10.1 変換エラー

以下の場合にエラーを発生:

1. **未定義テーブル/カラム**
   - スキーマ定義に存在しないテーブル/カラムを参照

2. **型不一致**
   - 値の型がカラムの型と一致しない

3. **制約違反**
   - NOT NULL制約、CHECK制約の違反

4. **構文エラー**
   - YQL構文が不正

### 10.2 警告

以下の場合に警告を出力:

1. **大量データのUPSERT**
   - バッチサイズが大きすぎる場合

2. **パフォーマンスに影響する可能性のある操作**
   - インデックスが使用されない可能性のある条件

## 11. 実装時の注意事項

### 11.1 バッチサイズの制限

- 大量データのUPSERT時は、バッチサイズを制限
- デフォルトバッチサイズ: 1000行（実装時に調整可能）

### 11.2 トランザクション

- UPSERTは1つのトランザクションで処理
- エラー時はロールバック

### 11.3 競合の処理

- 複数のUPSERTが同時に実行される場合、競合が発生する可能性がある
- 実装時にロック戦略を考慮

### 11.4 ロック

- 必要に応じて行ロックを取得
- デッドロックを避けるため、更新順序を考慮

### 11.5 import機能の詳細

import機能の詳細については、`specs/import.md`を参照してください。

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト
