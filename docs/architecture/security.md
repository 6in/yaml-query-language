# 🔒 セキュリティ設計

YQLは**多層防御アプローチ**でセキュリティを確保します。

## セキュリティレイヤー

| レイヤー | 対策 | 説明 |
|---------|------|------|
| **1. 構造検証** | YAML DSL構造の検証 | 許可された構造のみ受け入れ |
| **2. 権限チェック** | テーブル・カラムレベルのアクセス制御 | 許可されたリソースのみアクセス可能 |
| **3. SQL生成検証** | SQLインジェクション対策 | パラメータバインディング必須 |
| **4. 実行時制限** | タイムアウト、行数制限 | リソース枯渇を防止 |
| **5. 監査ログ** | 全クエリ記録 | 異常検知、事後分析 |

## セキュリティ設定例

```yaml
security:
  permissions:
    allowed_tables: ["customers", "orders", "products"]
    denied_tables: ["user_passwords", "admin_logs"]
    denied_columns: ["password", "credit_card", "ssn"]
  
  query_limits:
    max_rows: 1000
    max_joins: 5
    timeout_seconds: 30
    forbidden_functions: ["LOAD_FILE", "INTO OUTFILE", "EXEC"]
  
  audit:
    log_all_queries: true
    alert_on_anomaly: true
    retention_days: 90
```

## パラメータバインディング

YQLでは、ユーザー入力は必ずパラメータバインディングを使用します：

```yaml
# ✅ 安全: パラメータバインディング
where:
  - "c.customer_id = #{customer_id}"
  - "c.status IN (${statuses})"

# ❌ 危険: 文字列連結（YQLでは禁止）
where:
  - "c.customer_id = '${user_input}'"  # SQLインジェクションの危険
```

| 記法 | 用途 | 安全性 |
|------|------|--------|
| `#{name}` | 単一値のバインド | ✅ Prepared Statement |
| `${name}` | 配列展開、条件分岐 | ✅ 適切にエスケープ |

## アクセス制御

### テーブルレベル

```yaml
security:
  permissions:
    allowed_tables: ["customers", "orders"]  # ホワイトリスト
    denied_tables: ["admin_users"]           # ブラックリスト
```

### カラムレベル

```yaml
security:
  permissions:
    denied_columns: ["password", "credit_card"]
    # または
    allowed_columns:
      customers: ["id", "name", "email"]  # passwordは除外
```

## 実行時制限

```yaml
security:
  query_limits:
    max_rows: 1000           # 最大取得行数
    max_joins: 5             # 最大JOIN数
    timeout_seconds: 30      # タイムアウト
    max_query_length: 10000  # クエリ文字数制限
```

## 監査ログ

すべてのクエリを記録し、異常を検知します：

```yaml
security:
  audit:
    log_all_queries: true
    log_format: "json"
    alert_on_anomaly: true
    anomaly_rules:
      - "SELECT * FROM"           # 全カラム取得
      - "DELETE FROM .* WHERE 1"  # 全件削除
```

## ベストプラクティス

1. **最小権限の原則**: 必要なテーブル・カラムのみ許可
2. **パラメータバインディング必須**: ユーザー入力は必ずバインド
3. **実行時制限の設定**: タイムアウト、行数制限を適切に設定
4. **監査ログの有効化**: 全クエリを記録、定期的にレビュー
5. **定期的なセキュリティレビュー**: 設定の見直し
