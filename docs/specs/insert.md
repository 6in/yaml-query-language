# YQL INSERT文 変換ルール仕様書

## 1. 概要

このドキュメントは、YQLのINSERT文を各データベース方言のSQLに変換する際のルールを定義します。

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
- バッチ挿入は効率的に処理

## 2. 基本INSERT文の変換

### 2.1 単一行INSERT（VALUES句）

#### YQL構文
```yaml
operation: insert
table: table_name
values:
  column1: value1
  column2: value2
  column3: "expression"
```

#### 変換ルール

**全DB共通:**
```sql
INSERT INTO table_name (column1, column2, column3)
VALUES (value1, value2, expression)
```

**生成例:**
```sql
-- YQL:
-- operation: insert
-- table: customers
-- values:
--   name: "John Doe"
--   email: "john@example.com"
--   status: "active"

-- PostgreSQL/MySQL/SQL Server/Oracle:
INSERT INTO customers (name, email, status)
VALUES ('John Doe', 'john@example.com', 'active')
```

**注意事項:**
- カラム名と値のペアをYAMLのマッピング形式で記述
- 式は文字列として記述（例: `"CURRENT_TIMESTAMP"`）
- パラメータは`#{paramName}`形式で記述

### 2.2 複数行INSERT（バッチ挿入）

#### YQL構文
```yaml
operation: insert
table: table_name
values:
  - column1: value1
    column2: value2
  - column1: value3
    column2: value4
```

#### 変換ルール

**PostgreSQL/MySQL/Oracle:**
```sql
INSERT INTO table_name (column1, column2)
VALUES (value1, value2), (value3, value4)
```

**SQL Server:**
```sql
INSERT INTO table_name (column1, column2)
VALUES (value1, value2);
INSERT INTO table_name (column1, column2)
VALUES (value3, value4);
```

**注意事項:**
- PostgreSQL/MySQL/Oracleは複数行を1つのINSERT文で処理可能
- SQL Serverは複数のINSERT文に分割（またはUNION ALLを使用）
- バッチサイズは実装時に調整可能

### 2.3 SELECT句からの挿入

#### YQL構文
```yaml
operation: insert
table: table_name
columns: [column1, column2, column3]
from_query:
  select:
    - col1: s.source_column1
    - col2: s.source_column2
    - col3: "expression"
  from: s: source_table
  where:
    - "condition"
```

#### 変換ルール

**全DB共通:**
```sql
INSERT INTO table_name (column1, column2, column3)
SELECT source_column1 AS col1, source_column2 AS col2, expression AS col3
FROM source_table
WHERE condition
```

**生成例:**
```sql
-- YQL:
-- operation: insert
-- table: customer_archive
-- columns: [customer_id, name, archived_at]
-- from_query:
--   select:
--     - customer_id: c.customer_id
--     - name: c.name
--     - archived_at: "CURRENT_TIMESTAMP"
--   from: c: customers
--   where:
--     - "c.status = 'inactive'"

-- PostgreSQL/MySQL/SQL Server/Oracle:
INSERT INTO customer_archive (customer_id, name, archived_at)
SELECT c.customer_id AS customer_id, c.name AS name, CURRENT_TIMESTAMP AS archived_at
FROM customers c
WHERE c.status = 'inactive'
```

**注意事項:**
- `from_query`内のSELECT文は、`specs/select.md`の仕様に従う
- カラムの順序は`columns`で指定した順序に従う
- SELECT句のエイリアスは、INSERT先のカラム名と対応

## 3. UPSERT機能について

INSERT文でのUPSERT機能（ON CONFLICT、ON DUPLICATE KEY、MERGE）については、`specs/upsert.md` を参照してください。

**対応するDB固有構文:**

| データベース | 構文 | 詳細 |
|-------------|------|------|
| PostgreSQL | `ON CONFLICT ... DO UPDATE/NOTHING` | [upsert.md 3章](upsert.md#3-postgresql-on-conflict) |
| MySQL | `ON DUPLICATE KEY UPDATE` | [upsert.md 4章](upsert.md#4-mysql-on-duplicate-key-update) |
| SQL Server | `MERGE` | [upsert.md 5章](upsert.md#5-sql-server-merge) |

**注意**: INSERT文として記述する場合でも、UPSERT機能を使用する場合は `specs/upsert.md` の仕様に従ってください。

## 4. RETURNING句の変換

### 4.1 PostgreSQL: RETURNING句

#### YQL構文
```yaml
operation: insert
table: table_name
values:
  name: "John Doe"
  email: "john@example.com"
returning: [id, name, created_at]
```

#### 変換ルール

**PostgreSQL:**
```sql
INSERT INTO table_name (name, email)
VALUES ('John Doe', 'john@example.com')
RETURNING id, name, created_at
```

**注意事項:**
- PostgreSQLのみサポート
- MySQL、SQL Server、Oracleでは使用不可（別途SELECT文が必要）
- Oracleでは`RETURNING INTO`を使用可能だが、ストアドプロシージャ内での使用が一般的なため、YQLではサポートしない

## 5. パラメータバインディング

### 5.1 パラメータ記法

#### YQL構文
```yaml
operation: insert
table: table_name
values:
  name: "#{customerName}"           # 単一値パラメータ
  email: "#{customerEmail}"
  status: "#{status:active}"         # デフォルト値付き
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

3. **`${paramArray}` - 配列パラメータ（バッチ挿入）**
   - 配列を複数行のINSERTに展開
   - 例: `values: "${customers}"` → 複数行のVALUES句に展開

**注意事項:**
- `#{paramName}`は必ずPreparedStatement形式でバインド
- `${paramArray}`は配列を展開して複数行のINSERTに変換
- SQLインジェクション対策のため、文字列連結は禁止

## 6. エラーハンドリング

### 6.1 変換エラー

以下の場合にエラーを発生:

1. **未定義テーブル/カラム**
   - スキーマ定義に存在しないテーブル/カラムを参照

2. **型不一致**
   - 値の型がカラムの型と一致しない

3. **制約違反**
   - NOT NULL制約、CHECK制約、UNIQUE制約の違反

4. **構文エラー**
   - YQL構文が不正

### 6.2 警告

以下の場合に警告を出力:

1. **大量データの挿入**
   - バッチサイズが大きすぎる場合

2. **パフォーマンスに影響する可能性のある操作**
   - インデックスが使用されない可能性のある条件

## 7. import機能の利用

INSERT文でもimport機能を利用できます。詳細は`specs/import.md`を参照してください。

### 7.1 スキーマ定義のimport

スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照できます。

#### YQL構文
```yaml
imports:
  - "schemas/ecommerce.yql"

operation: insert
table: customers  # importしたスキーマ定義からテーブルを参照
values:
  name: "#{customerName}"
  email: "#{customerEmail}"
  status: "#{status:active}"
```

**注意事項:**
- スキーマ定義をimportすることで、テーブル名、カラム名、型情報を参照可能
- 型チェックやバリデーションに使用
- SQL生成時には直接的な変換は不要（型チェックに使用）

### 7.2 マクロ（カラム定義）のimport

複雑な式をマクロとして定義し、VALUES句で使用できます。

#### 定義ファイル（`macros/current_timestamp.yql`）
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
  - "macros/current_timestamp.yql"

operation: insert
table: customers
values:
  name: "#{customerName}"
  email: "#{customerEmail}"
  created_at: "@current_timestamp"  # マクロを参照
```

**注意事項:**
- マクロは式として展開される
- VALUES句で式として使用可能
- パラメータ付きマクロも使用可能（詳細は`specs/import.md`を参照）

### 7.3 SELECT定義のimport

SELECT定義をimportして、`from_query`で使用できます。

#### 定義ファイル（`queries/inactive_customers.yql`）
```yaml
name: "inactive_customers"
description: "非アクティブな顧客を取得するSELECT定義"

select_definition:
  select:
    - customer_id: c.customer_id
    - name: c.name
    - archived_at: "CURRENT_TIMESTAMP"
  from: c: customers
  where:
    - "c.status = 'inactive'"
```

#### 使用ファイル
```yaml
imports:
  - "queries/inactive_customers.yql"

operation: insert
table: customer_archive
columns: [customer_id, name, archived_at]
from_query:
  using: "inactive_customers"  # importしたSELECT定義を参照
```

**変換結果:**
```sql
INSERT INTO customer_archive (customer_id, name, archived_at)
SELECT c.customer_id AS customer_id, c.name AS name, CURRENT_TIMESTAMP AS archived_at
FROM customers c
WHERE c.status = 'inactive'
```

**注意事項:**
- SELECT定義をimportすることで、複雑なクエリを再利用可能
- `from_query.using`でimportしたSELECT定義を参照
- SELECT定義は`specs/select.md`の仕様に従う

## 8. 実装時の注意事項

### 8.1 バッチサイズの制限

- 大量データの挿入時は、バッチサイズを制限
- デフォルトバッチサイズ: 1000行（実装時に調整可能）

### 8.2 トランザクション

- 複数行のINSERTは、1つのトランザクションで処理
- エラー時はロールバック

### 8.3 自動インクリメント

- 自動インクリメントカラムは、値を指定しない場合は省略可能
- 明示的にNULLを指定することも可能（DB依存）

### 8.4 import機能の詳細

import機能の詳細については、`specs/import.md`を参照してください。

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト

