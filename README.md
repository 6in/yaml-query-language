# YQL (YAML Query Language)

> **AI-native な人間にも読みやすいクエリ言語**  
> 自然言語とデータベースを橋渡しする次世代データアクセス言語

## YQLとは

YQLは、**SQLをYAML形式で記述し、複数のデータベースを統一的に扱える言語**です。

```yaml
query:
  select:
    - name: c.name
    - total: "SUM(o.amount)"
  from: c: customers
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
  where:
    - "c.status = 'active'"
  order_by:
    - field: total
      direction: DESC
  limit: 10
```

↓ PostgreSQL / MySQL / SQL Server に自動変換

## 🎯 あなたの役割は？

| 役割 | おすすめドキュメント |
|------|---------------------|
| **🔰 初めての方** | [Getting Started](docs/getting-started/README.md) |
| **👨‍💻 エンジニア** | [仕様書](specs/README.md) ・ [アーキテクチャ](docs/architecture/README.md) |
| **👔 PM / PO** | [ビジネス価値](docs/business/README.md) ・ [非エンジニア向け](docs/business/for-non-engineers.md) |
| **📊 経営層** | [ROI・効果](docs/business/roi.md) ・ [導入戦略](docs/business/adoption-strategy.md) |

## ⭐ 核心価値

| 価値 | 説明 |
|------|------|
| 🤖 **AI-Native** | 自然言語 ↔ YQL ↔ SQL の変換に最適化 |
| 🌐 **マルチDB** | PostgreSQL / MySQL / SQL Server / Oracle |
| 📖 **実行可能ドキュメント** | コード = 仕様書 |
| 🔄 **DB移行支援** | Oracle → PostgreSQL 等の移行を支援 |

## 📁 プロジェクト構成

```
yql-specs/
├── specs/              # 📋 YQL仕様書
├── docs/
│   ├── getting-started/  # 🔰 初心者向け
│   ├── architecture/     # 🏗️ 技術設計
│   ├── business/         # 💼 ビジネス向け
│   └── guides/           # 📚 ガイド
├── validation/         # 🧪 検証サンプル
└── old-specs/          # 📜 旧仕様（参考）
```

## 📍 現在の状況

| 機能 | ステータス |
|------|-----------|
| 仕様書 | ✅ 完成 |
| SQL→YQL変換（AI） | ✅ 利用可能 |
| YQL→SQL変換（パーサー） | 🚧 開発中 |
| IDE拡張 | 📝 計画中 |

### 今すぐできること

- ✅ [仕様書](specs/README.md)を読んでYQLを理解する
- ✅ AIを使ってSQL→YQL変換を試す
- ✅ 要件整理ツールとしてYAML形式で要件を書く

## 🔗 クイックリンク

### 仕様書

- [SELECT](specs/select.md) ・ [INSERT](specs/insert.md) ・ [UPDATE](specs/update.md) ・ [DELETE](specs/delete.md) ・ [UPSERT](specs/upsert.md)
- [スキーマ定義](specs/schema.md) ・ [import機能](specs/import.md) ・ [ストアドプロシージャ](specs/procedure.md)

### ガイド

- [クイックスタート](docs/getting-started/quick-start.md)
- [ユースケース](docs/guides/yql-use-cases-overview.md)
- [DB移行ガイド](docs/guides/database-migration-guide.md)
- [競合比較](docs/business/comparison.md)

## 📄 ライセンス

MIT License（予定）

---

**バージョン**: 2.0.0 | **ステータス**: 仕様策定完了、MVP実装準備中

> 💡 **始めてみませんか？**  
> まずは [Getting Started](docs/getting-started/README.md) から始めてみてください。
