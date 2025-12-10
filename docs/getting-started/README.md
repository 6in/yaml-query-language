# 🔰 初めての方へ

YQL (YAML Query Language) を初めて触る方向けのガイドです。

## YQLとは？

YQLは、**SQLをYAML形式で記述する言語**です。

```yaml
# YQL
query:
  select:
    - name: c.name
    - email: c.email
  from: c: customers
  where:
    - "c.status = 'active'"
```

↓ 自動変換

```sql
-- SQL (PostgreSQL)
SELECT c.name AS name, c.email AS email
FROM customers c
WHERE c.status = 'active';
```

## なぜYQLを使うのか？

| 課題 | YQLによる解決 |
|------|--------------|
| **複数DBの方言の違い** | 1つのYQLから複数DB向けSQLを生成 |
| **SQLが読みにくい** | YAML形式で構造化、可読性向上 |
| **AIとの連携が難しい** | 構造化されたYQLはAIが理解しやすい |
| **仕様書とコードの乖離** | YQL自体が実行可能な仕様書 |

## 読む順番

| 順番 | ドキュメント | 内容 |
|------|-------------|------|
| 1 | **このページ** | YQLの概要を理解 |
| 2 | [クイックスタート](quick-start.md) | 基本的な書き方を学ぶ |
| 3 | [SELECT仕様書](../../specs/select.md) | 詳細な仕様を確認 |
| 4 | [ユースケース](../guides/yql-use-cases-overview.md) | 活用方法を知る |

## 今すぐできること

### ✅ AIを使ってSQL→YQL変換

1. [specs/select.md](../../specs/select.md) をAI（ChatGPT、Claude等）に渡す
2. 変換したいSQLを入力
3. YQLが生成される

### ✅ 要件整理ツールとして使う

YAMLで要件を構造化するだけでも価値があります：

```yaml
# 要件: 先月の売上トップ10顧客
query:
  select:
    - 顧客名: c.name
    - 売上合計: "SUM(o.amount)"
  from: c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
  where:
    - "o.order_date >= '2024-11-01'"
  order_by:
    - field: 売上合計
      direction: DESC
  limit: 10
```

## まだできないこと

| 機能 | ステータス |
|------|-----------|
| YQLパーサー（リアルタイムSQL生成） | 🚧 開発中 |
| IDE拡張（補完・検証） | 📝 計画中 |
| Webプレイグラウンド | 📝 計画中 |

## 用語集

| 用語 | 説明 |
|------|------|
| **YQL** | YAML Query Language の略 |
| **DSL** | Domain Specific Language（特定用途向け言語） |
| **パーサー** | YQLを解析してAST（抽象構文木）に変換するプログラム |
| **ジェネレーター** | ASTからSQLを生成するプログラム |
| **AST** | Abstract Syntax Tree（抽象構文木）。プログラムの構造を木構造で表現したもの |

## 次のステップ

→ [クイックスタート](quick-start.md) に進む
