# マクロ定義内のパラメータ記法の比較: `@name` vs `@{name}`

## 比較の目的

マクロ定義内でパラメータを参照する際の記法として、`@name`と`@{name}`のどちらが適切かを比較します。

## 比較

### 1. パラメータ名の境界の明確さ

#### `@name`形式
```yaml
expression: |
  CASE
    WHEN @annual_sales >= 1000000 THEN 'Enterprise'
    WHEN @price * 1.1 > 10000 THEN 'High'
  END
```

**問題点:**
- `@price * 1.1`の場合、`price`パラメータに`* 1.1`が続くのか、`price * 1.1`という1つのパラメータ名なのか、パーサーが判断する必要がある
- パラメータ名の終わりが明確でない場合がある

#### `@{name}`形式
```yaml
expression: |
  CASE
    WHEN @{annual_sales} >= 1000000 THEN 'Enterprise'
    WHEN @{price} * 1.1 > 10000 THEN 'High'
  END
```

**利点:**
- `@{price} * 1.1`の場合、`price`パラメータの終わりが明確（`}`で区切られる）
- パラメータ名の境界が明確
- パーサーの実装が容易

### 2. 複雑な式での使用

#### `@name`形式
```yaml
expression: |
  (@price + @tax) * @discount_rate
```

**問題点:**
- パラメータ名の終わりが明確でない
- `@price + @tax`の場合、`price + tax`という1つのパラメータ名なのか、2つのパラメータなのか、パーサーが判断する必要がある

#### `@{name}`形式
```yaml
expression: |
  (@{price} + @{tax}) * @{discount_rate}
```

**利点:**
- パラメータ名の境界が明確
- `@{price} + @{tax}`は明確に2つのパラメータ
- パーサーの実装が容易

### 3. パラメータ名に特殊文字が含まれる場合

#### `@name`形式
```yaml
expression: |
  @price_with_tax >= 1000
```

**問題点:**
- パラメータ名に特殊文字（例: `price-with-tax`）が含まれる場合、境界が不明確
- アンダースコア以外の文字が含まれる場合、パーサーが混乱する可能性

#### `@{name}`形式
```yaml
expression: |
  @{price-with-tax} >= 1000
  @{price_with_tax} >= 1000
  @{price.with.tax} >= 1000
```

**利点:**
- 波括弧で囲むことで、特殊文字を含むパラメータ名も安全に扱える
- パラメータ名の範囲が明確

### 4. 可読性

#### `@name`形式
```yaml
expression: |
  CASE
    WHEN @annual_sales >= 1000000 THEN 'Enterprise'
    WHEN @annual_sales >= 100000 THEN 'Business'
  END
```

**評価:**
- シンプルで読みやすい
- ただし、パラメータ名の境界が不明確な場合がある

#### `@{name}`形式
```yaml
expression: |
  CASE
    WHEN @{annual_sales} >= 1000000 THEN 'Enterprise'
    WHEN @{annual_sales} >= 100000 THEN 'Business'
  END
```

**評価:**
- 波括弧で囲むことで、パラメータ名が明確に識別できる
- 少し冗長だが、明確性が向上

### 5. パーサーの実装

#### `@name`形式
```python
# パーサーの実装例
def parse_macro_parameter(text):
    # @nameの形式を解析
    # パラメータ名の終わりを判断する必要がある
    # 例: @price * 1.1 → priceパラメータなのか、price * 1.1パラメータなのか
    # 識別子の終わり（空白、演算子、括弧等）を検出する必要がある
```

**問題点:**
- パラメータ名の終わりを判断するロジックが必要
- 複雑な式の場合、誤認識のリスクがある

#### `@{name}`形式
```python
# パーサーの実装例
def parse_macro_parameter(text):
    # @{name}の形式を解析
    # 波括弧で囲まれているので、パラメータ名の範囲が明確
    # 例: @{price} * 1.1 → priceパラメータが明確
    pattern = r'@\{([^}]+)\}'
    return re.findall(pattern, text)
```

**利点:**
- パラメータ名の範囲が明確（`{`から`}`まで）
- 正規表現で簡単に抽出可能
- 実装が容易

### 6. 既存の記法との一貫性

#### 既存のパラメータ記法
- `#{paramName}` - PreparedStatement用（波括弧なし）
- `${paramArray}` - 配列パラメータ（波括弧あり）
- `${paramName}` - 条件分岐用（波括弧あり）

#### `@name`形式
- 波括弧なし
- 既存の`#{name}`と似ているが、用途が異なる

#### `@{name}`形式
- 波括弧あり
- 既存の`${name}`と形式が似ている（用途は異なるが、記法の一貫性がある）

## 結論

### `@{name}`形式を推奨

**理由:**
1. **パラメータ名の境界が明確**: 波括弧で囲むことで、パラメータ名の範囲が明確
2. **パーサーの実装が容易**: 正規表現で簡単に抽出可能
3. **特殊文字に対応**: パラメータ名に特殊文字が含まれる場合も安全に扱える
4. **既存の記法との一貫性**: `${name}`と形式が似ており、記法の一貫性がある
5. **誤認識のリスクが低い**: 複雑な式でも、パラメータ名の境界が明確

**実装例:**
```yaml
column_definition:
  expression: |
    CASE
      WHEN @{annual_sales} >= 1000000 THEN 'Enterprise'
      WHEN @{annual_sales} >= 100000 THEN 'Business'
      WHEN @{annual_sales} >= 10000 THEN 'Professional'
      ELSE 'Starter'
    END
  parameters:
    annual_sales: null
```

**使用例:**
```yaml
segment:
  macro: "customer_segment"
  parameters:
    annual_sales: "SUM(o.amount)"
```

**展開結果:**
```sql
CASE
  WHEN SUM(o.amount) >= 1000000 THEN 'Enterprise'
  WHEN SUM(o.amount) >= 100000 THEN 'Business'
  WHEN SUM(o.amount) >= 10000 THEN 'Professional'
  ELSE 'Starter'
END
```

