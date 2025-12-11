# YQL Parser (Python)

YQL (YAML Query Language) のPython実装です。

## 概要

このパッケージは、YQLをパースしてAST（抽象構文木）に変換し、各データベース方言のSQLを生成します。

## インストール

```bash
# 開発モードでインストール
cd implementations/python
pip install -e ".[dev]"
```

## 使用方法

### コマンドライン

```bash
# YQLファイルをパースしてASTを表示
yql parse query.yql

# YQLファイルからSQLを生成
yql generate query.yql

# 特定のデータベース方言を指定
yql generate query.yql --dialect postgresql
yql generate query.yql --dialect mysql

# ファイルに出力
yql generate query.yql -o output.sql
```

### Pythonコード

```python
from yql import parse, generate_sql, Dialect

# YQL文字列をパース
yql_content = """
query:
  select:
    - id: c.id
    - name: c.name
  from:
    c: customers
  where:
    - "c.status = 'active'"
"""

# パース
query = parse(yql_content)

# SQL生成
sql = generate_sql(query, Dialect.POSTGRESQL)
print(sql)
```

出力:
```sql
SELECT
  c.id AS id,
  c.name AS name
FROM customers c
WHERE c.status = 'active'
```

## 対応状況

### データベース方言

| 方言 | 状態 |
|------|------|
| PostgreSQL | ✅ 対応 |
| MySQL | ✅ 対応 |
| SQL Server | ✅ 対応 |
| Oracle | 🚧 未実装 |

### SELECT機能

| 機能 | 状態 |
|------|------|
| SELECT句 | ✅ 対応 |
| FROM句（エイリアス必須） | ✅ 対応 |
| JOIN句（INNER/LEFT/RIGHT/FULL/CROSS） | ✅ 対応 |
| WHERE句 | ✅ 対応 |
| GROUP BY句 | ✅ 対応 |
| HAVING句 | ✅ 対応 |
| ORDER BY句 | ✅ 対応 |
| LIMIT/OFFSET | ✅ 対応 |
| WITH句（CTE） | ✅ 対応 |
| pagination | ✅ 対応 |

### DML機能

| 機能 | 状態 |
|------|------|
| INSERT | ✅ 対応 |
| UPDATE | ✅ 対応 |
| DELETE | ✅ 対応 |
| UPSERT | 🚧 未実装 |
| RETURNING句 | ✅ 対応 (PostgreSQL) |

### その他

| 機能 | 状態 |
|------|------|
| import機能 | 🚧 未実装 |
| マクロ展開 | 🚧 未実装 |

## 開発

### テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=yql

# 特定のテストファイル
pytest tests/test_parser.py
```

### コード品質

```bash
# リンター
ruff check src tests

# 型チェック
mypy src
```

## ディレクトリ構成

```
implementations/python/
├── pyproject.toml      # パッケージ設定
├── README.md           # このファイル
├── src/
│   └── yql/
│       ├── __init__.py # パッケージエントリポイント
│       ├── ast.py      # AST定義
│       ├── parser.py   # YAMLパーサー
│       ├── cli.py      # CLIエントリポイント
│       └── generator/
│           ├── __init__.py
│           ├── base.py        # 基底ジェネレーター
│           └── postgresql.py  # PostgreSQL用
└── tests/
    ├── __init__.py
    ├── test_parser.py    # パーサーテスト
    └── test_generator.py # ジェネレーターテスト
```

## 仕様書

詳細な仕様は以下を参照してください：

- [SELECT文仕様](../../specs/select.md)
- [INSERT文仕様](../../specs/insert.md)
- [UPDATE文仕様](../../specs/update.md)
- [DELETE文仕様](../../specs/delete.md)
- [import機能仕様](../../specs/import.md)

## ライセンス

MIT

