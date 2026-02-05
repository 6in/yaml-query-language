---
layout: default
title: Macro Parameter Notation Proposal
---

# マクロ定義内のパラメータ記法の提案

## 問題点

現在のマクロ定義では、パラメータの参照に`#{name}`を使用していますが、これは既存のパラメータバインディング（PreparedStatement用の`#{paramName}`）と混同される可能性があります。

### 既存のパラメータ記法

- **`#{paramName}`**: PreparedStatement用のパラメータバインディング（実行時に`?`に変換）
- **`${paramArray}`**: 配列パラメータの展開（IN句など）
- **`${paramName}`**: 条件分岐用パラメータ（テンプレートエンジン用）

### マクロ定義内のパラメータ

- **`#{name}`**: マクロ呼び出し時に渡された式を**埋め込む**（文字列置換のような動作）
- これは実行時のパラメータバインディングとは異なる

## 提案する記法の候補

### 1. `@name`形式（推奨）

**例:**
```yaml
column_definition:
  expression: |
    CASE
      WHEN @annual_sales >= 1000000 THEN 'Enterprise'
      WHEN @annual_sales >= 100000 THEN 'Business'
      ELSE 'Starter'
    END
  parameters:
    annual_sales: null
```

**利点:**
- ✅ シンプルで分かりやすい
- ✅ 既存の記法（`#{name}`, `${name}`）と明確に区別できる
- ✅ `@`は「参照」の意味で直感的
- ✅ SQLの構文と混同されない

**欠点:**
- ⚠️ 一部のSQL方言で`@`が変数記号として使われる（PostgreSQL等）
  - ただし、マクロ定義内では展開されるため問題なし

### 2. `{{name}}`形式

**例:**
```yaml
column_definition:
  expression: |
    CASE
      WHEN {{annual_sales}} >= 1000000 THEN 'Enterprise'
      WHEN {{annual_sales}} >= 100000 THEN 'Business'
      ELSE 'Starter'
    END
```

**利点:**
- ✅ テンプレートエンジン風で明確
- ✅ 既存の記法と明確に区別できる

**欠点:**
- ⚠️ 少し冗長
- ⚠️ 波括弧が2つで入力がやや面倒

### 3. `$name`形式

**例:**
```yaml
column_definition:
  expression: |
    CASE
      WHEN $annual_sales >= 1000000 THEN 'Enterprise'
      WHEN $annual_sales >= 100000 THEN 'Business'
      ELSE 'Starter'
    END
```

**利点:**
- ✅ シンプル
- ✅ シェルスクリプト風で直感的

**欠点:**
- ⚠️ SQLの構文と混同される可能性（一部のDBで`$`が使われる）
- ⚠️ 既存の`${name}`と混同される可能性

### 4. `{name}`形式

**例:**
```yaml
column_definition:
  expression: |
    CASE
      WHEN {annual_sales} >= 1000000 THEN 'Enterprise'
      WHEN {annual_sales} >= 100000 THEN 'Business'
      ELSE 'Starter'
    END
```

**利点:**
- ✅ シンプル
- ✅ 波括弧で明確

**欠点:**
- ⚠️ YAMLの構文と混同される可能性
- ⚠️ SQLの構文と混同される可能性

### 5. `%name%`形式

**例:**
```yaml
column_definition:
  expression: |
    CASE
      WHEN %annual_sales% >= 1000000 THEN 'Enterprise'
      WHEN %annual_sales% >= 100000 THEN 'Business'
      ELSE 'Starter'
    END
```

**利点:**
- ✅ 環境変数風で明確
- ✅ 既存の記法と明確に区別できる

**欠点:**
- ⚠️ 少し特殊な記法

## 推奨: `@name`形式

**理由:**
1. **明確な区別**: 既存の`#{name}`（PreparedStatement用）と明確に区別できる
2. **シンプル**: 記号が1つで入力しやすい
3. **直感的**: `@`は「参照」の意味で理解しやすい
4. **実装が容易**: パーサーで識別しやすい

## 実装例

### マクロ定義
```yaml
name: "customer_segment"
column_definition:
  expression: |
    CASE
      WHEN @annual_sales >= 1000000 THEN 'Enterprise'
      WHEN @annual_sales >= 100000 THEN 'Business'
      WHEN @annual_sales >= 10000 THEN 'Professional'
      ELSE 'Starter'
    END
  parameters:
    annual_sales: null
```

### マクロ呼び出し
```yaml
segment:
  macro: "customer_segment"
  parameters:
    annual_sales: "SUM(o.amount)"
```

### 展開結果
```sql
CASE
  WHEN SUM(o.amount) >= 1000000 THEN 'Enterprise'
  WHEN SUM(o.amount) >= 100000 THEN 'Business'
  WHEN SUM(o.amount) >= 10000 THEN 'Professional'
  ELSE 'Starter'
END
```

## まとめ

**推奨記法: `@name`**

- 既存のパラメータ記法（`#{name}`, `${name}`）と明確に区別できる
- シンプルで分かりやすい
- 実装が容易

