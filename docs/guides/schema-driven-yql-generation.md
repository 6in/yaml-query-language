---
layout: default
title: Schema Driven Yql Generation
---

# スキーマ定義駆動のYQL生成アプローチ

## 概要

スキーマ定義（`schemas/*.yql`）を先にAIに渡して、そこからYQLを組み立てるアプローチです。これにより、**スキーマ情報を理解した上で正確なYQLを生成**できます。

## アプローチの流れ

```
スキーマ定義 + 自然言語要件 + specs/select.md → [AI] → YQL
```

### 1. スキーマ定義をAIに渡す
- `schemas/*.yql`ファイルを読み込む
- テーブル定義、カラム定義、型情報、制約、リレーションシップを理解

### 2. 自然言語で要件を伝える
- 「アクティブな顧客の注文一覧を取得したい」
- 「過去30日以内に注文した顧客の売上合計を集計したい」

### 3. AIがYQLを生成
- スキーマ定義を参照して、存在するテーブル・カラムを正確に把握
- 型情報、制約、リレーションシップを理解した上でYQLを生成
- `specs/select.md`の仕様に従ってYQLを組み立て

## アプローチの利点

### 1. **正確性の向上**
- スキーマ定義を参照することで、存在するテーブル・カラムを正確に把握
- 存在しないテーブル・カラムを参照するエラーを防止

### 2. **型情報の理解**
- カラムの型情報を理解した上でYQLを生成
- 型不一致のエラーを防止（例: 文字列と数値の比較）

### 3. **リレーションシップの把握**
- 外部キー関係を理解した上でJOIN条件を生成
- 適切なJOINタイプ（INNER/LEFT/RIGHT）を選択

### 4. **制約の考慮**
- CHECK制約、ENUM値、NOT NULL制約を理解
- ビジネスルールに基づいた適切な条件を生成

### 5. **エラーの早期検出**
- スキーマ定義とYQLの整合性を事前にチェック
- 実行時エラーを防止

## 具体例

### 例1: 基本的なクエリ生成

**スキーマ定義（`schemas/ecommerce.yql`）:**
```yaml
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
        default: "active"
  
  orders:
    columns:
      order_id:
        type: integer
        constraints:
          primary_key: true
      customer_id:
        type: integer
        constraints:
          not_null: true
          foreign_key:
            table: "customers"
            column: "customer_id"
      order_date:
        type: timestamp
        constraints:
          not_null: true
      amount:
        type: decimal
        precision: 12
        scale: 2
        constraints:
          not_null: true
          check: "amount >= 0"
```

**自然言語要件:**
```
アクティブな顧客の注文一覧を取得したい。
顧客ID、顧客名、注文ID、注文日、注文金額を表示したい。
```

**AIが生成するYQL:**
```yaml
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
  - "c.status = 'active'"
```

**AIの処理フロー:**
1. スキーマ定義から`customers`と`orders`テーブルを特定
2. `customers.status`がENUM型で`"active"`が有効な値であることを確認
3. `orders.customer_id`が`customers.customer_id`を参照する外部キーであることを確認
4. JOIN条件`c.customer_id = o.customer_id`を生成
5. `specs/select.md`の仕様に従ってYQLを組み立て

### 例2: 集計クエリの生成

**自然言語要件:**
```
過去30日以内に注文した顧客の売上合計を集計したい。
顧客ID、顧客名、注文数、売上合計を表示したい。
売上合計の多い順に並べて、上位10件を取得したい。
```

**AIが生成するYQL:**
```yaml
select:
  - customer_id: c.customer_id
  - customer_name: c.name
  - order_count: "COUNT(o.order_id)"
  - total_amount: "SUM(o.amount)"
from: c: customers
joins:
  - type: LEFT
    alias: o
    table: orders
    on: "c.customer_id = o.customer_id"
where:
  - "o.order_date >= DATE('now', '-30 days')"
group_by: [c.customer_id, c.name]
having:
  - "COUNT(o.order_id) > 0"
order_by:
  - field: total_amount
    direction: DESC
limit: 10
```

**AIの処理フロー:**
1. スキーマ定義から`customers`と`orders`テーブルを特定
2. `orders.order_date`が`timestamp`型であることを確認
3. `orders.amount`が`decimal(12,2)`型で集計可能であることを確認
4. `orders.customer_id`が`customers.customer_id`を参照する外部キーであることを確認
5. LEFT JOINを使用（注文がない顧客も含める可能性を考慮）
6. 集計関数（COUNT、SUM）を使用
7. GROUP BY、HAVING、ORDER BY、LIMITを適切に配置
8. `specs/select.md`の仕様に従ってYQLを組み立て

### 例3: 複雑な条件の生成

**自然言語要件:**
```
高額注文（10万円以上）をしたアクティブな顧客の一覧を取得したい。
顧客ID、顧客名、注文数、最大注文金額を表示したい。
```

**AIが生成するYQL:**
```yaml
select:
  - customer_id: c.customer_id
  - customer_name: c.name
  - order_count: "COUNT(o.order_id)"
  - max_amount: "MAX(o.amount)"
from: c: customers
joins:
  - type: INNER
    alias: o
    table: orders
    on: "c.customer_id = o.customer_id"
where:
  - "c.status = 'active'"
  - "o.amount >= 100000"
group_by: [c.customer_id, c.name]
having:
  - "COUNT(o.order_id) > 0"
```

**AIの処理フロー:**
1. スキーマ定義から`customers.status`がENUM型で`"active"`が有効な値であることを確認
2. `orders.amount`が`decimal(12,2)`型で数値比較可能であることを確認
3. `orders.amount`のCHECK制約（`amount >= 0`）を確認
4. 10万円 = 100000（decimal型として扱う）
5. WHERE句で`c.status = 'active'`と`o.amount >= 100000`をAND結合
6. 集計関数（COUNT、MAX）を使用
7. GROUP BY、HAVINGを適切に配置
8. `specs/select.md`の仕様に従ってYQLを組み立て

## 実装方法

### 1. スキーマ定義の読み込み

```python
# スキーマ定義を読み込む
schema_files = [
    "schemas/ecommerce.yql",
    "schemas/users.yql",
    # ...
]

schemas = {}
for schema_file in schema_files:
    with open(schema_file, 'r') as f:
        schema = yaml.safe_load(f)
        schemas.update(schema.get('tables', {}))
```

### 2. AIプロンプトの構築

```python
prompt = f"""
以下のスキーマ定義と要件に基づいて、YQLを生成してください。

**スキーマ定義:**
{yaml.dump(schemas)}

**仕様書:**
{read_file('specs/select.md')}

**要件:**
{user_requirement}

**注意事項:**
- スキーマ定義に存在するテーブル・カラムのみを使用してください
- 型情報、制約、リレーションシップを考慮してください
- `specs/select.md`の仕様に従ってYQLを組み立ててください
"""
```

### 3. AI知識ベースへの格納

**GeminiのGem:**
- `schemas/*.yql`ファイルをアップロード
- `specs/select.md`もアップロード
- プロンプトで「スキーマ定義を参照してYQLを生成してください」と指示

**NotebookLM:**
- `schemas/*.yql`をソースとして追加
- `specs/select.md`もソースとして追加
- 自然言語で要件を伝えてYQLを生成

**独自実装:**
- ベクトルDBに`schemas/*.yql`と`specs/select.md`を格納
- セマンティック検索で関連箇所を取得
- プロンプトに含めてYQLを生成

## アプローチの比較

### 従来のアプローチ（SQLから変換）
```
SQL → [AI] → YQL
```
- 既存のSQLを変換する場合に有効
- スキーマ情報がないため、存在チェックができない

### スキーマ定義駆動アプローチ（新規生成）
```
スキーマ定義 + 要件 → [AI] → YQL
```
- 新規にYQLを生成する場合に有効
- スキーマ情報を参照できるため、正確性が高い

### ハイブリッドアプローチ
```
既存SQL → [AI] → YQL（変換）
スキーマ定義 + 要件 → [AI] → YQL（新規生成）
```
- 用途に応じて使い分け
- 既存SQLの変換と新規生成の両方をサポート

## まとめ

### スキーマ定義駆動アプローチの利点
1. **正確性の向上**: 存在するテーブル・カラムを正確に把握
2. **型情報の理解**: 型不一致のエラーを防止
3. **リレーションシップの把握**: 適切なJOIN条件を生成
4. **制約の考慮**: ビジネスルールに基づいた適切な条件を生成
5. **エラーの早期検出**: スキーマ定義とYQLの整合性を事前にチェック

### 実装方法
- **スキーマ定義の読み込み**: `schemas/*.yql`を読み込む
- **AIプロンプトの構築**: スキーマ定義 + 要件 + `specs/select.md`を含める
- **AI知識ベースへの格納**: GeminiのGem、NotebookLM、または独自実装

### 用途
- **新規YQL生成**: スキーマ定義駆動アプローチ
- **既存SQL変換**: SQL→YQL変換アプローチ
- **両方のサポート**: ハイブリッドアプローチ

このアプローチにより、**スキーマ情報を理解した上で正確なYQLを生成**できます。

