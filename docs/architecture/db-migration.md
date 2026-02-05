# 🔄 DB移行支援

YQLを中間形式として、データベース間の移行を支援します。

## 移行フロー

```
┌─────────────────────────────────────────────────────────────┐
│                    DB移行フロー                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [移行元 SQL]  (例: Oracle, SQL Server)                     │
│       │                                                     │
│       ▼ (AI変換)                                            │
│  [YQL]  ←── 検証・レビュー ←── スキーマ定義                  │
│       │                                                     │
│       ▼ (パーサー/ジェネレーター)                            │
│  [移行先 SQL]  (例: PostgreSQL)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 対応移行パターン

| 移行元 | 移行先 | 有効性 | 備考 |
|--------|--------|--------|------|
| Oracle | PostgreSQL | ⭐⭐⭐⭐ | ora2pg相当の機能 |
| SQL Server | PostgreSQL | ⭐⭐⭐⭐⭐ | 成熟ツールがないため特に有効 |
| MySQL | PostgreSQL | ⭐⭐⭐ | pgloader等の既存ツールあり |

## YQLを使う優位性

### 従来の移行方法

```
Oracle SQL → 手動変換 → PostgreSQL SQL
           ↑
      専門知識が必要
      時間がかかる
      ミスが発生しやすい
```

### YQLを使った移行

```
Oracle SQL → AI変換 → YQL → 自動生成 → PostgreSQL SQL
                      ↑
                 検証・レビュー
                 スキーマ情報付与
                 一貫性の確保
```

## 移行手順

### Step 1: 移行元SQLをYQLに変換

```bash
# AIを使って変換（specs/select.md を参照させる）
# 入力: Oracle SQL
SELECT 
  customer_id,
  customer_name,
  TO_CHAR(created_at, 'YYYY-MM-DD') as created_date
FROM customers
WHERE ROWNUM <= 10;

# 出力: YQL
query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.customer_name
    - created_date: "TO_CHAR(c.created_at, 'YYYY-MM-DD')"
  from: c: customers
  limit: 10
```

### Step 2: YQLを検証・レビュー

- 構文の正確性を確認
- スキーマ定義との整合性を確認
- ビジネスロジックの正確性を確認

### Step 3: 移行先SQLを生成

```sql
-- PostgreSQL
SELECT 
  c.customer_id AS customer_id,
  c.customer_name AS customer_name,
  TO_CHAR(c.created_at, 'YYYY-MM-DD') AS created_date
FROM customers c
LIMIT 10;
```

## 関数マッピング例

### Oracle → PostgreSQL

| Oracle | YQL | PostgreSQL |
|--------|-----|------------|
| `SYSDATE` | `CURRENT_TIMESTAMP` | `CURRENT_TIMESTAMP` |
| `NVL(a, b)` | `COALESCE(a, b)` | `COALESCE(a, b)` |
| `ROWNUM <= n` | `limit: n` | `LIMIT n` |
| `TO_DATE(s, fmt)` | `TO_DATE(s, fmt)` | `TO_DATE(s, fmt)` |
| `DECODE(...)` | `CASE WHEN ...` | `CASE WHEN ...` |

### SQL Server → PostgreSQL

| SQL Server | YQL | PostgreSQL |
|------------|-----|------------|
| `GETDATE()` | `CURRENT_TIMESTAMP` | `CURRENT_TIMESTAMP` |
| `ISNULL(a, b)` | `COALESCE(a, b)` | `COALESCE(a, b)` |
| `TOP n` | `limit: n` | `LIMIT n` |
| `CONVERT(type, val)` | 型変換式 | `CAST(val AS type)` |
| `DATEADD(...)` | 日付加算式 | `date + INTERVAL '...'` |

## ストアドプロシージャの移行

ストアドプロシージャは [specs/procedure.md](../specs/procedure.md) を使って解析・ドキュメント化できます：

```yaml
procedures:
  - name: calculate_monthly_sales
    label: 月次売上計算
    description: 指定月の売上を集計し、レポートテーブルに格納
    
    python_sample: |
      def calculate_monthly_sales(target_month):
          """月次売上を計算してレポートに格納"""
          # 売上データを取得
          sales = db.query("""
              SELECT customer_id, SUM(amount) as total
              FROM orders
              WHERE order_month = :month
              GROUP BY customer_id
          """, month=target_month)
          
          # レポートテーブルに格納
          for row in sales:
              db.execute("""
                  INSERT INTO monthly_report (customer_id, total, month)
                  VALUES (:cust, :total, :month)
              """, cust=row.customer_id, total=row.total, month=target_month)
```

## 詳細ガイド

→ [データベース移行ガイド](../guides/database-migration-guide.md)

