# SQL→YQL変換における`specs/select.md`の役割

## 概要

`specs/select.md`は、YQLからSQLへの変換ルールを定義した仕様書ですが、**逆方向の変換（SQL→YQL）のガイドラインとしても機能します**。特にAIを利用した変換において、この仕様書は非常に強力なリファレンスとなります。

## `specs/select.md`がSQL→YQL変換に有効な理由

### 1. **双方向の変換ルールが明確**

`specs/select.md`は、YQLの各構文要素とSQLの対応関係を詳細に定義しています。この対応関係は**双方向的**に機能します。

#### 例: SELECT句の変換

**YQL → SQL（仕様書の定義）:**
```yaml
# YQL
select:
  - id: c.id
  - name: c.name
```
↓ 変換ルール（`specs/select.md` 2.1章）
```sql
-- SQL
SELECT c.id AS id, c.name AS name
```

**SQL → YQL（逆変換）:**
```sql
-- SQL
SELECT c.id AS id, c.name AS name
```
↓ 逆変換ルール（`specs/select.md` 2.1章を逆に適用）
```yaml
# YQL
select:
  - id: c.id
  - name: c.name
```

### 2. **構造化された変換パターン**

`specs/select.md`は、各SQL構文要素を体系的に分類し、対応するYQL構文を定義しています。AIはこの構造化されたパターンを使って、SQLを解析し、適切なYQL構文に変換できます。

#### 変換パターンの例

| SQL構文 | YQL構文 | 仕様書の章 |
|---------|---------|-----------|
| `SELECT col AS alias` | `alias: col` | 2.1章 |
| `FROM table alias` | `from: alias: table` | 3.1章 |
| `INNER JOIN table alias ON ...` | `joins: [{type: INNER, alias: ..., table: ..., on: ...}]` | 4.1章 |
| `WHERE condition1 AND condition2` | `where: ["condition1", "condition2"]` | 6.1章 |
| `GROUP BY col1, col2` | `group_by: [col1, col2]` | 7.1章 |
| `HAVING COUNT(*) > 10` | `having: ["COUNT(*) > 10"]` | 8.1章 |
| `ORDER BY col DESC` | `order_by: [{field: col, direction: DESC}]` | 9.1章 |
| `LIMIT 10 OFFSET 20` | `limit: 10, offset: 20` | 10.1章 |

### 3. **制約とルールの明確化**

`specs/select.md`は、YQLの制約とルールを明確に定義しています。これにより、AIは変換時に適切な制約を適用できます。

#### 制約の例

**エイリアス必須（2.1章）:**
- YQLではすべてのSELECT句のカラムにエイリアスが必須
- SQLにエイリアスがない場合、AIは自動的にエイリアスを生成する必要がある

**FROM句でのサブクエリ禁止（3.2章）:**
- SQLにFROM句のサブクエリがある場合、AIはWITH句（CTE）に変換する必要がある

**WHERE句の簡略化（6.1章）:**
- SQLの複雑なWHERE条件を、YQLの配列形式（`where: ["condition1", "condition2"]`）に変換

### 4. **データベース方言の抽象化**

`specs/select.md`は、複数のデータベース方言（PostgreSQL、MySQL、SQL Server）の違いを抽象化しています。AIは、特定のデータベース方言のSQLを、YQLの抽象構文に変換できます。

#### 例: LIMIT/OFFSETの変換

**PostgreSQL:**
```sql
LIMIT 10 OFFSET 20
```

**MySQL:**
```sql
LIMIT 20, 10
```

**SQL Server:**
```sql
OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY
```

↓ すべて同じYQLに変換可能
```yaml
limit: 10
offset: 20
```

## AIを使ったSQL→YQL変換の利点

### 1. **パーサー実装の不要**

従来のアプローチでは、SQLパーサーを実装する必要がありました。しかし、AIを利用すれば、`specs/select.md`をガイドラインとして、自然言語処理で変換できます。

**従来のアプローチ:**
```
SQL → [SQLパーサー] → AST → [YQL生成器] → YQL
```

**AIアプローチ:**
```
SQL + specs/select.md → [AI] → YQL
```

### 2. **柔軟性の高い変換**

AIは、`specs/select.md`のルールを柔軟に適用できます。例えば：
- エイリアスがない場合の自動生成
- 複雑なWHERE条件の適切な分解
- サブクエリのCTEへの変換

### 3. **仕様書の更新に追従しやすい**

`specs/select.md`が更新されれば、AIのプロンプトに新しい仕様を追加するだけで、変換ロジックを更新できます。パーサーのコードを変更する必要がありません。

### 4. **エラーハンドリングの改善**

`specs/select.md`の「15. エラーハンドリング」セクションを参照することで、AIは変換時のエラーを適切に検出・報告できます。

## 実際の変換例での検証

### 例1: 基本的なJOINクエリ

**元のSQL:**
```sql
SELECT c.id, c.name, o.id as order_id, o.order_date, o.amount
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id;
```

**変換されたYQL:**
```yaml
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

**`specs/select.md`の参照箇所:**
- 2.1章: SELECT句の変換（エイリアス必須）
- 3.1章: FROM句の変換（エイリアスを先頭に）
- 4.1章: JOIN句の変換（type, alias, table, on）

### 例2: 複雑な集計クエリ

**元のSQL:**
```sql
SELECT c.id, c.name, COUNT(o.id) as order_count, SUM(o.amount) as total
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE c.status = 'active'
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 0
ORDER BY total DESC
LIMIT 10;
```

**変換されたYQL:**
```yaml
select:
  - id: c.id
  - name: c.name
  - order_count: "COUNT(o.id)"
  - total: "SUM(o.amount)"
from: c: customers
joins:
  - type: LEFT
    alias: o
    table: orders
    on: "c.id = o.customer_id"
where:
  - "c.status = 'active'"
group_by: [c.id, c.name]
having:
  - "COUNT(o.id) > 0"
order_by:
  - field: total
    direction: DESC
limit: 10
```

**`specs/select.md`の参照箇所:**
- 2.3章: 集計関数の変換
- 6.1章: WHERE句の変換（配列形式）
- 7.1章: GROUP BY句の変換
- 8.1章: HAVING句の変換
- 9.1章: ORDER BY句の変換（エイリアス参照）
- 10.1章: LIMIT句の変換

## AIプロンプトでの活用方法

### プロンプト例

```
以下のSQLをYQLに変換してください。
`specs/select.md`の仕様に従って変換してください。

**変換ルール:**
1. SELECT句: すべてのカラムにエイリアスが必須（2.1章）
2. FROM句: エイリアスを先頭に記述（3.1章）
3. JOIN句: type, alias, table, onの形式（4.1章）
4. WHERE句: 配列形式で記述（6.1章）
5. その他の句も同様に`specs/select.md`の仕様に従う

**SQL:**
[SQLコード]

**注意事項:**
- FROM句でのサブクエリは禁止（3.2章）。WITH句（CTE）に変換してください。
- エイリアスがない場合は、適切なエイリアスを生成してください。
```

## 結論

**`specs/select.md`は、SQL→YQL変換の強力なガイドラインとして機能します。**

主な理由：
1. **双方向の変換ルールが明確**: YQL→SQLのルールを逆に適用できる
2. **構造化された変換パターン**: 体系的に分類された構文要素
3. **制約とルールの明確化**: 変換時の制約が明確
4. **データベース方言の抽象化**: 複数のDB方言を統一的なYQLに変換可能

**AIを使った変換の利点:**
- パーサー実装が不要
- 柔軟性が高い
- 仕様書の更新に追従しやすい
- エラーハンドリングが改善される

実際の検証でも、`specs/select.md`に従って正確に変換できていることが確認されています。

