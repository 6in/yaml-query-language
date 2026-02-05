---
layout: default
title: Multi Db
---

# 🌍 マルチデータベース対応

YQLは同一の記述から複数のSQL方言を生成します。

## 対応データベース

| データベース | SELECT | INSERT | UPDATE | DELETE | UPSERT |
|-------------|--------|--------|--------|--------|--------|
| PostgreSQL | ✅ | ✅ | ✅ | ✅ | ✅ |
| MySQL | ✅ | ✅ | ✅ | ✅ | ✅ |
| SQL Server | ✅ | ✅ | ✅ | ✅ | ✅ |
| Oracle | ✅ | ✅ | ✅ | ✅ | ✅ |

## SQL方言の抽象化

### LIMIT / OFFSET

```yaml
# YQL (共通)
query:
  select:
    - name: u.name
  from: u: users
  limit: 10
  offset: 20
```

| データベース | 生成SQL |
|-------------|---------|
| **PostgreSQL** | `SELECT u.name AS name FROM users u LIMIT 10 OFFSET 20` |
| **MySQL** | `SELECT u.name AS name FROM users u LIMIT 20, 10` |
| **SQL Server** | `SELECT u.name AS name FROM users u ORDER BY u.name OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY` |

### 文字列検索（大文字小文字無視）

```yaml
# YQL (共通)
where:
  - "u.name ILIKE '%john%'"
```

| データベース | 生成SQL |
|-------------|---------|
| **PostgreSQL** | `WHERE u.name ILIKE '%john%'` |
| **MySQL** | `WHERE u.name COLLATE utf8_general_ci LIKE '%john%'` |
| **SQL Server** | `WHERE u.name LIKE '%john%'` (照合順序依存) |

### 日付関数

```yaml
# YQL (共通)
where:
  - "order_date >= DATE('now', '-1 month')"
```

| データベース | 生成SQL |
|-------------|---------|
| **PostgreSQL** | `WHERE order_date >= CURRENT_DATE - INTERVAL '1 month'` |
| **MySQL** | `WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)` |
| **SQL Server** | `WHERE order_date >= DATEADD(month, -1, GETDATE())` |

### UPSERT

```yaml
# YQL (共通)
upsert:
  table: products
  conflict_target: [product_id]
  values:
    product_id: "#{product_id}"
    name: "#{name}"
    price: "#{price}"
  on_conflict:
    update:
      - name
      - price
```

| データベース | 生成SQL |
|-------------|---------|
| **PostgreSQL** | `INSERT ... ON CONFLICT (product_id) DO UPDATE SET ...` |
| **MySQL** | `INSERT ... ON DUPLICATE KEY UPDATE ...` |
| **SQL Server** | `MERGE ... WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...` |

## 関数マッピング

### 文字列関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|------------|-------|------------|
| `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` | `CONCAT(a, b)` |
| `LENGTH(s)` | `LENGTH(s)` | `CHAR_LENGTH(s)` | `LEN(s)` |
| `SUBSTRING(s, start, len)` | `SUBSTRING(...)` | `SUBSTRING(...)` | `SUBSTRING(...)` |

### 日付関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|------------|-------|------------|
| `CURRENT_DATE` | `CURRENT_DATE` | `CURDATE()` | `CAST(GETDATE() AS DATE)` |
| `CURRENT_TIMESTAMP` | `CURRENT_TIMESTAMP` | `NOW()` | `GETDATE()` |
| `DATE_ADD(d, n, unit)` | `d + INTERVAL 'n unit'` | `DATE_ADD(d, INTERVAL n unit)` | `DATEADD(unit, n, d)` |

### 集計関数

| YQL | PostgreSQL | MySQL | SQL Server |
|-----|------------|-------|------------|
| `COUNT(*)` | `COUNT(*)` | `COUNT(*)` | `COUNT(*)` |
| `STRING_AGG(col, ',')` | `STRING_AGG(col, ',')` | `GROUP_CONCAT(col)` | `STRING_AGG(col, ',')` |

## 詳細仕様

各DMLの詳細な方言対応は仕様書を参照してください：

- [specs/select.md](../specs/select.md) - SELECT文
- [specs/insert.md](../specs/insert.md) - INSERT文
- [specs/update.md](../specs/update.md) - UPDATE文
- [specs/delete.md](../specs/delete.md) - DELETE文
- [specs/upsert.md](../specs/upsert.md) - UPSERT文
