# stereotypeアプローチの批判的検討

## 1. 問題提起の再確認

**元の問題**: LIMIT/OFFSETを毎回記述するのが面倒

**stereotypeアプローチ**: 結果タイプを明示して自動付与

しかし、本当にこれが最適解か？もっと深く考える必要がある。

## 2. YQLの設計思想との整合性

### 2.1 YQLの設計原則

1. **明示性**: コードが意図を明確に表現
2. **構造化**: YAML形式で階層的に整理
3. **一貫性**: エイリアス必須、各句が明確に分離
4. **DB抽象化**: 複数のDB方言を統一インターフェースで操作
5. **AI-native**: AIが理解しやすい形式

### 2.2 stereotypeアプローチの問題点

#### 問題1: 明示性の欠如

```yaml
query:
  stereotype: paging
  # LIMIT/OFFSETが自動的に付与される（どこに？）
```

**問題**: LIMIT/OFFSETが「自動的に」付与されるため、YQLを見ただけでは実際のSQLがどうなるか分からない。

**既存アプローチとの比較**:
```yaml
query:
  limit: "${per_page:20}"
  offset: "$((${page:1} - 1) * ${per_page:20})"
```

**既存アプローチの方が明示的**: LIMIT/OFFSETがどこに付与されるかが明確。

#### 問題2: 分類の曖昧さ

`paging`, `single`, `limit`, `stream`の分類は本当に適切か？

- **`paging` vs `limit`**: どちらもLIMITを使う。違いはOFFSETの有無だけ？
- **`single` vs `limit`**: `limit: 1`と`stereotype: single`は同じ結果。なぜ別の概念？
- **`stream`**: LIMIT/OFFSETなしは「デフォルト」では？わざわざstereotypeが必要？

**疑問**: これらは本当に「結果タイプ」なのか？それとも単に「LIMIT/OFFSETの使い方」なのか？

#### 問題3: 実装の複雑さ

パーサーがstereotypeを理解してLIMIT/OFFSETを自動付与するのは、既存の仕様と比べて複雑。

**既存の仕様**:
- `limit`と`offset`をそのままSQLに変換するだけ

**stereotypeアプローチ**:
- stereotypeを解釈
- パラメータを確認
- LIMIT/OFFSETを計算
- SQLに変換

**コスト**: パーサーの実装が複雑になる。既存の仕様で十分では？

#### 問題4: デフォルト値の問題

```yaml
query:
  stereotype: paging  # デフォルトでpage=1, per_page=20
```

**問題**: パラメータ名が固定される（`page`, `per_page`）。カスタマイズできない。

**構文案B**:
```yaml
query:
  stereotype: paging
  pagination:
    page: "#{current_page:1}"
    per_page: "#{items_per_page:20}"
```

**問題**: これなら既存の`limit`/`offset`と大差ない。stereotypeの価値は？

#### 問題5: AI理解性の疑問

stereotypeは本当にAIが理解しやすいのか？

**stereotypeアプローチ**:
```yaml
stereotype: paging
```

**既存アプローチ**:
```yaml
limit: "${per_page:20}"
offset: "$((${page:1} - 1) * ${per_page:20})"
```

**疑問**: AIにとって、どちらが理解しやすいか？

- `stereotype: paging`は抽象的（「ページング」という概念）
- `limit`/`offset`は具体的（実際のSQLに近い）

**仮説**: 既存アプローチの方が、AIがSQLに変換しやすいのでは？

## 3. 代替アプローチの検討

### 3.1 アプローチA: 既存仕様の改善（推奨）

既存の`limit`/`offset`を改善する。

#### 改善案1: 計算式の簡略化

```yaml
query:
  limit: "#{per_page:20}"
  offset: "#{page:1}"  # 自動的に (page - 1) * per_page を計算
```

**問題**: これでも`offset`の計算式は必要。

#### 改善案2: ヘルパー構文

```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  # 内部的に limit と offset に展開される
```

**メリット**:
- 明示的（`pagination`セクションがある）
- 既存の`limit`/`offset`と共存可能
- パラメータ名をカスタマイズ可能
- 実装がシンプル（`pagination`を`limit`/`offset`に展開するだけ）

**デメリット**:
- `stereotype`のような「結果タイプ」の概念はない

### 3.2 アプローチB: コメント/メタデータ

```yaml
query:
  # stereotype: paging
  limit: "${per_page:20}"
  offset: "$((${page:1} - 1) * ${per_page:20})"
```

**メリット**:
- 既存仕様を変更しない
- コメントとして意図を記述可能
- AIが理解しやすい（コメントを参照）

**デメリット**:
- コメントは実行時には無視される
- バリデーションに使えない

### 3.3 アプローチC: 別ファイルでの定義

ページング用のクエリは、別のファイル（例: `queries/paginated/`）に配置。

**メリット**:
- ファイル名で意図が明確
- 既存仕様を変更しない

**デメリット**:
- ファイル構造に依存
- 柔軟性が低い

## 4. 本当に必要なのは何か？

### 4.1 ユーザーの真のニーズ

1. **記述の簡略化**: LIMIT/OFFSETの記述を簡単にしたい
2. **意図の明確化**: このSELECT文がページング用であることを明示したい

### 4.2 各アプローチの評価

| アプローチ | 記述の簡略化 | 意図の明確化 | 実装の複雑さ | 既存仕様との整合性 |
|----------|------------|------------|------------|------------------|
| **stereotype** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| **pagination構文** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **既存仕様** | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **コメント** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

### 4.3 推奨アプローチ: pagination構文（stereotypeなし）

```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  select:
    - id: id
    - name: name
  from: customers
  order_by:
    - field: created_at
      direction: DESC
  # 内部的に以下に展開される:
  # limit: "#{per_page:20}"
  # offset: "$((${page:1} - 1) * ${per_page:20})"
```

**メリット**:
1. **明示的**: `pagination`セクションがあることで意図が明確
2. **簡潔**: `limit`/`offset`の計算式を書かなくて良い
3. **柔軟**: パラメータ名をカスタマイズ可能
4. **実装がシンプル**: `pagination`を`limit`/`offset`に展開するだけ
5. **既存仕様との整合性**: 既存の`limit`/`offset`と共存可能

**デメリット**:
- `stereotype`のような「結果タイプ」の概念はない
- ただし、`pagination`セクションがあることで、意図は十分に明確

## 5. stereotypeアプローチの再評価

### 5.1 stereotypeの価値

**stereotypeの価値**: 「このSELECT文が何を返すのか？」を明示

**しかし**:
- `pagination`セクションがあれば、意図は十分に明確
- `single`は`limit: 1`で十分
- `limit`は既存の`limit`で十分
- `stream`はLIMIT/OFFSETなしで十分（デフォルト）

**結論**: stereotypeは過剰設計の可能性がある。

### 5.2 もしstereotypeを採用する場合

以下の条件を満たす必要がある：

1. **明確な分類**: 各stereotypeが明確に区別できる
2. **実装の簡潔さ**: パーサーの実装が複雑にならない
3. **既存仕様との整合性**: 既存の`limit`/`offset`と矛盾しない
4. **拡張性**: 将来的に新しいstereotypeを追加しやすい

**現状の問題**:
- `paging`, `single`, `limit`, `stream`の分類が曖昧
- 実装が複雑になる可能性
- 既存仕様との重複が多い

## 6. 重要な発見: pagination構文の包括性

### 6.1 pagination構文で全てのケースをカバーできる

実は、`pagination`構文だけで、stereotypeが想定していた全てのケースを表現できる：

#### ケース1: ページング（本来の用途）
```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
```
→ `LIMIT 20 OFFSET 0` (page=1の場合) または `LIMIT 20 OFFSET 20` (page=2の場合)

#### ケース2: 単一レコード取得（single相当）
```yaml
query:
  pagination:
    page: 1
    per_page: 1
```
→ `LIMIT 1 OFFSET 0` = `LIMIT 1`（実用的には問題なし）

#### ケース3: 上限付き取得（limit相当）
```yaml
query:
  pagination:
    page: 1
    per_page: "#{max_rows:100}"
```
→ `LIMIT 100 OFFSET 0` = `LIMIT 100`（実用的には問題なし）

#### ケース4: ストリーミング（stream相当）
```yaml
query:
  # paginationなし
```
→ LIMIT/OFFSETなし（デフォルト）

### 6.2 結論: stereotypeは不要

**重要な発見**: `pagination`構文だけで、stereotypeが想定していた全てのケースを表現できる。

**stereotypeの必要性**: 
- ❌ `pagination`構文で全てカバーできる
- ❌ 分類が曖昧（`paging` vs `limit`の違いはOFFSETの有無だけ）
- ❌ 実装が複雑になる
- ❌ 既存仕様との重複が多い

**推奨アプローチ**: `pagination`構文のみ

```yaml
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  # ...
```

**理由**:
1. **包括性**: 全てのケースをカバーできる
2. **明示性**: `pagination`セクションがあることで意図が明確
3. **実装の簡潔さ**: `pagination`を`limit`/`offset`に展開するだけ
4. **既存仕様との整合性**: 既存の`limit`/`offset`と共存可能
5. **柔軟性**: パラメータ名をカスタマイズ可能

### 6.3 実用的な考慮事項

#### 6.3.1 `single`ケースの最適化

`pagination: { page: 1, per_page: 1 }`は`LIMIT 1 OFFSET 0`を生成するが、`OFFSET 0`は不要。

**解決策1**: パーサーが最適化
- `page: 1`かつ`per_page: 1`の場合、`OFFSET 0`を省略して`LIMIT 1`のみ生成

**解決策2**: 既存の`limit`を使用
- `single`ケースは`limit: 1`を使用（`pagination`を使わない）

**推奨**: 解決策2（既存の`limit`を使用）
- シンプルで明確
- `pagination`はページング専用として使う

#### 6.3.2 `limit`ケースの扱い

`pagination: { page: 1, per_page: 100 }`は`LIMIT 100 OFFSET 0`を生成するが、`OFFSET 0`は不要。

**解決策**: 既存の`limit`を使用
- 上限付き取得は`limit: "#{max_rows:100}"`を使用（`pagination`を使わない）

**推奨**: 既存の`limit`を使用
- シンプルで明確
- `pagination`はページング専用として使う

### 6.4 最終的な推奨アプローチ

**`pagination`構文はページング専用として使用**：

```yaml
# ページング用
query:
  pagination:
    page: "#{page:1}"
    per_page: "#{per_page:20}"
  # ...

# 単一レコード取得
query:
  limit: 1
  # ...

# 上限付き取得
query:
  limit: "#{max_rows:100}"
  # ...

# ストリーミング（全件取得）
query:
  # limit/offsetなし
  # ...
```

**理由**:
1. **明確性**: 各構文の用途が明確
2. **既存仕様の活用**: `limit`は既に存在する
3. **実装の簡潔さ**: `pagination`を`limit`/`offset`に展開するだけ
4. **stereotype不要**: `pagination`構文だけでページングをカバー、`limit`でその他をカバー

### 6.2 stereotypeアプローチの採用条件

stereotypeを採用する場合は、以下を明確にする必要がある：

1. **分類の明確化**: 各stereotypeが本当に必要か？重複はないか？
2. **実装方針**: パーサーの実装が複雑にならないか？
3. **既存仕様との関係**: 既存の`limit`/`offset`とどう共存するか？
4. **拡張性**: 将来的に新しいstereotypeを追加する際のルール

### 6.3 次のステップ

1. **`pagination`構文の詳細仕様を作成**
2. **stereotypeアプローチの再検討**（分類の明確化、実装方針の検討）
3. **両アプローチの比較検討**（実際の使用例での比較）

