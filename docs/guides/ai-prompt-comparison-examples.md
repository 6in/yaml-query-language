---
layout: default
title: Ai Prompt Comparison Examples
---

# AIプロンプトでの実際の違い：具体例

## 目的

スキーマ情報付与YQLとSQL+DDL分離型の、実際のAIプロンプトでの違いを具体例で示します。

---

## シナリオ: JOIN条件の妥当性検証

### タスク
「以下のクエリのJOIN条件が正しいか検証してください。外部キー関係、型の一致、インデックスの有無を確認してください。」

---

## アプローチA: スキーマ情報付与YQL

### プロンプト

```
以下のYQLファイルを解析して、JOIN条件の妥当性を検証してください。
外部キー関係、型の一致、インデックスの有無を確認してください。

```yaml
metadata:
  source_sql: "SELECT c.id, c.name, o.id as order_id, o.order_date, o.amount FROM customers c INNER JOIN orders o ON c.id = o.customer_id"
  converted_at: "2024-12-20T10:00:00Z"

schema:
  tables:
    customers:
      columns:
        id:
          type: integer
          constraints:
            not_null: true
            primary_key: true
        name:
          type: string
          constraints:
            not_null: true
      indexes:
        - name: "idx_customers_id"
          columns: ["id"]
          unique: true
    
    orders:
      columns:
        id:
          type: integer
          constraints:
            not_null: true
            primary_key: true
        customer_id:
          type: integer
          constraints:
            not_null: true
            foreign_key:
              table: "customers"
              column: "id"
        order_date:
          type: timestamp
        amount:
          type: decimal
          precision: 12
          scale: 2
      indexes:
        - name: "idx_orders_customer"
          columns: ["customer_id"]
      foreign_keys:
        - column: "customer_id"
          references:
            table: "customers"
            column: "id"

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
```

### AIの処理フロー（推測）

1. **ファイル読み込み**: YQLファイルを1回読み込む
2. **テーブル特定**: `query.from` と `query.joins` から `customers` と `orders` を特定
3. **スキーマ情報取得**: `schema.tables.customers` と `schema.tables.orders` を直接参照
4. **JOIN条件の検証**:
   - 条件: `c.id = o.customer_id`
   - `customers.id`: integer型、PRIMARY KEY
   - `orders.customer_id`: integer型、外部キー（customers.id参照）
   - 型一致: ✅
   - 外部キー関係: ✅
5. **インデックス確認**:
   - `idx_customers_id`: customers.idに存在
   - `idx_orders_customer`: orders.customer_idに存在
6. **結果**: JOIN条件は妥当

### 処理時間（推定）
- ファイル読み込み: 1回
- 関連付け処理: 不要（直接参照）
- 検証処理: 即座に実行可能
- **総処理時間: 短い**

### トークン使用量（推定）
- ファイル全体: 約500トークン
- 不要な情報: なし（使用テーブルのみ）
- **総トークン: 約500トークン**

---

## アプローチB: SQL + DDL分離型

### プロンプト

```
以下のSQLとDDLを解析して、JOIN条件の妥当性を検証してください。
外部キー関係、型の一致、インデックスの有無を確認してください。

**SQLファイル:**
```sql
SELECT c.id, c.name, o.id as order_id, o.order_date, o.amount 
FROM customers c 
INNER JOIN orders o ON c.id = o.customer_id;
```

**DDLファイル:**
```sql
-- customers テーブル定義
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customers_id (id),
    INDEX idx_customers_status (status)
);

-- orders テーブル定義
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    INDEX idx_orders_id (id),
    INDEX idx_orders_customer (customer_id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- products テーブル定義（使用されていない）
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- categories テーブル定義（使用されていない）
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);
```
```

### AIの処理フロー（推測）

1. **SQLファイル読み込み**: SQLファイルを読み込む
2. **SQL解析**: SQLを解析して使用テーブル（`customers`, `orders`）を特定
3. **DDLファイル読み込み**: DDLファイルを読み込む
4. **DDL解析**: DDLを解析して全テーブル定義を抽出
   - customers テーブル定義を抽出
   - orders テーブル定義を抽出
   - products テーブル定義を抽出（使用されていない）
   - categories テーブル定義を抽出（使用されていない）
5. **テーブルマッチング**: SQLで使用されているテーブルとDDL内のテーブルをマッチング
   - `customers` → DDL内のcustomersテーブル
   - `orders` → DDL内のordersテーブル
6. **カラム情報抽出**:
   - `customers.id`: INTEGER, PRIMARY KEY
   - `orders.customer_id`: INTEGER, FOREIGN KEY (customers.id参照)
7. **JOIN条件の検証**:
   - 条件: `c.id = o.customer_id`
   - `customers.id`: INTEGER型、PRIMARY KEY
   - `orders.customer_id`: INTEGER型、外部キー（customers.id参照）
   - 型一致: ✅
   - 外部キー関係: ✅
8. **インデックス確認**:
   - DDLからインデックス定義を抽出
   - `idx_customers_id`: customers.idに存在
   - `idx_orders_customer`: orders.customer_idに存在
9. **結果**: JOIN条件は妥当

### 処理時間（推定）
- SQLファイル読み込み: 1回
- DDLファイル読み込み: 1回
- SQL解析: テーブル特定
- DDL解析: 全テーブル定義抽出（使用されていないテーブルも含む）
- テーブルマッチング: 関連付け処理
- カラム情報抽出: 抽出処理
- 検証処理: 関連付け後に実行
- **総処理時間: 長い**

### トークン使用量（推定）
- SQLファイル: 約50トークン
- DDLファイル: 約800トークン（使用されていないテーブルも含む）
- 不要な情報: products, categoriesテーブル（約300トークン）
- **総トークン: 約850トークン**

---

## 比較結果

| 項目 | アプローチA（統合型） | アプローチB（分離型） | 差 |
|------|---------------------|---------------------|-----|
| **ファイル読み込み** | 1回 | 2回 | +100% |
| **処理ステップ** | 6ステップ | 9ステップ | +50% |
| **関連付け処理** | 不要 | 必要 | +100% |
| **不要な情報処理** | なし | あり（products, categories） | +∞ |
| **トークン使用量** | 約500トークン | 約850トークン | +70% |
| **処理時間（推定）** | 短い | 長い | +50-100% |
| **エラーの可能性** | 低い | 高い（関連付けミス） | - |

---

## 実際のAI応答の違い

### アプローチA（統合型）での応答例

```
JOIN条件の検証結果:

✅ **JOIN条件は妥当です**

**検証内容:**
1. **外部キー関係**: 
   - `orders.customer_id` は `customers.id` を参照する外部キーとして定義されています
   - JOIN条件 `c.id = o.customer_id` はこの外部キー関係と一致しています

2. **型の一致**:
   - `customers.id`: INTEGER型
   - `orders.customer_id`: INTEGER型
   - 型が一致しています

3. **インデックス**:
   - `customers.id`: `idx_customers_id` インデックスが存在
   - `orders.customer_id`: `idx_orders_customer` インデックスが存在
   - 両方のカラムにインデックスがあるため、JOINのパフォーマンスは良好です

**結論**: JOIN条件は正しく、パフォーマンスも最適化されています。
```

**応答の特徴**:
- 明確で簡潔
- 関連情報が直接参照されている
- 不要な情報がない

### アプローチB（分離型）での応答例

```
JOIN条件の検証結果:

✅ **JOIN条件は妥当です**

**検証内容:**
1. **使用テーブルの特定**:
   - SQLから `customers` と `orders` テーブルが使用されていることを確認

2. **DDLからの定義抽出**:
   - DDLから `customers` テーブル定義を抽出
   - DDLから `orders` テーブル定義を抽出

3. **外部キー関係**: 
   - DDLの `FOREIGN KEY (customer_id) REFERENCES customers(id)` から
   - `orders.customer_id` は `customers.id` を参照する外部キーであることを確認
   - JOIN条件 `c.id = o.customer_id` はこの外部キー関係と一致しています

4. **型の一致**:
   - DDLから `customers.id`: INTEGER型を確認
   - DDLから `orders.customer_id`: INTEGER型を確認
   - 型が一致しています

5. **インデックス**:
   - DDLから `idx_customers_id` インデックスが `customers.id` に存在することを確認
   - DDLから `idx_orders_customer` インデックスが `orders.customer_id` に存在することを確認
   - 両方のカラムにインデックスがあるため、JOINのパフォーマンスは良好です

**結論**: JOIN条件は正しく、パフォーマンスも最適化されています。

**注意**: DDLには `products` と `categories` テーブルの定義も含まれていましたが、このクエリでは使用されていないため、検証対象外としました。
```

**応答の特徴**:
- より詳細な説明（処理ステップが多いため）
- 関連付けの過程が明示されている
- 不要な情報への言及がある

---

## 結論

### AIの理解のしやすさ

**アプローチA（スキーマ情報付与YQL）が圧倒的に優れている**

主な理由：
1. **処理ステップが少ない**: 関連付け処理が不要
2. **不要な情報がない**: 使用されているテーブルのみスキーマ情報が含まれる
3. **直接参照が可能**: 構造化された情報から直接参照できる
4. **トークン使用量が少ない**: 不要な情報を含めないため
5. **エラーの可能性が低い**: 関連付けミスのリスクがない

### 実用的な観点

**アプローチAの利点**:
- **コスト削減**: トークン使用量が約40%削減（500 vs 850）
- **処理速度**: 処理ステップが約33%削減（6 vs 9）
- **精度向上**: 関連付けミスのリスクがない
- **明確性**: 不要な情報がないため、AIの応答がより明確

**アプローチBの利点**:
- 標準的な形式（SQL/DDL）
- スキーマ定義の再利用性

### 推奨

**AI解析の目的であれば、アプローチA（スキーマ情報付与YQL）を強く推奨**

特に以下の用途で効果的：
- クエリの解析・理解
- エラー検出
- 最適化提案
- 型チェック
- リレーションシップの検証

