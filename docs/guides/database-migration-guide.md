---
layout: default
title: Database Migration Guide
---

# YQLを使ったデータベース移行ガイド

## 1. 概要

このドキュメントは、YQLを中間形式として使用し、データベース間の移行を行う方法を説明します。

### 1.1 対象読者

- データベース移行を検討しているエンジニア
- Oracle→PostgreSQL等の移行プロジェクト担当者
- YQLを活用したDB抽象化に興味がある方

### 1.2 YQLを使った移行のメリット

| メリット | 説明 |
|----------|------|
| **中間形式の標準化** | YQLが共通言語となり、複数DB対応の基盤になる |
| **段階的移行** | YQL変換後に検証可能で、リスクを低減 |
| **ドキュメント化** | YQLがそのまま仕様書になる |
| **AI活用** | SQL→YQL変換はAIが得意で効率化可能 |
| **検証可能性** | YQL→SQL変換は決定的で品質担保しやすい |
| **将来の柔軟性** | YQLがあれば他DBへの移行も容易 |

## 2. 移行フロー

### 2.1 全体フロー

```
┌─────────────────────────────────────────────────────────────┐
│                    DB移行フロー                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [移行元 SQL]  (例: Oracle)                                 │
│       │                                                     │
│       ▼ (AI変換)                                            │
│  [YQL]  ←── 検証・レビュー ←── スキーマ定義                  │
│       │                                                     │
│       ▼ (パーサー/ジェネレーター)                            │
│  [移行先 SQL]  (例: PostgreSQL)                             │
│       │                                                     │
│       ▼ (実行・検証)                                        │
│  [移行先 DB]                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 段階的アプローチ

| Phase | 対象 | 内容 |
|-------|------|------|
| Phase 1 | スキーマ | テーブル、インデックス、制約、シーケンス |
| Phase 2 | SELECT | 基本SELECT、JOIN、サブクエリ、集計 |
| Phase 3 | DML | INSERT、UPDATE、DELETE、UPSERT |
| Phase 4 | 複雑機能 | 階層クエリ、ストアドプロシージャ等 |

## 3. 移行パターン別ガイド

### 3.1 Oracle → PostgreSQL

#### 3.1.1 関数マッピング

| Oracle | PostgreSQL | YQLでの扱い |
|--------|------------|-------------|
| `NVL(a, b)` | `COALESCE(a, b)` | 式として記述 |
| `NVL2(a, b, c)` | `CASE WHEN a IS NOT NULL THEN b ELSE c END` | 式として記述 |
| `DECODE(a, b, c, d)` | `CASE a WHEN b THEN c ELSE d END` | 式として記述 |
| `SYSDATE` | `CURRENT_TIMESTAMP` | 式として記述 |
| `SYSTIMESTAMP` | `CURRENT_TIMESTAMP` | 式として記述 |
| `ROWNUM` | `ROW_NUMBER() OVER ()` または `LIMIT` | ページングはYQLのlimitを使用 |
| `TO_DATE(s, fmt)` | `TO_DATE(s, fmt)` | 書式の違いに注意 |
| `TO_CHAR(d, fmt)` | `TO_CHAR(d, fmt)` | 書式の違いに注意 |
| `SUBSTR(s, start, len)` | `SUBSTRING(s FROM start FOR len)` | 式として記述 |
| `INSTR(s, sub)` | `POSITION(sub IN s)` | 式として記述 |
| `LENGTH(s)` | `LENGTH(s)` | 互換 |
| `TRIM(s)` | `TRIM(s)` | 互換 |
| `UPPER(s)` | `UPPER(s)` | 互換 |
| `LOWER(s)` | `LOWER(s)` | 互換 |

#### 3.1.2 構文変換

**外部結合（Oracle旧構文）**

```sql
-- Oracle（旧構文）
SELECT * FROM a, b WHERE a.id = b.id(+)

-- PostgreSQL
SELECT * FROM a LEFT JOIN b ON a.id = b.id
```

**YQL:**
```yaml
query:
  select:
    - all_columns: "*"
  from: a: a
  joins:
    - type: LEFT
      alias: b
      table: b
      on: "a.id = b.id"
```

**ROWNUM（ページング）**

```sql
-- Oracle
SELECT * FROM customers WHERE ROWNUM <= 10

-- PostgreSQL
SELECT * FROM customers c LIMIT 10
```

**YQL:**
```yaml
query:
  select:
    - all_columns: "c.*"
  from: c: customers
  limit: 10
```

**DUAL テーブル**

```sql
-- Oracle
SELECT SYSDATE FROM DUAL

-- PostgreSQL
SELECT CURRENT_TIMESTAMP
```

**YQL:**
```yaml
query:
  select:
    - current_time: "CURRENT_TIMESTAMP"
```

**階層クエリ（CONNECT BY）**

```sql
-- Oracle
SELECT employee_id, manager_id, LEVEL
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id

-- PostgreSQL
WITH RECURSIVE emp_hierarchy AS (
  SELECT employee_id, manager_id, 1 AS level
  FROM employees
  WHERE manager_id IS NULL
  UNION ALL
  SELECT e.employee_id, e.manager_id, h.level + 1
  FROM employees e
  INNER JOIN emp_hierarchy h ON e.manager_id = h.employee_id
)
SELECT * FROM emp_hierarchy
```

**YQL:**
```yaml
query:
  with_clauses:
    emp_hierarchy:
      recursive: true
      base_query:
        select:
          - employee_id: e.employee_id
          - manager_id: e.manager_id
          - level: "1"
        from: e: employees
        where:
          - "e.manager_id IS NULL"
      recursive_query:
        select:
          - employee_id: e.employee_id
          - manager_id: e.manager_id
          - level: "h.level + 1"
        from: e: employees
        joins:
          - type: INNER
            alias: h
            table: emp_hierarchy
            on: "e.manager_id = h.employee_id"
  select:
    - employee_id: eh.employee_id
    - manager_id: eh.manager_id
    - level: eh.level
  from: eh: emp_hierarchy
```

#### 3.1.3 データ型マッピング

| Oracle | PostgreSQL | 備考 |
|--------|------------|------|
| `NUMBER` | `NUMERIC` | 精度・スケール指定 |
| `NUMBER(n)` | `NUMERIC(n)` | 整数 |
| `NUMBER(p,s)` | `NUMERIC(p,s)` | 固定小数点 |
| `VARCHAR2(n)` | `VARCHAR(n)` | 可変長文字列 |
| `CHAR(n)` | `CHAR(n)` | 固定長文字列 |
| `CLOB` | `TEXT` | 長いテキスト |
| `BLOB` | `BYTEA` | バイナリ |
| `DATE` | `TIMESTAMP` | Oracleの`DATE`は時刻を含む |
| `TIMESTAMP` | `TIMESTAMP` | 互換 |
| `TIMESTAMP WITH TIME ZONE` | `TIMESTAMPTZ` | 互換 |
| `RAW(n)` | `BYTEA` | バイナリ |
| `LONG` | `TEXT` | 非推奨 |

### 3.2 MySQL → PostgreSQL

#### 3.2.1 関数マッピング

| MySQL | PostgreSQL | YQLでの扱い |
|-------|------------|-------------|
| `IFNULL(a, b)` | `COALESCE(a, b)` | 式として記述 |
| `IF(cond, a, b)` | `CASE WHEN cond THEN a ELSE b END` | 式として記述 |
| `NOW()` | `CURRENT_TIMESTAMP` | 式として記述 |
| `CURDATE()` | `CURRENT_DATE` | 式として記述 |
| `DATE_FORMAT(d, fmt)` | `TO_CHAR(d, fmt)` | 書式の違いに注意 |
| `STR_TO_DATE(s, fmt)` | `TO_DATE(s, fmt)` | 書式の違いに注意 |
| `CONCAT(a, b, ...)` | `CONCAT(a, b, ...)` | 互換 |
| `GROUP_CONCAT(...)` | `STRING_AGG(...)` | 構文が異なる |
| `LIMIT n, m` | `LIMIT m OFFSET n` | 順序が逆 |

#### 3.2.2 構文変換

**LIMIT（オフセット付き）**

```sql
-- MySQL
SELECT * FROM customers LIMIT 10, 20

-- PostgreSQL
SELECT * FROM customers c LIMIT 20 OFFSET 10
```

**YQL:**
```yaml
query:
  select:
    - all_columns: "c.*"
  from: c: customers
  limit: 20
  offset: 10
```

**AUTO_INCREMENT → SERIAL**

```sql
-- MySQL
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY
)

-- PostgreSQL
CREATE TABLE users (
  id SERIAL PRIMARY KEY
)
```

**YQL Schema:**
```yaml
tables:
  users:
    label: "ユーザー"
    columns:
      id:
        type: integer
        label: "ID"
        constraints:
          primary_key: true
          auto_increment: true
```

### 3.3 SQL Server → PostgreSQL

#### 3.3.0 YQLを使う優位性

**重要:** SQL Server → PostgreSQL移行において、YQLを使うアプローチは特に有効です。

| 観点 | Oracle → PG | SQL Server → PG |
|------|-------------|-----------------|
| 成熟ツール | ora2pg（15年+の歴史） | **なし** |
| AWS SCT | 対応 | 対応（商用） |
| OSS選択肢 | 豊富 | **限定的** |
| YQLの相対的価値 | 条件付き | **高い** |

**SQL Server → PostgreSQL移行でYQLを使うメリット:**

1. **成熟したOSSツールがない**: ora2pg相当のツールが存在しないため、YQL + AIの組み合わせが現実的な解
2. **AWS SCTは商用**: コストが発生するため、OSSで対応したい場合はYQLが有力
3. **T-SQL固有構文の吸収**: TOP、CROSS APPLY、OUTPUT等をYQLで抽象化
4. **段階的移行**: YQLを中間形式として検証しながら進められる
5. **ドキュメント化**: 移行後もYQLが仕様書として残る

#### 3.3.1 関数マッピング

| SQL Server | PostgreSQL | YQLでの扱い |
|------------|------------|-------------|
| `ISNULL(a, b)` | `COALESCE(a, b)` | 式として記述 |
| `GETDATE()` | `CURRENT_TIMESTAMP` | 式として記述 |
| `DATEADD(unit, n, d)` | `d + INTERVAL 'n unit'` | 式として記述 |
| `DATEDIFF(unit, d1, d2)` | `DATE_PART('unit', d2 - d1)` | 式として記述 |
| `TOP n` | `LIMIT n` | ページングはYQLのlimitを使用 |
| `LEN(s)` | `LENGTH(s)` | 式として記述 |
| `CHARINDEX(sub, s)` | `POSITION(sub IN s)` | 式として記述 |
| `CONVERT(type, value)` | `CAST(value AS type)` | 式として記述 |
| `CAST(value AS VARCHAR(MAX))` | `CAST(value AS TEXT)` | 式として記述 |

#### 3.3.2 構文変換

**TOP（ページング）**

```sql
-- SQL Server
SELECT TOP 10 * FROM customers

-- PostgreSQL
SELECT * FROM customers c LIMIT 10
```

**YQL:**
```yaml
query:
  select:
    - all_columns: "c.*"
  from: c: customers
  limit: 10
```

**IDENTITY → SERIAL**

```sql
-- SQL Server
CREATE TABLE users (
  id INT IDENTITY(1,1) PRIMARY KEY
)

-- PostgreSQL
CREATE TABLE users (
  id SERIAL PRIMARY KEY
)
```

**OFFSET-FETCH（ページング）**

```sql
-- SQL Server
SELECT * FROM customers
ORDER BY id
OFFSET 10 ROWS FETCH NEXT 20 ROWS ONLY

-- PostgreSQL
SELECT * FROM customers c
ORDER BY c.id
LIMIT 20 OFFSET 10
```

**YQL:**
```yaml
query:
  select:
    - all_columns: "c.*"
  from: c: customers
  order_by:
    - field: c.id
      direction: ASC
  pagination:
    page: 1
    per_page: 20
```

**WITH (NOLOCK) ヒント**

```sql
-- SQL Server
SELECT * FROM customers WITH (NOLOCK)

-- PostgreSQL（ヒントは削除、分離レベルで制御）
SELECT * FROM customers c
```

**YQL:**
```yaml
query:
  select:
    - all_columns: "c.*"
  from: c: customers
  # ヒントはYQLでは無視される（DB側の設定で制御）
```

**OUTPUT句 → RETURNING**

```sql
-- SQL Server
DELETE FROM customers OUTPUT deleted.* WHERE id = 1

-- PostgreSQL
DELETE FROM customers WHERE id = 1 RETURNING *
```

**CROSS APPLY → LATERAL JOIN**

```sql
-- SQL Server
SELECT o.order_id, i.item_name
FROM orders o
CROSS APPLY (
  SELECT TOP 1 item_name
  FROM order_items
  WHERE order_id = o.order_id
  ORDER BY price DESC
) AS i

-- PostgreSQL
SELECT o.order_id, i.item_name
FROM orders o
CROSS JOIN LATERAL (
  SELECT item_name
  FROM order_items
  WHERE order_id = o.order_id
  ORDER BY price DESC
  LIMIT 1
) AS i
```

**注意:** CROSS APPLY/OUTER APPLYは、YQLで直接サポートする場合は `specs/select.md` への追加が必要です。現時点では式として記述するか、WITH句で代替します。

#### 3.3.3 データ型マッピング

| SQL Server | PostgreSQL | 備考 |
|------------|------------|------|
| `INT` | `INTEGER` | 互換 |
| `BIGINT` | `BIGINT` | 互換 |
| `SMALLINT` | `SMALLINT` | 互換 |
| `TINYINT` | `SMALLINT` | PostgreSQLにTINYINTなし |
| `BIT` | `BOOLEAN` | 0/1 → true/false |
| `DECIMAL(p,s)` | `NUMERIC(p,s)` | 互換 |
| `FLOAT` | `DOUBLE PRECISION` | 互換 |
| `REAL` | `REAL` | 互換 |
| `VARCHAR(n)` | `VARCHAR(n)` | 互換 |
| `VARCHAR(MAX)` | `TEXT` | 無制限テキスト |
| `NVARCHAR(n)` | `VARCHAR(n)` | PostgreSQLはUnicode標準 |
| `CHAR(n)` | `CHAR(n)` | 互換 |
| `TEXT` | `TEXT` | 互換 |
| `DATETIME` | `TIMESTAMP` | 互換 |
| `DATETIME2` | `TIMESTAMP` | 互換 |
| `DATE` | `DATE` | 互換 |
| `TIME` | `TIME` | 互換 |
| `DATETIMEOFFSET` | `TIMESTAMPTZ` | タイムゾーン付き |
| `UNIQUEIDENTIFIER` | `UUID` | GUID |
| `VARBINARY(n)` | `BYTEA` | バイナリ |
| `IMAGE` | `BYTEA` | 非推奨 |

#### 3.3.4 移行時の注意点

| 項目 | 説明 |
|------|------|
| **照合順序** | SQL Serverの照合順序はPostgreSQLと異なる。大文字小文字の扱いに注意 |
| **NULL結合** | SQL Serverの`+`でのNULL結合はNULLを返す。PostgreSQLの`||`も同様だが、`CONCAT`は異なる |
| **日付演算** | `DATEADD`/`DATEDIFF`は`INTERVAL`演算に変換 |
| **ヒント** | クエリヒント（`WITH (NOLOCK)`等）は削除。分離レベルで制御 |
| **自動採番** | `IDENTITY`は`SERIAL`または`GENERATED`に変換 |

## 4. 移行手順

### 4.1 Phase 1: スキーマ移行

1. **DDL抽出**: 移行元DBからDDLを抽出
2. **YQL Schema変換**: DDLをYQL Schema形式に変換（AIまたは手動）
3. **レビュー**: YQL Schemaの確認・修正
4. **DDL生成**: YQL Schemaから移行先DB用DDLを生成
5. **実行**: 移行先DBでDDLを実行

### 4.2 Phase 2: クエリ移行（SELECT）

1. **SQL抽出**: アプリケーションからSELECT文を抽出
2. **YQL変換**: SQLをYQL形式に変換（AIまたは手動）
3. **レビュー**: YQLの確認・修正
4. **SQL生成**: YQLから移行先DB用SQLを生成
5. **検証**: 結果の比較検証

### 4.3 Phase 3: DML移行

1. **SQL抽出**: INSERT/UPDATE/DELETE文を抽出
2. **YQL変換**: SQLをYQL形式に変換
3. **レビュー**: YQLの確認・修正
4. **SQL生成**: YQLから移行先DB用SQLを生成
5. **検証**: 動作検証

### 4.4 Phase 4: 複雑機能

1. **対象特定**: PL/SQL、ストアドプロシージャ等を特定
2. **個別対応**: YQL対象外の機能は手動で変換
3. **検証**: 動作検証

## 5. 検証方法

### 5.1 ラウンドトリップ検証

```
移行元 SQL → YQL → 移行先 SQL → 実行 → 結果比較
```

1. 移行元DBで元のSQLを実行し、結果を保存
2. SQLをYQLに変換
3. YQLから移行先DB用SQLを生成
4. 移行先DBで生成SQLを実行
5. 結果を比較

### 5.2 検証スクリプト例

```bash
# 1. 移行元DBで実行
psql -h oracle-host -c "SELECT ..." > expected.csv

# 2. YQL変換（AIまたはツール）
# oracle.sql → query.yql

# 3. SQL生成（YQLパーサー）
# query.yql → postgresql.sql

# 4. 移行先DBで実行
psql -h postgres-host -c "SELECT ..." > actual.csv

# 5. 結果比較
diff expected.csv actual.csv
```

### 5.3 検証観点

| 観点 | 確認内容 |
|------|----------|
| **結果の一致** | 行数、値が一致するか |
| **NULL処理** | NULL値の扱いが同じか |
| **日付処理** | 日付の精度、タイムゾーンが同じか |
| **文字コード** | 文字化けがないか |
| **パフォーマンス** | 実行時間が許容範囲か |

## 6. 注意事項

### 6.1 YQL対象外の機能

以下の機能はYQLの対象外であり、別途対応が必要です：

| 機能 | 対応方針 |
|------|----------|
| PL/SQL / PL/pgSQL | 手動変換 |
| ストアドプロシージャ | 手動変換 |
| トリガー | 手動変換 |
| パッケージ | スキーマ+関数に分解 |
| ユーザー定義型 | 個別対応 |

### 6.2 パフォーマンス考慮

- 移行後は実行計画を確認
- インデックスの再設計が必要な場合がある
- 統計情報の収集を忘れずに

### 6.3 データ移行

- DDL変換後にデータ移行が必要
- pg_dump/pg_restore、ora2pg等のツールを活用
- 大量データの場合は分割移行を検討

## 7. 参考情報

### 7.1 関連仕様書

- `specs/select.md`: SELECT文変換ルール
- `specs/insert.md`: INSERT文変換ルール
- `specs/update.md`: UPDATE文変換ルール
- `specs/delete.md`: DELETE文変換ルール
- `specs/schema.md`: スキーマ定義

### 7.2 外部ツール

| ツール | 用途 |
|--------|------|
| ora2pg | Oracle→PostgreSQL移行ツール |
| pgloader | 各種DB→PostgreSQL移行ツール |
| AWS SCT | AWSのスキーマ変換ツール |

---

**バージョン**: 1.0.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト

