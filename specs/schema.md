# YQL スキーマ定義 仕様書

## 1. 概要

このドキュメントは、YQLにおけるスキーマ定義（テーブル、ビュー、マテリアライズド・ビュー等）の仕様を定義します。スキーマ定義はYQLの基盤となる重要な定義であり、以下の用途で使用されます。

### 1.1 スキーマ定義の用途

1. **型チェック・バリデーション**: YQL→SQL変換時のテーブル/カラム存在確認、型チェック
2. **AI解析用スキーマ埋め込み**: YQLにスキーマ情報を埋め込んでAI解析精度を向上
3. **DDL生成**: CREATE TABLE/VIEW文の自動生成
4. **ドキュメント生成**: テーブル仕様書の自動生成
5. **マイグレーション支援**: スキーマ変更の影響分析
6. **セキュリティチェック**: 機密カラムの検出、アクセス制御

### 1.2 対応データベース

- PostgreSQL
- MySQL
- SQL Server (MSSQL)
- Oracle (将来対応)

### 1.3 対応オブジェクト

| オブジェクト | 説明 | 対応状況 |
|-------------|------|----------|
| テーブル | 基本的なデータ格納 | ✅ 対応 |
| ビュー | 仮想テーブル | ✅ 対応 |
| マテリアライズド・ビュー | 実体化されたビュー | ✅ 対応 |
| インデックス | 検索最適化 | ✅ 対応 |
| 制約 | データ整合性 | ✅ 対応 |
| シーケンス | 連番生成 | ✅ 対応 |
| トリガー | 自動処理 | 🔜 将来対応 |

## 2. スキーマファイルの基本構造

### 2.1 ファイル構造

```yaml
# スキーマ定義ファイル
schema_version: "1.0.0"
namespace: "namespace_name"
description: "スキーマの説明"
created_at: "2024-12-20"
author: "author_name"

# 共通型定義（オプション）
common_types:
  # ...

# テーブル定義
tables:
  # ...

# ビュー定義（オプション）
views:
  # ...

# マテリアライズド・ビュー定義（オプション）
materialized_views:
  # ...

# シーケンス定義（オプション）
sequences:
  # ...

# データベース設定（オプション）
database_settings:
  # ...
```

### 2.2 メタデータ

```yaml
schema_version: "1.0.0"          # スキーマ定義のバージョン
namespace: "ecommerce"           # 名前空間（スキーマ名）
description: "Eコマースシステムのデータベーススキーマ"
created_at: "2024-12-20"
updated_at: "2024-12-20"
author: "database-team"
```

**注意事項:**
- `schema_version`はセマンティックバージョニングを使用
- `namespace`はスキーマ名として使用（PostgreSQLのスキーマ、MySQLのデータベース名など）

## 3. データ型

### 3.1 基本データ型

| YQL型 | PostgreSQL | MySQL | SQL Server | 説明 |
|-------|------------|-------|------------|------|
| `integer` | INTEGER | INT | INT | 整数 |
| `bigint` | BIGINT | BIGINT | BIGINT | 大きな整数 |
| `smallint` | SMALLINT | SMALLINT | SMALLINT | 小さな整数 |
| `decimal` | DECIMAL(p,s) | DECIMAL(p,s) | DECIMAL(p,s) | 固定小数点 |
| `float` | REAL | FLOAT | REAL | 単精度浮動小数点 |
| `double` | DOUBLE PRECISION | DOUBLE | FLOAT | 倍精度浮動小数点 |
| `string` | VARCHAR(n) | VARCHAR(n) | NVARCHAR(n) | 可変長文字列 |
| `char` | CHAR(n) | CHAR(n) | NCHAR(n) | 固定長文字列 |
| `text` | TEXT | TEXT | NVARCHAR(MAX) | 長いテキスト |
| `boolean` | BOOLEAN | TINYINT(1) | BIT | 真偽値 |
| `date` | DATE | DATE | DATE | 日付 |
| `time` | TIME | TIME | TIME | 時刻 |
| `timestamp` | TIMESTAMP | DATETIME | DATETIME2 | 日時 |
| `timestamptz` | TIMESTAMPTZ | DATETIME | DATETIMEOFFSET | タイムゾーン付き日時 |
| `json` | JSONB | JSON | NVARCHAR(MAX) | JSON |
| `uuid` | UUID | CHAR(36) | UNIQUEIDENTIFIER | UUID |
| `binary` | BYTEA | BLOB | VARBINARY(MAX) | バイナリ |
| `enum` | ENUM型 | ENUM | CHECK制約 | 列挙型 |
| `array` | ARRAY | JSON | JSON | 配列（PostgreSQLのみネイティブ） |

### 3.2 データ型の定義例

```yaml
columns:
  # 整数型
  id:
    type: integer
    
  # 大きな整数型
  big_number:
    type: bigint
    
  # 固定小数点型（精度と小数点以下桁数を指定）
  price:
    type: decimal
    precision: 10
    scale: 2
    
  # 可変長文字列型（最大長を指定）
  name:
    type: string
    max_length: 100
    
  # 列挙型（値のリストを指定）
  status:
    type: enum
    values: ["active", "inactive", "suspended"]
    
  # JSON型
  metadata:
    type: json
    
  # 配列型（PostgreSQLのみネイティブ、他はJSONで代用）
  tags:
    type: array
    element_type: string
```

## 4. テーブル定義

### 4.1 基本構文

```yaml
tables:
  table_name:
    label: "テーブルの論理名"       # 論理名（必須）
    description: "テーブルの説明"   # 説明（オプション）
    columns:
      column_name:
        type: data_type
        label: "カラムの論理名"     # 論理名（必須）
        description: "カラムの説明" # 説明（オプション）
        constraints:
          # 制約
        default: default_value
        # その他のオプション
    indexes:
      # インデックス定義
    constraints:
      # テーブルレベルの制約
```

**テーブル属性:**

| 属性 | 必須 | 説明 |
|------|------|------|
| `label` | ✅ | 論理名（日本語名など） |
| `description` | - | テーブルの詳細説明（オプション） |
| `columns` | ✅ | カラム定義 |
| `indexes` | - | インデックス定義 |
| `constraints` | - | テーブルレベルの制約 |

### 4.2 カラム定義

#### 4.2.1 基本的なカラム定義

```yaml
columns:
  # 主キー（自動増分）
  id:
    type: integer
    label: "ID"                        # 論理名（必須）
    constraints:
      primary_key: true
      auto_increment: true
      
  # NOT NULL制約付き文字列
  name:
    type: string
    label: "名前"                       # 論理名（必須）
    description: "顧客の氏名"            # 説明（オプション）
    max_length: 100
    constraints:
      not_null: true
      
  # UNIQUE制約付き文字列
  email:
    type: string
    label: "メールアドレス"              # 論理名（必須）
    description: "連絡用メールアドレス"   # 説明（オプション）
    max_length: 255
    constraints:
      not_null: true
      unique: true
      
  # デフォルト値付き
  status:
    type: enum
    label: "ステータス"                  # 論理名（必須）
    values: ["active", "inactive"]
    default: "active"
    constraints:
      not_null: true
      
  # NULL許容
  remarks:
    type: text
    label: "備考"                       # 論理名（必須）
    description: "自由記述欄"            # 説明（オプション）
    nullable: true
```

**カラム属性:**

| 属性 | 必須 | 説明 |
|------|------|------|
| `type` | ✅ | データ型 |
| `label` | ✅ | 論理名（日本語名など） |
| `description` | - | カラムの詳細説明（オプション） |
| `constraints` | - | 制約定義 |
| `default` | - | デフォルト値 |
| `nullable` | - | NULL許容（デフォルト: false） |

#### 4.2.2 制約の種類

```yaml
constraints:
  # 主キー制約
  primary_key: true
  
  # 自動増分
  auto_increment: true
  
  # NOT NULL制約
  not_null: true
  
  # UNIQUE制約
  unique: true
  
  # 外部キー制約
  foreign_key:
    table: "referenced_table"
    column: "referenced_column"
    on_delete: "CASCADE"    # CASCADE | SET NULL | SET DEFAULT | RESTRICT | NO ACTION
    on_update: "CASCADE"    # CASCADE | SET NULL | SET DEFAULT | RESTRICT | NO ACTION
    
  # CHECK制約
  check: "column_name >= 0"
  
  # 文字列長制約
  max_length: 100
  min_length: 1
  
  # パターン制約（正規表現）
  pattern: "^[A-Z]{2}[0-9]{6}$"
```

#### 4.2.3 セキュリティ属性

```yaml
columns:
  password_hash:
    type: string
    max_length: 255
    constraints:
      not_null: true
    security:
      sensitive: true           # 機密情報フラグ
      access_level: "admin_only"  # アクセスレベル
      pii: false                # 個人情報フラグ
      
  email:
    type: string
    max_length: 255
    security:
      pii: true                 # 個人情報
      retention_period: 365     # 保持期間（日）
```

### 4.3 インデックス定義

```yaml
indexes:
  # 単一カラムインデックス
  - name: "idx_table_column"
    columns: ["column_name"]
    
  # 複合インデックス
  - name: "idx_table_col1_col2"
    columns: ["column1", "column2"]
    
  # ユニークインデックス
  - name: "idx_table_unique"
    columns: ["column_name"]
    unique: true
    
  # 部分インデックス（PostgreSQLのみ）
  - name: "idx_table_partial"
    columns: ["column_name"]
    where: "status = 'active'"
    
  # 関数インデックス
  - name: "idx_table_lower"
    columns: ["LOWER(column_name)"]
    
  # インデックスタイプの指定
  - name: "idx_table_btree"
    columns: ["column_name"]
    type: "btree"  # btree | hash | gin | gist (PostgreSQL)
```

### 4.4 テーブルレベルの制約

```yaml
constraints:
  # 複合主キー
  - name: "pk_table"
    type: primary_key
    columns: ["column1", "column2"]
    
  # 複合ユニーク制約
  - name: "uq_table_unique"
    type: unique
    columns: ["column1", "column2"]
    
  # CHECK制約
  - name: "chk_table_check"
    type: check
    check: "end_date >= start_date"
    
  # 外部キー制約（複合）
  - name: "fk_table_ref"
    type: foreign_key
    columns: ["column1", "column2"]
    references:
      table: "referenced_table"
      columns: ["ref_column1", "ref_column2"]
    on_delete: "CASCADE"
```

### 4.5 完全なテーブル定義例

```yaml
tables:
  customers:
    label: "顧客マスタ"                   # テーブルの論理名（必須）
    description: "顧客情報を管理するマスタテーブル"  # テーブルの説明（オプション）
    columns:
      customer_id:
        type: integer
        label: "顧客ID"
        constraints:
          primary_key: true
          auto_increment: true
          
      customer_code:
        type: string
        label: "顧客コード"
        description: "C + 8桁の数字で構成される一意のコード"
        max_length: 20
        constraints:
          not_null: true
          unique: true
          pattern: "^C[0-9]{8}$"
          
      name:
        type: string
        label: "顧客名"
        max_length: 100
        constraints:
          not_null: true
          
      email:
        type: string
        label: "メールアドレス"
        description: "連絡用メールアドレス"
        max_length: 255
        constraints:
          not_null: true
          unique: true
          pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
        security:
          pii: true
          
      status:
        type: enum
        label: "ステータス"
        description: "顧客の状態（active: 有効, inactive: 無効, suspended: 停止）"
        values: ["active", "inactive", "suspended"]
        default: "active"
        constraints:
          not_null: true
          
      credit_limit:
        type: decimal
        label: "与信限度額"
        description: "この顧客に対する与信の上限金額"
        precision: 12
        scale: 2
        default: 0
        constraints:
          check: "credit_limit >= 0"
          
      created_at:
        type: timestamp
        label: "作成日時"
        default: "CURRENT_TIMESTAMP"
        constraints:
          not_null: true
          
      updated_at:
        type: timestamp
        label: "更新日時"
        on_update: "CURRENT_TIMESTAMP"
        
      deleted_at:
        type: timestamp
        label: "削除日時"
        description: "論理削除された日時（NULLの場合は未削除）"
        nullable: true
        
    indexes:
      - name: "idx_customers_code"
        columns: ["customer_code"]
        unique: true
      - name: "idx_customers_email"
        columns: ["email"]
        unique: true
      - name: "idx_customers_status"
        columns: ["status"]
      - name: "idx_customers_name"
        columns: ["name"]
        
    constraints:
      - name: "chk_customers_email_format"
        type: check
        check: "email LIKE '%@%'"
```

## 5. 共通型定義（再利用可能なカラム定義）

### 5.1 基本構文

```yaml
common_types:
  # YAMLアンカーを使用した再利用可能な定義
  type_name: &type_name
    type: data_type
    constraints:
      # 制約
```

### 5.2 使用例

```yaml
common_types:
  # 主キー定義
  id_field: &id_field
    type: integer
    constraints:
      primary_key: true
      auto_increment: true
      
  # 監査フィールド
  audit_fields: &audit_fields
    created_at:
      type: timestamp
      default: "CURRENT_TIMESTAMP"
      constraints:
        not_null: true
    updated_at:
      type: timestamp
      on_update: "CURRENT_TIMESTAMP"
    created_by:
      type: integer
      constraints:
        foreign_key:
          table: "users"
          column: "user_id"
    updated_by:
      type: integer
      constraints:
        foreign_key:
          table: "users"
          column: "user_id"
          
  # 論理削除フィールド
  soft_delete: &soft_delete
    deleted_at:
      type: timestamp
      nullable: true
    deleted_by:
      type: integer
      nullable: true
      constraints:
        foreign_key:
          table: "users"
          column: "user_id"

tables:
  customers:
    columns:
      customer_id: *id_field           # 主キー定義を参照
      name:
        type: string
        max_length: 100
      <<: *audit_fields                # 監査フィールドを展開
      <<: *soft_delete                 # 論理削除フィールドを展開
```

## 6. ビュー定義

### 6.1 基本構文

```yaml
views:
  view_name:
    description: "ビューの説明"
    query:
      select:
        - column_alias: expression
      from: alias: table_name
      joins:
        # JOIN定義
      where:
        # WHERE条件
      group_by:
        # GROUP BY
```

### 6.2 ビュー定義例

```yaml
views:
  customer_summary:
    description: "顧客サマリービュー"
    query:
      select:
        - customer_id: c.customer_id
        - customer_code: c.customer_code
        - customer_name: c.name
        - order_count: "COUNT(o.order_id)"
        - total_spent: "SUM(o.total_amount)"
        - last_order_date: "MAX(o.order_date)"
        - avg_order_value: "AVG(o.total_amount)"
      from: c: customers
      joins:
        - type: LEFT
          alias: o
          table: orders
          on: "c.customer_id = o.customer_id"
          additional_conditions:
            - "o.status IN ('confirmed', 'shipped', 'delivered')"
      where:
        - "c.deleted_at IS NULL"
      group_by:
        - c.customer_id
        - c.customer_code
        - c.name
```

### 6.3 DDL生成例

**PostgreSQL/MySQL/SQL Server:**
```sql
CREATE VIEW customer_summary AS
SELECT
  c.customer_id AS customer_id,
  c.customer_code AS customer_code,
  c.name AS customer_name,
  COUNT(o.order_id) AS order_count,
  SUM(o.total_amount) AS total_spent,
  MAX(o.order_date) AS last_order_date,
  AVG(o.total_amount) AS avg_order_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
  AND o.status IN ('confirmed', 'shipped', 'delivered')
WHERE c.deleted_at IS NULL
GROUP BY c.customer_id, c.customer_code, c.name
```

## 7. マテリアライズド・ビュー定義

### 7.1 基本構文

```yaml
materialized_views:
  mv_name:
    description: "マテリアライズド・ビューの説明"
    query:
      # ビューと同じクエリ定義
    refresh:
      type: "manual"           # manual | on_commit | scheduled
      schedule: "0 0 * * *"    # cron形式（scheduledの場合）
    indexes:
      # インデックス定義
```

### 7.2 マテリアライズド・ビュー定義例

```yaml
materialized_views:
  mv_product_sales_daily:
    description: "商品別日次売上サマリー"
    query:
      select:
        - product_id: p.product_id
        - product_name: p.product_name
        - sale_date: "DATE(o.order_date)"
        - quantity_sold: "SUM(oi.quantity)"
        - revenue: "SUM(oi.line_total)"
      from: p: products
      joins:
        - type: INNER
          alias: oi
          table: order_items
          on: "p.product_id = oi.product_id"
        - type: INNER
          alias: o
          table: orders
          on: "oi.order_id = o.order_id"
      where:
        - "o.status IN ('confirmed', 'shipped', 'delivered')"
      group_by:
        - p.product_id
        - p.product_name
        - "DATE(o.order_date)"
    refresh:
      type: "scheduled"
      schedule: "0 1 * * *"    # 毎日1時に更新
    indexes:
      - name: "idx_mv_product_sales_date"
        columns: ["sale_date"]
      - name: "idx_mv_product_sales_product"
        columns: ["product_id"]
```

### 7.3 DDL生成例

**PostgreSQL:**
```sql
CREATE MATERIALIZED VIEW mv_product_sales_daily AS
SELECT
  p.product_id AS product_id,
  p.product_name AS product_name,
  DATE(o.order_date) AS sale_date,
  SUM(oi.quantity) AS quantity_sold,
  SUM(oi.line_total) AS revenue
FROM products p
INNER JOIN order_items oi ON p.product_id = oi.product_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.status IN ('confirmed', 'shipped', 'delivered')
GROUP BY p.product_id, p.product_name, DATE(o.order_date);

CREATE INDEX idx_mv_product_sales_date ON mv_product_sales_daily (sale_date);
CREATE INDEX idx_mv_product_sales_product ON mv_product_sales_daily (product_id);
```

**SQL Server (Indexed View):**
```sql
CREATE VIEW mv_product_sales_daily
WITH SCHEMABINDING AS
SELECT
  p.product_id AS product_id,
  p.product_name AS product_name,
  CAST(o.order_date AS DATE) AS sale_date,
  SUM(oi.quantity) AS quantity_sold,
  SUM(oi.line_total) AS revenue,
  COUNT_BIG(*) AS row_count
FROM dbo.products p
INNER JOIN dbo.order_items oi ON p.product_id = oi.product_id
INNER JOIN dbo.orders o ON oi.order_id = o.order_id
WHERE o.status IN ('confirmed', 'shipped', 'delivered')
GROUP BY p.product_id, p.product_name, CAST(o.order_date AS DATE);

CREATE UNIQUE CLUSTERED INDEX idx_mv_product_sales_pk
ON mv_product_sales_daily (product_id, sale_date);
```

**注意事項:**
- MySQLはマテリアライズド・ビューをネイティブサポートしていないため、テーブル＋トリガーまたはイベントスケジューラで代用
- SQL Serverでは「Indexed View」として実装（WITH SCHEMABINDINGが必要）

## 8. シーケンス定義

### 8.1 基本構文

```yaml
sequences:
  sequence_name:
    description: "シーケンスの説明"
    start: 1
    increment: 1
    min_value: 1
    max_value: 9223372036854775807
    cycle: false
    cache: 1
```

### 8.2 シーケンス定義例

```yaml
sequences:
  order_number_seq:
    description: "注文番号用シーケンス"
    start: 1000000001
    increment: 1
    min_value: 1000000001
    max_value: 9999999999
    cycle: false
    cache: 100
    
  customer_code_seq:
    description: "顧客コード用シーケンス"
    start: 1
    increment: 1
    cache: 50
```

### 8.3 DDL生成例

**PostgreSQL:**
```sql
CREATE SEQUENCE order_number_seq
  START WITH 1000000001
  INCREMENT BY 1
  MINVALUE 1000000001
  MAXVALUE 9999999999
  NO CYCLE
  CACHE 100;
```

**SQL Server:**
```sql
CREATE SEQUENCE order_number_seq
  START WITH 1000000001
  INCREMENT BY 1
  MINVALUE 1000000001
  MAXVALUE 9999999999
  NO CYCLE
  CACHE 100;
```

**MySQL:**
MySQLはシーケンスをネイティブサポートしていないため、AUTO_INCREMENTまたはテーブルで代用。

## 9. データベース設定

### 9.1 基本構文

```yaml
database_settings:
  charset: "utf8mb4"
  collation: "utf8mb4_unicode_ci"
  engine: "InnoDB"              # MySQL固有
  
  performance:
    # パフォーマンス設定
    
  security:
    # セキュリティ設定
    
  backup:
    # バックアップ設定
```

### 9.2 設定例

```yaml
database_settings:
  charset: "utf8mb4"
  collation: "utf8mb4_unicode_ci"
  engine: "InnoDB"
  
  performance:
    enable_query_cache: true
    slow_query_log: true
    slow_query_threshold: 2       # 2秒以上のクエリをログ
    
  security:
    ssl_required: true
    password_validation: true
    audit_log: true
    
  backup:
    daily_backup: true
    retention_days: 30
    compression: true
```

## 10. 権限設定

### 10.1 基本構文

```yaml
permissions:
  roles:
    role_name:
      tables: ["table1", "table2"]   # または ["*"] で全テーブル
      operations: ["SELECT", "INSERT", "UPDATE", "DELETE"]
      restrictions:
        - "restriction_definition"
```

### 10.2 権限設定例

```yaml
permissions:
  roles:
    admin:
      tables: ["*"]
      operations: ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
      
    manager:
      tables: ["customers", "orders", "order_items", "products"]
      operations: ["SELECT", "INSERT", "UPDATE"]
      restrictions:
        - "cannot_access_columns: ['password_hash', 'cost_price']"
        
    staff:
      tables: ["customers", "orders", "order_items", "products"]
      operations: ["SELECT", "INSERT"]
      restrictions:
        - "cannot_access_columns: ['password_hash', 'cost_price', 'credit_limit']"
        
    readonly:
      tables: ["customers", "orders", "products"]
      operations: ["SELECT"]
      restrictions:
        - "cannot_access_columns: ['password_hash', 'cost_price']"
        - "row_level_security: 'can_only_see_own_data'"
```

## 11. データマスキング設定

### 11.1 基本構文

```yaml
data_masking:
  environment_name:
    table.column: "masking_expression"
```

### 11.2 データマスキング例

```yaml
data_masking:
  development:
    customers.name: "CONCAT('テスト', LPAD(customer_id, 3, '0'))"
    customers.email: "CONCAT('test', customer_id, '@example.com')"
    customers.phone: "'000-0000-0000'"
    
  staging:
    customers.phone: "CONCAT(SUBSTRING(phone, 1, 3), '-xxxx-xxxx')"
    customers.email: "CONCAT(SUBSTRING(email, 1, 3), '***@', SUBSTRING_INDEX(email, '@', -1))"
```

## 12. import機能との連携

### 12.1 スキーマ定義のimport

```yaml
# queries/customer_orders.yql
imports:
  - "schemas/ecommerce.yql"

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - order_count: "COUNT(o.order_id)"
  from: c: customers    # importしたスキーマからテーブルを参照
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  group_by: [c.customer_id, c.name]
```

### 12.2 スキーマ埋め込み（AI解析用）

```yaml
# スキーマ情報を埋め込んだYQL（.enriched形式）
metadata:
  source_sql: "SELECT c.customer_id, c.name FROM customers c"
  converted_at: "2024-12-20T10:00:00Z"

schema:
  tables:
    customers:
      columns:
        customer_id:
          type: integer
          constraints:
            primary_key: true
        name:
          type: string
          max_length: 100
          constraints:
            not_null: true
        # ...

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
  from: c: customers
```

## 13. DDL生成

### 13.1 生成可能なDDL

| DDL | PostgreSQL | MySQL | SQL Server |
|-----|------------|-------|------------|
| CREATE TABLE | ✅ | ✅ | ✅ |
| CREATE VIEW | ✅ | ✅ | ✅ |
| CREATE MATERIALIZED VIEW | ✅ | ❌ (代替) | ✅ (Indexed View) |
| CREATE INDEX | ✅ | ✅ | ✅ |
| CREATE SEQUENCE | ✅ | ❌ (代替) | ✅ |
| ALTER TABLE | ✅ | ✅ | ✅ |
| DROP TABLE/VIEW | ✅ | ✅ | ✅ |

### 13.2 DDL生成例

**YQL定義:**
```yaml
tables:
  customers:
    columns:
      customer_id:
        type: integer
        constraints:
          primary_key: true
          auto_increment: true
      name:
        type: string
        max_length: 100
        constraints:
          not_null: true
      email:
        type: string
        max_length: 255
        constraints:
          not_null: true
          unique: true
      status:
        type: enum
        values: ["active", "inactive"]
        default: "active"
    indexes:
      - name: "idx_customers_email"
        columns: ["email"]
        unique: true
```

**PostgreSQL:**
```sql
CREATE TYPE customer_status AS ENUM ('active', 'inactive');

CREATE TABLE customers (
  customer_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  status customer_status DEFAULT 'active'
);

CREATE UNIQUE INDEX idx_customers_email ON customers (email);
```

**MySQL:**
```sql
CREATE TABLE customers (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  status ENUM('active', 'inactive') DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE UNIQUE INDEX idx_customers_email ON customers (email);
```

**SQL Server:**
```sql
CREATE TABLE customers (
  customer_id INT IDENTITY(1,1) PRIMARY KEY,
  name NVARCHAR(100) NOT NULL,
  email NVARCHAR(255) NOT NULL UNIQUE,
  status NVARCHAR(20) DEFAULT 'active',
  CONSTRAINT chk_customers_status CHECK (status IN ('active', 'inactive'))
);

CREATE UNIQUE INDEX idx_customers_email ON customers (email);
```

## 14. エラーハンドリング

### 14.1 バリデーションエラー

以下の場合にエラーを発生:

1. **未定義の型**: サポートされていないデータ型
2. **制約違反**: 無効な制約定義
3. **循環参照**: 外部キーの循環参照
4. **重複定義**: 同名のテーブル/カラム/インデックス
5. **構文エラー**: YQL構文が不正

### 14.2 警告

以下の場合に警告を出力:

1. **インデックス未設定**: 外部キーにインデックスがない
2. **大きなカラム**: VARCHAR(MAX)などの使用
3. **非推奨機能**: 非推奨の型や制約

## 15. 実装時の注意事項

### 15.1 DB方言の違い

- **ENUM型**: PostgreSQLはCREATE TYPE、MySQLはカラム定義内、SQL ServerはCHECK制約
- **自動増分**: PostgreSQLはSERIAL、MySQLはAUTO_INCREMENT、SQL ServerはIDENTITY
- **文字列型**: SQL ServerはNVARCHAR（Unicode対応）を使用

### 15.2 マイグレーション

- スキーマ変更時は、ALTER TABLE文を生成
- 破壊的変更（カラム削除等）は警告を出力
- バックアップの推奨

### 15.3 パフォーマンス

- 大量のインデックスは更新性能に影響
- マテリアライズド・ビューの更新タイミングを考慮

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト

