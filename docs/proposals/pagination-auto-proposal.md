---
layout: default
title: Pagination Auto Proposal
---

# SELECT結果タイプ自動化機能 提案書

## 1. 問題提起

現在のYQLでは、SELECT文の結果タイプ（ページング、単一レコード取得、上限付き取得など）を実現する際に、毎回`limit`と`offset`を明示的に記述する必要があります：

```yaml
query:
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  limit: "${per_page:20}"
  offset: "$((${page:1} - 1) * ${per_page:20})"
```

この記述が毎回必要で、面倒に感じる場合があります。また、**「このSELECT文がどんな結果を返すのか？」**という意図が明確でない場合があります。

## 1.1 新しい観点: 結果タイプの明示化

SELECT文が返す結果の種類を明示的に定義することで、以下のメリットがあります：

1. **意図の明確化**: このSELECT文がページング用なのか、単一レコード取得なのかが明確
2. **自動化**: 結果タイプに応じて、自動的にLIMIT/OFFSETを付与
3. **AI理解性**: AIがSELECT文の意図を理解しやすくなる
4. **バリデーション**: 結果タイプに応じた適切なバリデーション（例: ページングにはORDER BY必須）

## 2. 結果タイプ（stereotype）の定義

### 2.1 提案するstereotype

```yaml
stereotype: paging | single | limit | stream
```

- **`paging`**: ページング処理（LIMIT/OFFSET自動付与）
  - パラメータ: `page`, `per_page`
  - 自動付与: `LIMIT per_page OFFSET (page - 1) * per_page`
  - 必須: `ORDER BY`（SQL Serverの制約）

- **`single`**: 単一レコード取得（LIMIT 1自動付与）
  - パラメータ: なし（または`limit: 1`を明示）
  - 自動付与: `LIMIT 1`
  - 用途: 主キー検索、最新1件取得など

- **`limit`**: 上限付き取得（LIMITのみ）
  - パラメータ: `limit`（または`max_rows`）
  - 自動付与: `LIMIT limit`
  - 用途: 最新N件取得、トップN取得など

- **`stream`**: ストリーミング（LIMITなし、全件取得）
  - パラメータ: なし
  - 自動付与: なし（LIMIT/OFFSETなし）
  - 用途: 全件エクスポート、バッチ処理など

## 3. 提案アプローチの比較

### アプローチ1: stereotypeベース（新提案・推奨）

YQL定義に`stereotype`を追加し、結果タイプに応じて自動的にLIMIT/OFFSETを付与します。

#### 構文案A: シンプルなstereotype
```yaml
query:
  stereotype: paging  # ページング用
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # limit/offsetは自動的に付与される（page=1, per_page=20がデフォルト）
```

#### 構文案B: stereotype + パラメータ定義（推奨）
```yaml
query:
  stereotype: paging
  pagination:
    page: "#{page:1}"           # ページ番号（デフォルト: 1）
    per_page: "#{per_page:20}"  # 1ページあたりの件数（デフォルト: 20）
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # limit/offsetは自動的に付与される
```

#### 構文案C: stereotypeのみ（シンプル版）
```yaml
query:
  stereotype: single  # 単一レコード取得
  select:
    - id: id
    - name: name
  from: customers
  where:
    - "id = #{id}"
  # LIMIT 1が自動的に付与される
```

```yaml
query:
  stereotype: limit
  limit: "#{max_rows:100}"  # 上限件数
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # LIMIT max_rowsが自動的に付与される
```

```yaml
query:
  stereotype: stream  # ストリーミング（全件取得）
  select:
    - id: id
    - name: name
  from: customers
  # LIMIT/OFFSETは付与されない
```

### アプローチ2: メタデータベース（従来案）

YQL定義にページング用のメタデータを追加し、コンパイラが自動的にLIMIT/OFFSETを付与します。

#### 構文案A: フラグベース
```yaml
query:
  pagination: true  # ページングを有効化
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # limit/offsetは自動的に付与される
```

#### 構文案B: パラメータ定義ベース
```yaml
query:
  pagination:
    page: "#{page:1}"           # ページ番号（デフォルト: 1）
    per_page: "#{per_page:20}"  # 1ページあたりの件数（デフォルト: 20）
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # limit/offsetは自動的に付与される
```

#### 変換ルール

**PostgreSQL:**
```sql
SELECT id AS id, name AS name
FROM customers
ORDER BY created_at DESC
LIMIT #{per_page} OFFSET #{(page - 1) * per_page}
```

**MySQL:**
```sql
SELECT id AS id, name AS name
FROM customers
ORDER BY created_at DESC
LIMIT #{(page - 1) * per_page}, #{per_page}
```

**SQL Server:**
```sql
SELECT id AS id, name AS name
FROM customers
ORDER BY created_at DESC
OFFSET #{(page - 1) * per_page} ROWS FETCH NEXT #{per_page} ROWS ONLY
```

#### メリット
- ✅ 明示的で理解しやすい
- ✅ AIが理解しやすい（メタデータとして明確）
- ✅ 既存のLIMIT/OFFSET記法と共存可能
- ✅ パラメータ名をカスタマイズ可能
- ✅ デフォルト値を設定可能

#### デメリット
- ⚠️ コンパイラの実装が必要（自動展開ロジック）
- ⚠️ ORDER BYが必須（SQL Serverの制約）

### アプローチ3: import機能を活用したラッパー

既存のSELECT定義をimportして、ページング用のラッパーを作成します。

#### 構文
```yaml
# queries/customer_list_base.yql（ページングなしのベース定義）
name: "customer_list_base"
select_definition:
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
```

```yaml
# queries/customer_list_paginated.yql（ページング付きラッパー）
imports:
  - "queries/customer_list_base.yql"

query:
  with_clauses:
    base:
      using: customer_list_base
  select:
    - id: base.id
    - name: base.name
  from: base
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
```

#### メリット
- ✅ 既存のimport機能を活用
- ✅ ベース定義とページング定義を分離可能
- ✅ 柔軟性が高い

#### デメリット
- ⚠️ 記述が冗長になる可能性
- ⚠️ シンプルなクエリには過剰
- ⚠️ ページング機能自体の実装が必要

### アプローチ4: デフォルトパラメータベース

パラメータとして`page`と`per_page`を定義し、存在する場合に自動的にLIMIT/OFFSETを展開します。

#### 構文
```yaml
query:
  parameters:
    page: 1
    per_page: 20
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # page/per_pageパラメータが存在する場合、自動的にLIMIT/OFFSETが付与される
```

#### メリット
- ✅ 既存のパラメータ定義を活用
- ✅ 暗黙的な動作（記述が少ない）

#### デメリット
- ⚠️ 暗黙的すぎて理解しにくい
- ⚠️ 意図しないページングが発生する可能性
- ⚠️ パラメータ名が固定される（`page`/`per_page`）

### アプローチ5: テンプレートエンジンレベルでの処理

YQLから生成されたSQLテンプレートに対して、テンプレートエンジンが自動的にLIMIT/OFFSETを付与します。

#### メリット
- ✅ YQLの仕様変更が不要
- ✅ 既存のテンプレートエンジンの機能を活用

#### デメリット
- ⚠️ YQLの範囲外（テンプレートエンジンの責任）
- ⚠️ データベース方言の違いを扱えない
- ⚠️ YQLの設計思想（DB抽象化）に反する

## 4. 推奨アプローチ: stereotypeベース（構文案B）

### 4.1 理由

1. **意図の明確化**: SELECT文が返す結果の種類が明確（`paging`, `single`, `limit`, `stream`）
2. **包括性**: ページングだけでなく、他の結果タイプも統一的に扱える
3. **AI理解性**: stereotypeとしてAIが理解しやすい（「このSELECT文は何を返すのか？」）
4. **柔軟性**: パラメータ名やデフォルト値をカスタマイズ可能
5. **既存仕様との整合性**: 既存のLIMIT/OFFSET記法と共存可能
6. **DB抽象化**: データベース方言の違いを自動的に処理
7. **拡張性**: 将来的に新しいstereotypeを追加可能（例: `cursor`, `window`など）

### 4.2 詳細仕様

#### 4.2.1 stereotype: paging（ページング）

```yaml
query:
  stereotype: paging
  pagination:
    page: "#{page:1}"           # ページ番号（デフォルト: 1）
    per_page: "#{per_page:20}"  # 1ページあたりの件数（デフォルト: 20）
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
```

**変換ルール:**
- 自動的に`LIMIT per_page OFFSET (page - 1) * per_page`を付与
- SQL Serverでは`ORDER BY`が必須（エラーチェック）

**生成されるSQL（PostgreSQL例）:**
```sql
SELECT id AS id, name AS name
FROM customers
ORDER BY created_at DESC
LIMIT #{per_page} OFFSET #{(page - 1) * per_page}
```

#### 4.2.2 stereotype: single（単一レコード取得）

```yaml
query:
  stereotype: single
  select:
    - id: id
    - name: name
  from: customers
  where:
    - "id = #{id}"
```

**変換ルール:**
- 自動的に`LIMIT 1`を付与

**生成されるSQL:**
```sql
SELECT id AS id, name AS name
FROM customers
WHERE id = ?
LIMIT 1
```

#### 4.2.3 stereotype: limit（上限付き取得）

```yaml
query:
  stereotype: limit
  limit: "#{max_rows:100}"  # 上限件数
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
```

**変換ルール:**
- 自動的に`LIMIT max_rows`を付与
- `limit`パラメータが必須

**生成されるSQL:**
```sql
SELECT id AS id, name AS name
FROM customers
ORDER BY created_at DESC
LIMIT #{max_rows}
```

#### 4.2.4 stereotype: stream（ストリーミング）

```yaml
query:
  stereotype: stream
  select:
    - id: id
    - name: name
  from: customers
```

**変換ルール:**
- `LIMIT/OFFSET`は付与されない（全件取得）

**生成されるSQL:**
```sql
SELECT id AS id, name AS name
FROM customers
```

#### 4.2.5 パラメータ名のカスタマイズ

```yaml
query:
  stereotype: paging
  pagination:
    page: "#{current_page:1}"
    per_page: "#{items_per_page:20}"
  # ...
```

#### 4.2.6 明示的なLIMIT/OFFSETとの共存

```yaml
query:
  stereotype: paging
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  # ...
  limit: 100  # 明示的に指定した場合、stereotypeは無視される（またはエラー）
```

**ルール:**
- `limit`または`offset`が明示的に定義されている場合、`stereotype`は無視（またはエラー）
- `stereotype`が定義されている場合、明示的な`limit`/`offset`は無視（またはエラー）

### 4.3 実装時の注意事項

1. **ORDER BYの必須チェック**: `stereotype: paging`の場合、SQL Serverでは`ORDER BY`が必須
2. **パラメータ名の衝突**: `page`や`per_page`が既存のパラメータと衝突しないように注意
3. **計算式の評価**: `offset = (page - 1) * per_page`の計算をテンプレートエンジンで行う
4. **デフォルト値の処理**: パラメータが渡されない場合のデフォルト値の適用
5. **stereotypeの検証**: 無効なstereotype値のエラーチェック
6. **stereotypeと明示的なLIMIT/OFFSETの競合**: どちらを優先するかの明確なルール

## 5. stereotypeベース vs メタデータベースの比較

### 5.1 stereotypeベースのメリット

1. **意図の明確化**: 「このSELECT文は何を返すのか？」が明確
2. **包括性**: ページングだけでなく、`single`, `limit`, `stream`も統一的に扱える
3. **拡張性**: 将来的に新しいstereotypeを追加可能
4. **AI理解性**: stereotypeとしてAIが理解しやすい
5. **ドキュメント性**: SELECT文の用途が一目で分かる

### 5.2 メタデータベースのメリット

1. **シンプル**: `pagination`という単一の概念
2. **既存仕様との整合性**: ページング専用のメタデータ

### 5.3 ハイブリッド案

`stereotype`と`pagination`を組み合わせることも可能です：

```yaml
query:
  stereotype: paging
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  # ...
```

この場合、`stereotype`で結果タイプを明示し、`pagination`で詳細なパラメータを定義します。

## 6. 結論

**推奨: stereotypeベース（構文案B）**

- 意図が明確（「このSELECT文は何を返すのか？」）
- 包括的（ページングだけでなく、他の結果タイプも統一的に扱える）
- 拡張性が高い（将来的に新しいstereotypeを追加可能）
- AIが理解しやすい
- 柔軟性が高い（パラメータ名やデフォルト値をカスタマイズ可能）

**実装方針:**
1. 最初は`stereotype: paging | single | limit | stream`の4つを実装
2. 必要に応じて新しいstereotypeを追加（例: `cursor`, `window`など）
3. `stereotype`と明示的な`limit`/`offset`の競合時は、エラーを発生させる（意図の明確化のため）

