# 共通テストフィクスチャ

このディレクトリには、すべての言語実装（Python、Go、Rustなど）で共有されるYQLテストファイルが格納されています。

## ディレクトリ構造

```
implementations/tests/fixtures/
├── simple_select/
│   ├── before.yql          # YQLファイル
│   ├── postgresql.sql      # PostgreSQL期待SQL
│   ├── mysql.sql           # MySQL期待SQL
│   ├── sqlserver.sql       # SQL Server期待SQL
│   └── oracle.sql          # Oracle期待SQL
├── select_with_join/
│   ├── before.yql
│   ├── postgresql.sql
│   └── ...
└── ...
```

## 使用方法

### Python実装

```python
from pathlib import Path
from yql import parse_file, generate_sql, Dialect

# 共通フィクスチャディレクトリを参照
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"

# YQLファイルを読み込む
query = parse_file(FIXTURES_DIR / "simple_select" / "before.yql")

# SQLを生成
sql = generate_sql(query, Dialect.POSTGRESQL)

# 期待SQLファイルと比較
expected_sql = (FIXTURES_DIR / "simple_select" / "postgresql.sql").read_text()
assert sql.strip() == expected_sql.strip()
```

### Go実装（将来）

```go
package main

import (
    "path/filepath"
    "os"
)

// 共通フィクスチャディレクトリを参照
fixturesDir := filepath.Join("..", "..", "tests", "fixtures")
yqlFile := filepath.Join(fixturesDir, "simple_select", "before.yql")
expectedSQL := filepath.Join(fixturesDir, "simple_select", "postgresql.sql")
```

### Rust実装（将来）

```rust
use std::path::PathBuf;

// 共通フィクスチャディレクトリを参照
let fixtures_dir = PathBuf::from("../../tests/fixtures");
let yql_file = fixtures_dir.join("simple_select").join("before.yql");
let expected_sql = fixtures_dir.join("simple_select").join("postgresql.sql");
```

## ファイル命名規則

### フォルダ構造
- 各テストケースはフォルダとして管理
- フォルダ名: `{operation}_{description}` 形式
- 例: `simple_select/`, `insert_with_returning/`

### ファイル名
- YQLファイル: `before.yql`（固定）
- 期待SQLファイル: `{dialect}.sql`
  - 例: `postgresql.sql`, `mysql.sql`, `sqlserver.sql`, `oracle.sql`
- 対応DB: `postgresql`, `mysql`, `sqlserver`, `oracle`

## 追加・変更時の注意

1. **言語非依存であること**: YQLファイルは言語非依存なので、どの実装でも使えるようにする
2. **一貫性**: 既存のファイル命名規則に従う
3. **テスト**: 変更後は全言語実装のテストが通ることを確認

