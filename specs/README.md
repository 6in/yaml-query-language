# 📋 YQL仕様書

YQLの言語仕様書です。

## 仕様書一覧

### DML仕様

| 仕様書 | 内容 | ステータス |
|--------|------|-----------|
| [select.md](select.md) | SELECT文の変換ルール、JOIN、CTE、ページング等 | ✅ 完成 |
| [insert.md](insert.md) | INSERT文の変換ルール、バルクINSERT等 | ✅ 完成 |
| [update.md](update.md) | UPDATE文の変換ルール、JOIN UPDATE等 | ✅ 完成 |
| [delete.md](delete.md) | DELETE文の変換ルール、論理削除等 | ✅ 完成 |
| [upsert.md](upsert.md) | UPSERT文の変換ルール、バッチ処理等 | ✅ 完成 |

### DDL・その他仕様

| 仕様書 | 内容 | ステータス |
|--------|------|-----------|
| [schema.md](schema.md) | テーブル、ビュー、インデックス等の定義 | ✅ 完成 |
| [import.md](import.md) | using機能、マクロ、スキーマ参照 | ✅ 完成 |
| [procedure.md](procedure.md) | ストアドプロシージャ定義（解析専用） | ✅ 完成 |

## 読む順番

### 初めての方

1. [select.md](select.md) - 最も基本的なSELECT文から
2. [insert.md](insert.md) / [update.md](update.md) / [delete.md](delete.md) - 他のDML
3. [schema.md](schema.md) - スキーマ定義

### 特定の目的がある方

| 目的 | 読むべき仕様書 |
|------|---------------|
| SELECTの書き方を知りたい | [select.md](select.md) |
| INSERT/UPDATE/DELETEを書きたい | [insert.md](insert.md), [update.md](update.md), [delete.md](delete.md) |
| UPSERTを書きたい | [upsert.md](upsert.md) |
| スキーマを定義したい | [schema.md](schema.md) |
| YQLを再利用したい | [import.md](import.md) |
| ストアドプロシージャを解析したい | [procedure.md](procedure.md) |

## 仕様書の構成

各仕様書は以下の構成になっています：

1. **概要**: 目的と対象範囲
2. **基本構文**: YQLの書き方
3. **変換ルール**: YQL → SQL の変換方法
4. **DB別の違い**: PostgreSQL/MySQL/SQL Server/Oracle の差異
5. **パラメータ**: パラメータバインディングの方法
6. **エラーハンドリング**: エラー時の動作
7. **例**: 具体的な使用例

## パラメータ記法

全仕様書で共通のパラメータ記法：

| 記法 | 用途 | 例 |
|------|------|-----|
| `#{name}` | 単一値のバインド | `"c.id = #{customer_id}"` |
| `${name}` | 配列展開、条件分岐 | `"c.status IN (${statuses})"` |
| `@{name}` | マクロパラメータ | `@{column_name}` |

## 対応データベース

| データベース | SELECT | INSERT | UPDATE | DELETE | UPSERT |
|-------------|--------|--------|--------|--------|--------|
| PostgreSQL | ✅ | ✅ | ✅ | ✅ | ✅ |
| MySQL | ✅ | ✅ | ✅ | ✅ | ✅ |
| SQL Server | ✅ | ✅ | ✅ | ✅ | ✅ |
| Oracle | ✅ | ✅ | ✅ | ✅ | ✅ |

## 関連ドキュメント

- [クイックスタート](../docs/getting-started/quick-start.md) - 基本的な使い方
- [アーキテクチャ](../docs/architecture/README.md) - 技術設計
- [ユースケース](../docs/guides/yql-use-cases-overview.md) - 活用方法

