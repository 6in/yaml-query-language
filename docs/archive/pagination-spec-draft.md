---
layout: default
title: Pagination Spec Draft
---

# YQL pagination構文 仕様書（ドラフト）

## 1. 概要

YQLのSELECT文でページング処理を簡潔に記述するための`pagination`構文を定義します。

## 2. 基本構文

### 2.1 pagination構文

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
```

### 2.2 変換ルール

`pagination`構文は、内部的に`limit`と`offset`に展開されます：

```yaml
# pagination構文
pagination:
  page: "#{page:1}"
  per_page: "#{per_page:20}"

# 内部的に以下に展開される:
limit: "#{per_page:20}"
offset: "$((${page:1} - 1) * ${per_page:20})"
```

### 2.3 paginationが定義されていない場合

`pagination`が定義されていない場合、ページングは適用されません（LIMIT/OFFSETなし）。

```yaml
query:
  select:
    - id: id
    - name: name
  from: customers
  # paginationなし = LIMIT/OFFSETなし（全件取得）
```

**注意**: `pagination: false`のような明示的な無効化は不要です。`pagination`が定義されていない = ページングなし（デフォルト）と判断します。

## 3. パラメータのカスタマイズ

### 3.1 パラメータ名のカスタマイズ

パラメータ名はカスタマイズ可能です：

```yaml
query:
  pagination:
    page: "#{current_page:1}"
    per_page: "#{items_per_page:20}"
  # ...
```

### 3.2 デフォルト値

デフォルト値は`#{paramName:defaultValue}`形式で指定します：

```yaml
query:
  pagination:
    page: "#{page:1}"           # デフォルト: 1
    per_page: "#{per_page:20}"  # デフォルト: 20
  # ...
```

## 4. 明示的なLIMIT/OFFSETとの関係

### 4.1 競合の扱い

`pagination`と明示的な`limit`/`offset`が同時に定義されている場合、エラーを発生させます。

```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  limit: 100  # エラー: paginationとlimit/offsetは同時に使用できません
```

**理由**: 意図の明確化のため。どちらを使うか明確に判断できるようにする。

### 4.2 推奨パターン

- **ページング**: `pagination`構文を使用
- **上限付き取得**: 既存の`limit`を使用
- **単一レコード取得**: 既存の`limit: 1`を使用
- **全件取得**: `limit`/`offset`なし（デフォルト）

## 5. データベース方言の違い

### 5.1 PostgreSQL

```sql
LIMIT #{per_page} OFFSET #{(page - 1) * per_page}
```

### 5.2 MySQL

```sql
LIMIT #{(page - 1) * per_page}, #{per_page}
```

### 5.3 SQL Server

```sql
OFFSET #{(page - 1) * per_page} ROWS FETCH NEXT #{per_page} ROWS ONLY
```

**注意**: SQL Serverでは`ORDER BY`が必須です。`pagination`が定義されている場合、`order_by`が存在しない場合はエラーを発生させます。

## 6. 実装時の注意事項

### 6.1 計算式の評価

`offset = (page - 1) * per_page`の計算は、テンプレートエンジンで行います。

### 6.2 バリデーション

以下の場合にエラーを発生させます：

1. `pagination`と`limit`/`offset`が同時に定義されている
2. `pagination`が定義されているが、`order_by`が存在しない（SQL Serverの場合）

### 6.3 デフォルト値の処理

パラメータが渡されない場合、デフォルト値を使用します。

## 7. 使用例

### 7.1 基本的なページング

```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
```

### 7.2 カスタムパラメータ名

```yaml
query:
  pagination:
    page: "#{current_page:1}"
    per_page: "#{items_per_page:20}"
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
```

### 7.3 ページングなし（全件取得）

```yaml
query:
  select:
    - id: id
    - name: name
  from: customers
  # paginationなし = LIMIT/OFFSETなし
```

