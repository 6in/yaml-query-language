# YQL ストアドプロシージャ/関数 定義仕様書

## 1. 概要

このドキュメントは、ストアドプロシージャおよび関数をYQL形式で定義し、**AI解析**を支援するための仕様を定義します。

### 1.1 目的

| 目的 | 説明 |
|------|------|
| **AI解析支援** | AIがストアドプロシージャのロジックを正確に理解できるようにする |
| **ドキュメント化** | 人間が読みやすい形式で仕様を記述 |
| **移行計画** | DB移行時に何を移行すべきか把握 |
| **依存関係可視化** | テーブル、関数、外部リソースの依存関係を明確化 |

### 1.2 位置づけ

**重要:** この仕様は**解析専用**です。

```
┌─────────────────────────────────────────────────────────────┐
│                    位置づけ                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [この仕様でできること]                                      │
│    ✅ ストアドプロシージャのメタデータ定義                   │
│    ✅ Pythonサンプルコードによるロジック説明                 │
│    ✅ 依存関係の可視化                                       │
│    ✅ AI解析・レビュー・移行判断の支援                       │
│                                                             │
│  [この仕様でできないこと]                                    │
│    ❌ ストアドプロシージャの実行                             │
│    ❌ DB固有コードの自動生成                                 │
│    ❌ Pythonコードの実行                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Pythonサンプルコードの役割

Pythonサンプルコードは**擬似コード**として使用します：

| 観点 | 説明 |
|------|------|
| **実行可能性** | 実行を想定していない（擬似コード） |
| **目的** | ロジックをAI/人間が理解しやすい形式で表現 |
| **DB操作** | `db.query()`, `db.execute()` で抽象化 |
| **ファイル操作** | `file.read()`, `file.write()` で抽象化 |

### 1.4 対応データベース

- Oracle (PL/SQL)
- PostgreSQL (PL/pgSQL)
- MySQL (SQL/PSM)
- SQL Server (T-SQL)

---

## 2. プロシージャ定義

### 2.1 基本構造

```yaml
procedures:
  procedure_name:
    label: "日本語名"
    description: |
      プロシージャの詳細説明。
      複数行で記述可能。
    
    # パラメータ定義
    parameters:
      - name: param1
        type: integer
        direction: IN
        label: "パラメータ1"
        description: "パラメータの説明"
      - name: param2
        type: varchar(100)
        direction: OUT
        label: "パラメータ2"
    
    # 戻り値（プロシージャは通常void）
    returns:
      type: void
    
    # 依存関係
    dependencies:
      tables:
        - table_name1
        - table_name2
      views:
        - view_name1
      procedures:
        - other_procedure
      functions:
        - helper_function
      files:
        - "/path/to/input.csv"
        - "/path/to/output.log"
      external_services:
        - "HTTP API: https://api.example.com"
    
    # セキュリティ
    security:
      definer: schema_owner
      sql_security: DEFINER  # DEFINER | INVOKER
    
    # Pythonサンプルコード（ロジック説明用）
    python_sample: |
      def procedure_name(param1: int) -> str:
          """
          プロシージャの説明
          
          Args:
              param1: パラメータの説明
          
          Returns:
              OUT パラメータの値
          """
          # ロジックをここに記述
          ...
    
    # 元のDB固有コード（参考用、オプション）
    original_code:
      oracle: |
        CREATE PROCEDURE procedure_name(...)
        ...
    
    # メタ情報
    metadata:
      created_by: "developer"
      created_at: "2024-01-01"
      modified_at: "2024-12-01"
      version: "1.0.0"
      tags:
        - "batch"
        - "monthly"
```

### 2.2 パラメータ方向

| direction | 説明 | 例 |
|-----------|------|-----|
| `IN` | 入力パラメータ | 検索条件 |
| `OUT` | 出力パラメータ | 処理結果 |
| `INOUT` | 入出力パラメータ | 更新対象 |

### 2.3 データ型

`specs/schema.md` で定義されたデータ型を使用します。

---

## 3. 関数定義

### 3.1 基本構造

```yaml
functions:
  function_name:
    label: "日本語名"
    description: "関数の説明"
    
    # パラメータ定義
    parameters:
      - name: param1
        type: integer
        direction: IN
        label: "パラメータ1"
    
    # 戻り値（関数は必須）
    returns:
      type: decimal(10,2)
      label: "戻り値"
      description: "戻り値の説明"
    
    # 関数の特性
    deterministic: true  # 同じ入力で同じ出力を返すか
    side_effects: false  # 副作用があるか
    
    # 依存関係
    dependencies:
      tables:
        - table_name1
      functions:
        - helper_function
    
    # Pythonサンプルコード
    python_sample: |
      def function_name(param1: int) -> Decimal:
          """関数の説明"""
          ...
```

### 3.2 プロシージャと関数の違い

| 観点 | プロシージャ | 関数 |
|------|-------------|------|
| 戻り値 | OUT パラメータ | RETURNS |
| SQL内での使用 | ❌ | ✅ |
| 副作用 | 可能 | 推奨されない |
| deterministic | - | 指定可能 |

### 3.3 パイプライン関数（テーブル関数）

**DB固有構文:**
```sql
-- Oracle PL/SQL
CREATE TYPE t_customer_row AS OBJECT (
  customer_id NUMBER,
  name VARCHAR2(100)
);
CREATE TYPE t_customer_table AS TABLE OF t_customer_row;

CREATE FUNCTION get_active_customers RETURN t_customer_table PIPELINED IS
BEGIN
  FOR rec IN (SELECT customer_id, name FROM customers WHERE status = 'active') LOOP
    PIPE ROW(t_customer_row(rec.customer_id, rec.name));
  END LOOP;
  RETURN;
END;

-- 使用例
SELECT * FROM TABLE(get_active_customers());

-- SQL Server T-SQL（テーブル値関数）
CREATE FUNCTION get_active_customers()
RETURNS @result TABLE (
  customer_id INT,
  name VARCHAR(100)
)
AS
BEGIN
  INSERT INTO @result
  SELECT customer_id, name FROM customers WHERE status = 'active';
  RETURN;
END;

-- 使用例
SELECT * FROM get_active_customers();

-- PostgreSQL PL/pgSQL（SETOF）
CREATE FUNCTION get_active_customers()
RETURNS SETOF customers AS $$
BEGIN
  RETURN QUERY SELECT * FROM customers WHERE status = 'active';
END;
$$ LANGUAGE plpgsql;

-- 使用例
SELECT * FROM get_active_customers();
```

**Pythonサンプルコード:**
```python
from typing import Iterator

@dataclass
class CustomerRow:
    customer_id: int
    name: str

def get_active_customers() -> Iterator[CustomerRow]:
    """
    パイプライン関数の例（ジェネレータで表現）
    
    テーブル関数として使用可能な関数。
    結果セットを1行ずつ返す。
    
    Yields:
        CustomerRow: アクティブな顧客レコード
    """
    for rec in db.cursor("""
        SELECT customer_id, name FROM customers WHERE status = 'active'
    """):
        yield CustomerRow(customer_id=rec.customer_id, name=rec.name)


# 使用例
for customer in get_active_customers():
    log.info(f"Customer: {customer.name}")
```

**YQL定義:**
```yaml
functions:
  get_active_customers:
    label: "アクティブ顧客取得"
    description: "アクティブな顧客の一覧を返すテーブル関数"
    parameters: []
    returns:
      type: table
      columns:
        - name: customer_id
          type: integer
        - name: name
          type: varchar(100)
    table_function: true  # テーブル関数であることを示す
    deterministic: false
    dependencies:
      tables:
        - customers
```

---

## 4. パッケージ定義（Oracle固有）

### 4.1 基本構造

Oracleパッケージは、関連するプロシージャ、関数、変数をグループ化する機能です。他のDBには直接対応する機能がないため、移行時は個別のプロシージャ/関数に分解します。

```yaml
packages:
  order_management:
    label: "注文管理パッケージ"
    description: |
      注文に関連するプロシージャと関数をまとめたパッケージ。
      移行時は個別のプロシージャ/関数に分解する。
    
    # パッケージ変数（グローバル変数）
    variables:
      - name: g_default_tax_rate
        type: decimal(5,2)
        initial_value: 0.1
        scope: session  # session | global
        label: "デフォルト税率"
      - name: g_max_order_items
        type: integer
        initial_value: 100
        scope: session
        label: "最大注文明細数"
    
    # パッケージ定数
    constants:
      - name: c_version
        type: varchar(10)
        value: "1.0.0"
        label: "バージョン"
    
    # 含まれるプロシージャ
    procedures:
      - calculate_order_total
      - update_order_status
      - process_order_cancellation
    
    # 含まれる関数
    functions:
      - get_order_count
      - is_order_valid
      - get_customer_discount_rate
    
    # 初期化処理（パッケージ初期化ブロック）
    initialization: |
      パッケージが最初にアクセスされた時に実行される初期化処理。
      セッション変数の初期化などを行う。
    
    # 依存関係
    dependencies:
      tables:
        - orders
        - order_items
        - customers
      packages:
        - customer_management
    
    # 移行時の注意
    migration_notes: |
      - パッケージ変数はアプリケーション層で管理する（セッションスコープ）
      - 初期化処理はアプリケーション起動時またはセッション開始時に実行
      - プロシージャ/関数は個別に移行し、スキーマまたはモジュールで整理
      - パッケージ間の依存関係に注意
    
    # Pythonサンプルコード（パッケージ全体の構造）
    python_sample: |
      """
      注文管理モジュール
      
      Oracleパッケージ order_management の移行先。
      パッケージ変数はモジュールレベル変数またはクラス変数として管理。
      """
      from decimal import Decimal
      from typing import Optional
      
      # パッケージ定数
      VERSION = "1.0.0"
      
      # パッケージ変数（セッションスコープ → クラスで管理）
      class OrderManagementContext:
          """注文管理コンテキスト（セッションごとに生成）"""
          def __init__(self):
              self.default_tax_rate = Decimal("0.1")
              self.max_order_items = 100
          
          def initialize(self):
              """初期化処理（パッケージ初期化ブロック相当）"""
              # 必要な初期化処理をここに記述
              pass
      
      # プロシージャ
      def calculate_order_total(ctx: OrderManagementContext, order_id: int) -> Decimal:
          """注文合計計算"""
          ...
      
      def update_order_status(ctx: OrderManagementContext, order_id: int, status: str) -> None:
          """注文ステータス更新"""
          ...
      
      # 関数
      def get_order_count(ctx: OrderManagementContext, customer_id: int) -> int:
          """注文件数取得"""
          ...
      
      def is_order_valid(ctx: OrderManagementContext, order_id: int) -> bool:
          """注文有効性チェック"""
          ...
    
    original_code:
      oracle: |
        CREATE OR REPLACE PACKAGE order_management AS
          -- 定数
          c_version CONSTANT VARCHAR2(10) := '1.0.0';
          
          -- 変数
          g_default_tax_rate NUMBER(5,2) := 0.1;
          g_max_order_items INTEGER := 100;
          
          -- プロシージャ
          PROCEDURE calculate_order_total(p_order_id IN NUMBER, p_total OUT NUMBER);
          PROCEDURE update_order_status(p_order_id IN NUMBER, p_status IN VARCHAR2);
          
          -- 関数
          FUNCTION get_order_count(p_customer_id IN NUMBER) RETURN NUMBER;
          FUNCTION is_order_valid(p_order_id IN NUMBER) RETURN BOOLEAN;
        END order_management;
```

### 4.2 移行時の分解方法

**分解パターン:**

| パッケージ要素 | 移行先 | 説明 |
|---------------|--------|------|
| パッケージ変数 | アプリケーション層 | セッションスコープのクラス/オブジェクト |
| パッケージ定数 | モジュール定数 | Pythonのモジュールレベル定数 |
| プロシージャ | 個別プロシージャ | スキーマで整理 |
| 関数 | 個別関数 | スキーマで整理 |
| 初期化ブロック | アプリケーション初期化 | 起動時/セッション開始時に実行 |

**分解例:**
```
Oracle:
  PACKAGE order_management
    ├── g_default_tax_rate (変数)
    ├── calculate_order_total (プロシージャ)
    └── get_order_count (関数)

PostgreSQL移行後:
  Schema: order_mgmt
    ├── calculate_order_total (プロシージャ)
    └── get_order_count (関数)
  
  アプリケーション層:
    └── OrderManagementContext (セッション変数管理)
```

---

## 5. Pythonサンプルコードの記述ルール

### 4.1 基本構造

```python
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Iterator
from dataclasses import dataclass

# 結果セットの型定義（必要に応じて）
@dataclass
class CustomerRow:
    customer_id: int
    name: str
    status: str

def procedure_name(param1: int, param2: str) -> Optional[Decimal]:
    """
    プロシージャの説明
    
    詳細な説明を複数行で記述。
    ビジネスロジックの背景や注意事項など。
    
    Args:
        param1: パラメータ1の説明
        param2: パラメータ2の説明
    
    Returns:
        戻り値の説明。OUTパラメータがある場合はその説明。
        戻り値がない場合は None。
    
    Raises:
        ValueError: 入力値が不正な場合
        DatabaseError: DB操作に失敗した場合
    
    Note:
        - 注意事項1
        - 注意事項2
    """
    # ロジックをここに記述
    ...
```

### 4.2 変数定義

**DB固有構文:**
```sql
-- Oracle PL/SQL
DECLARE
  v_count NUMBER := 0;
  v_name VARCHAR2(100);
  v_total NUMBER(10,2) DEFAULT 0;
  v_date DATE := SYSDATE;

-- SQL Server T-SQL
DECLARE @count INT = 0;
DECLARE @name VARCHAR(100);
DECLARE @total DECIMAL(10,2) = 0;
DECLARE @date DATETIME = GETDATE();

-- PostgreSQL PL/pgSQL
DECLARE
  v_count INTEGER := 0;
  v_name VARCHAR(100);
  v_total NUMERIC(10,2) DEFAULT 0;
  v_date DATE := CURRENT_DATE;
```

**Pythonサンプルコード:**
```python
def example_procedure() -> None:
    """変数定義の例"""
    
    # 数値変数（初期値あり）
    count: int = 0
    total: Decimal = Decimal("0")
    
    # 文字列変数（初期値なし → None）
    name: Optional[str] = None
    
    # 日付変数
    current_date: date = date.today()
    current_datetime: datetime = datetime.now()
    
    # 定数（大文字で定義）
    TAX_RATE: Decimal = Decimal("0.1")
    MAX_RETRY: int = 3
```

### 4.3 条件分岐

#### 4.3.1 IF文

**DB固有構文:**
```sql
-- Oracle PL/SQL
IF v_amount > 100000 THEN
  v_discount := v_amount * 0.1;
ELSIF v_amount > 50000 THEN
  v_discount := v_amount * 0.05;
ELSE
  v_discount := 0;
END IF;

-- SQL Server T-SQL
IF @amount > 100000
  SET @discount = @amount * 0.1;
ELSE IF @amount > 50000
  SET @discount = @amount * 0.05;
ELSE
  SET @discount = 0;

-- PostgreSQL PL/pgSQL
IF v_amount > 100000 THEN
  v_discount := v_amount * 0.1;
ELSIF v_amount > 50000 THEN
  v_discount := v_amount * 0.05;
ELSE
  v_discount := 0;
END IF;

-- MySQL
IF v_amount > 100000 THEN
  SET v_discount = v_amount * 0.1;
ELSEIF v_amount > 50000 THEN
  SET v_discount = v_amount * 0.05;
ELSE
  SET v_discount = 0;
END IF;
```

**Pythonサンプルコード:**
```python
def calculate_discount(amount: Decimal) -> Decimal:
    """割引額を計算"""
    
    if amount > Decimal("100000"):
        discount = amount * Decimal("0.1")
    elif amount > Decimal("50000"):
        discount = amount * Decimal("0.05")
    else:
        discount = Decimal("0")
    
    return discount
```

#### 4.3.2 CASE文

**DB固有構文:**
```sql
-- Oracle PL/SQL
v_category := CASE v_status
  WHEN 'A' THEN 'Active'
  WHEN 'I' THEN 'Inactive'
  WHEN 'P' THEN 'Pending'
  ELSE 'Unknown'
END;

-- 検索CASE
v_priority := CASE
  WHEN v_amount > 100000 THEN 'High'
  WHEN v_amount > 50000 THEN 'Medium'
  ELSE 'Low'
END;

-- MySQL（CASE文は同様、変数への代入は SET を使用）
SET v_category = CASE v_status
  WHEN 'A' THEN 'Active'
  WHEN 'I' THEN 'Inactive'
  WHEN 'P' THEN 'Pending'
  ELSE 'Unknown'
END;
```

**Pythonサンプルコード:**
```python
def get_category(status: str) -> str:
    """ステータスからカテゴリを取得"""
    
    # 単純CASE（辞書で表現）
    status_map = {
        'A': 'Active',
        'I': 'Inactive',
        'P': 'Pending',
    }
    return status_map.get(status, 'Unknown')


def get_priority(amount: Decimal) -> str:
    """金額から優先度を取得"""
    
    # 検索CASE（if-elif で表現）
    if amount > Decimal("100000"):
        return 'High'
    elif amount > Decimal("50000"):
        return 'Medium'
    else:
        return 'Low'
```

### 4.4 ループ

#### 4.4.1 FORループ（数値範囲）

**DB固有構文:**
```sql
-- Oracle PL/SQL
FOR i IN 1..10 LOOP
  DBMS_OUTPUT.PUT_LINE('Count: ' || i);
END LOOP;

-- 逆順
FOR i IN REVERSE 1..10 LOOP
  ...
END LOOP;

-- PostgreSQL PL/pgSQL
FOR i IN 1..10 LOOP
  RAISE NOTICE 'Count: %', i;
END LOOP;
```

**Pythonサンプルコード:**
```python
def loop_example() -> None:
    """FORループの例"""
    
    # 1から10まで
    for i in range(1, 11):
        log.info(f"Count: {i}")
    
    # 逆順
    for i in range(10, 0, -1):
        log.info(f"Count: {i}")
```

#### 4.4.2 WHILEループ

**DB固有構文:**
```sql
-- Oracle PL/SQL
WHILE v_count < 10 LOOP
  v_count := v_count + 1;
  -- 処理
END LOOP;

-- SQL Server T-SQL
WHILE @count < 10
BEGIN
  SET @count = @count + 1;
  -- 処理
END;

-- PostgreSQL PL/pgSQL
WHILE v_count < 10 LOOP
  v_count := v_count + 1;
  -- 処理
END LOOP;

-- MySQL
WHILE v_count < 10 DO
  SET v_count = v_count + 1;
  -- 処理
END WHILE;
```

**Pythonサンプルコード:**
```python
def while_example() -> None:
    """WHILEループの例"""
    
    count: int = 0
    
    while count < 10:
        count += 1
        # 処理
        ...
```

#### 4.4.3 ループ制御

**DB固有構文:**
```sql
-- Oracle PL/SQL
LOOP
  FETCH cursor INTO v_record;
  EXIT WHEN cursor%NOTFOUND;
  
  IF v_record.status = 'skip' THEN
    CONTINUE;
  END IF;
  
  -- 処理
END LOOP;

-- SQL Server T-SQL
WHILE 1=1
BEGIN
  FETCH NEXT FROM cursor INTO @record;
  IF @@FETCH_STATUS <> 0 BREAK;
  
  IF @status = 'skip' CONTINUE;
  
  -- 処理
END;

-- PostgreSQL PL/pgSQL
LOOP
  FETCH cursor INTO v_record;
  EXIT WHEN NOT FOUND;
  
  IF v_record.status = 'skip' THEN
    CONTINUE;
  END IF;
  
  -- 処理
END LOOP;

-- MySQL（ラベル付きループ）
process_loop: LOOP
  FETCH cursor INTO v_customer_id, v_name, v_status;
  IF done THEN
    LEAVE process_loop;
  END IF;
  
  IF v_status = 'skip' THEN
    ITERATE process_loop;
  END IF;
  
  -- 処理
END LOOP process_loop;
```

**Pythonサンプルコード:**
```python
def loop_control_example() -> None:
    """ループ制御の例"""
    
    for record in db.cursor("SELECT ..."):
        # CONTINUE相当
        if record.status == 'skip':
            continue
        
        # EXIT相当
        if record.status == 'stop':
            break
        
        # 処理
        ...
```

### 4.5 カーソル操作

#### 4.5.1 明示的カーソル

**DB固有構文:**
```sql
-- Oracle PL/SQL
DECLARE
  CURSOR c_customers IS
    SELECT customer_id, name, status
    FROM customers
    WHERE status = 'active';
  v_customer c_customers%ROWTYPE;
BEGIN
  OPEN c_customers;
  LOOP
    FETCH c_customers INTO v_customer;
    EXIT WHEN c_customers%NOTFOUND;
    
    -- 処理
    DBMS_OUTPUT.PUT_LINE(v_customer.name);
  END LOOP;
  CLOSE c_customers;
END;

-- SQL Server T-SQL
DECLARE customer_cursor CURSOR FOR
  SELECT customer_id, name, status
  FROM customers
  WHERE status = 'active';

DECLARE @customer_id INT, @name VARCHAR(100), @status VARCHAR(10);

OPEN customer_cursor;
FETCH NEXT FROM customer_cursor INTO @customer_id, @name, @status;

WHILE @@FETCH_STATUS = 0
BEGIN
  -- 処理
  PRINT @name;
  FETCH NEXT FROM customer_cursor INTO @customer_id, @name, @status;
END;

CLOSE customer_cursor;
DEALLOCATE customer_cursor;

-- PostgreSQL PL/pgSQL
DECLARE
  c_customers CURSOR FOR
    SELECT customer_id, name, status
    FROM customers
    WHERE status = 'active';
  v_customer RECORD;
BEGIN
  OPEN c_customers;
  LOOP
    FETCH c_customers INTO v_customer;
    EXIT WHEN NOT FOUND;
    
    -- 処理
    RAISE NOTICE '%', v_customer.name;
  END LOOP;
  CLOSE c_customers;
END;

-- MySQL
DECLARE done INT DEFAULT FALSE;
DECLARE v_customer_id INT;
DECLARE v_name VARCHAR(100);
DECLARE v_status VARCHAR(10);

DECLARE customer_cursor CURSOR FOR
  SELECT customer_id, name, status
  FROM customers
  WHERE status = 'active';

DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

OPEN customer_cursor;

read_loop: LOOP
  FETCH customer_cursor INTO v_customer_id, v_name, v_status;
  IF done THEN
    LEAVE read_loop;
  END IF;
  
  -- 処理
  SELECT v_name;
END LOOP;

CLOSE customer_cursor;
```

**Pythonサンプルコード:**
```python
@dataclass
class CustomerRow:
    """顧客レコード"""
    customer_id: int
    name: str
    status: str


def cursor_example() -> None:
    """明示的カーソルの例"""
    
    # カーソルを開いて順次処理
    # db.cursor() は Iterator を返す抽象化
    for customer in db.cursor("""
        SELECT customer_id, name, status
        FROM customers
        WHERE status = 'active'
    """, row_type=CustomerRow):
        # 処理
        log.info(customer.name)
```

#### 4.5.2 カーソルFORループ

**DB固有構文:**
```sql
-- Oracle PL/SQL（暗黙的OPEN/FETCH/CLOSE）
FOR rec IN (
  SELECT customer_id, name
  FROM customers
  WHERE status = 'active'
) LOOP
  -- 処理
  DBMS_OUTPUT.PUT_LINE(rec.name);
END LOOP;
```

**Pythonサンプルコード:**
```python
def cursor_for_example() -> None:
    """カーソルFORループの例（暗黙的カーソル）"""
    
    # db.query() で直接イテレート
    for rec in db.query("""
        SELECT customer_id, name
        FROM customers
        WHERE status = 'active'
    """):
        # 処理
        log.info(rec.name)
```

#### 4.5.3 バルクフェッチ

**DB固有構文:**
```sql
-- Oracle PL/SQL
DECLARE
  TYPE t_customers IS TABLE OF customers%ROWTYPE;
  v_customers t_customers;
BEGIN
  SELECT * BULK COLLECT INTO v_customers
  FROM customers
  WHERE status = 'active';
  
  FOR i IN 1..v_customers.COUNT LOOP
    -- 処理
  END LOOP;
END;
```

**Pythonサンプルコード:**
```python
def bulk_fetch_example() -> None:
    """バルクフェッチの例"""
    
    # 全件をリストとして取得
    customers: List[CustomerRow] = db.fetch_all("""
        SELECT customer_id, name, status
        FROM customers
        WHERE status = 'active'
    """, row_type=CustomerRow)
    
    for customer in customers:
        # 処理
        ...
```

### 4.6 例外処理

#### 4.6.1 基本的な例外処理

**DB固有構文:**
```sql
-- Oracle PL/SQL
BEGIN
  -- 処理
  INSERT INTO logs (message) VALUES ('処理開始');
  
  -- エラーが発生する可能性のある処理
  UPDATE accounts SET balance = balance - v_amount
  WHERE account_id = v_account_id;
  
  IF SQL%ROWCOUNT = 0 THEN
    RAISE_APPLICATION_ERROR(-20001, 'Account not found');
  END IF;
  
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    -- データなしエラー
    DBMS_OUTPUT.PUT_LINE('No data found');
    RAISE;
  WHEN DUP_VAL_ON_INDEX THEN
    -- 一意制約違反
    DBMS_OUTPUT.PUT_LINE('Duplicate value');
    RAISE;
  WHEN OTHERS THEN
    -- その他のエラー
    DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
    ROLLBACK;
    RAISE;
END;

-- SQL Server T-SQL
BEGIN TRY
  -- 処理
  INSERT INTO logs (message) VALUES ('処理開始');
  
  UPDATE accounts SET balance = balance - @amount
  WHERE account_id = @account_id;
  
  IF @@ROWCOUNT = 0
    THROW 50001, 'Account not found', 1;
    
END TRY
BEGIN CATCH
  PRINT 'Error: ' + ERROR_MESSAGE();
  ROLLBACK;
  THROW;
END CATCH;

-- PostgreSQL PL/pgSQL
BEGIN
  -- 処理
  INSERT INTO logs (message) VALUES ('処理開始');
  
  UPDATE accounts SET balance = balance - v_amount
  WHERE account_id = v_account_id;
  
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Account not found: %', v_account_id;
  END IF;
  
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RAISE NOTICE 'No data found';
    RAISE;
  WHEN unique_violation THEN
    RAISE NOTICE 'Duplicate value';
    RAISE;
  WHEN OTHERS THEN
    RAISE NOTICE 'Error: %', SQLERRM;
    ROLLBACK;
    RAISE;
END;

-- MySQL
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
  -- エラー発生時の処理
  GET DIAGNOSTICS CONDITION 1 @sqlstate = RETURNED_SQLSTATE, @errmsg = MESSAGE_TEXT;
  SELECT CONCAT('Error: ', @errmsg);
  ROLLBACK;
  RESIGNAL;
END;

DECLARE EXIT HANDLER FOR NOT FOUND
BEGIN
  SELECT 'No data found';
END;

-- 処理
INSERT INTO logs (message) VALUES ('処理開始');

UPDATE accounts SET balance = balance - v_amount
WHERE account_id = v_account_id;

IF ROW_COUNT() = 0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Account not found';
END IF;
```

**Pythonサンプルコード:**
```python
class AccountNotFoundError(Exception):
    """アカウントが見つからないエラー"""
    pass


class DuplicateValueError(Exception):
    """重複値エラー"""
    pass


def transfer_example(account_id: int, amount: Decimal) -> None:
    """例外処理の例"""
    
    try:
        # 処理開始ログ
        db.execute("INSERT INTO logs (message) VALUES ('処理開始')")
        
        # 更新処理
        result = db.execute("""
            UPDATE accounts SET balance = balance - :amount
            WHERE account_id = :account_id
        """, amount=amount, account_id=account_id)
        
        # 更新件数チェック
        if result.rowcount == 0:
            raise AccountNotFoundError(f"Account not found: {account_id}")
        
    except AccountNotFoundError:
        # データなしエラー
        log.warning("Account not found")
        raise
    
    except DuplicateValueError:
        # 一意制約違反
        log.warning("Duplicate value")
        raise
    
    except DatabaseError as e:
        # その他のDBエラー
        log.error(f"Database error: {e}")
        db.rollback()
        raise
```

#### 4.6.2 カスタム例外

**DB固有構文:**
```sql
-- Oracle PL/SQL
DECLARE
  e_insufficient_balance EXCEPTION;
  PRAGMA EXCEPTION_INIT(e_insufficient_balance, -20002);
BEGIN
  IF v_balance < v_amount THEN
    RAISE e_insufficient_balance;
  END IF;
EXCEPTION
  WHEN e_insufficient_balance THEN
    DBMS_OUTPUT.PUT_LINE('Insufficient balance');
END;
```

**Pythonサンプルコード:**
```python
class InsufficientBalanceError(Exception):
    """残高不足エラー"""
    def __init__(self, balance: Decimal, required: Decimal):
        self.balance = balance
        self.required = required
        super().__init__(f"Insufficient balance: {balance} < {required}")


def withdraw(account_id: int, amount: Decimal) -> None:
    """出金処理"""
    
    balance = db.query_one("""
        SELECT balance FROM accounts WHERE account_id = :account_id
    """, account_id=account_id).balance
    
    if balance < amount:
        raise InsufficientBalanceError(balance, amount)
    
    # 出金処理
    ...
```

### 4.7 トランザクション制御

**DB固有構文:**
```sql
-- Oracle PL/SQL
BEGIN
  SAVEPOINT before_update;
  
  UPDATE accounts SET balance = balance - v_amount
  WHERE account_id = v_from_account;
  
  UPDATE accounts SET balance = balance + v_amount
  WHERE account_id = v_to_account;
  
  COMMIT;
EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK TO before_update;
    RAISE;
END;

-- SQL Server T-SQL
BEGIN TRANSACTION;
SAVE TRANSACTION before_update;

BEGIN TRY
  UPDATE accounts SET balance = balance - @amount
  WHERE account_id = @from_account;
  
  UPDATE accounts SET balance = balance + @amount
  WHERE account_id = @to_account;
  
  COMMIT TRANSACTION;
END TRY
BEGIN CATCH
  ROLLBACK TRANSACTION before_update;
  THROW;
END CATCH;
```

**Pythonサンプルコード:**
```python
def transfer(from_account: int, to_account: int, amount: Decimal) -> None:
    """送金処理（トランザクション制御の例）"""
    
    # トランザクション開始（コンテキストマネージャ）
    with db.transaction() as tx:
        try:
            # セーブポイント
            tx.savepoint("before_update")
            
            # 出金
            db.execute("""
                UPDATE accounts SET balance = balance - :amount
                WHERE account_id = :account_id
            """, amount=amount, account_id=from_account)
            
            # 入金
            db.execute("""
                UPDATE accounts SET balance = balance + :amount
                WHERE account_id = :account_id
            """, amount=amount, account_id=to_account)
            
            # コミット（with ブロック終了時に自動コミット）
            
        except Exception:
            # セーブポイントまでロールバック
            tx.rollback_to("before_update")
            raise
```

### 4.8 ファイル入出力

#### 4.8.1 ファイル読み込み

**DB固有構文:**
```sql
-- Oracle PL/SQL (UTL_FILE)
DECLARE
  v_file UTL_FILE.FILE_TYPE;
  v_line VARCHAR2(32767);
  v_dir VARCHAR2(100) := 'DATA_DIR';  -- ディレクトリオブジェクト
  v_filename VARCHAR2(100) := 'input.csv';
BEGIN
  v_file := UTL_FILE.FOPEN(v_dir, v_filename, 'R');
  
  LOOP
    BEGIN
      UTL_FILE.GET_LINE(v_file, v_line);
      -- 行を処理
      DBMS_OUTPUT.PUT_LINE(v_line);
    EXCEPTION
      WHEN NO_DATA_FOUND THEN
        EXIT;
    END;
  END LOOP;
  
  UTL_FILE.FCLOSE(v_file);
EXCEPTION
  WHEN OTHERS THEN
    IF UTL_FILE.IS_OPEN(v_file) THEN
      UTL_FILE.FCLOSE(v_file);
    END IF;
    RAISE;
END;

-- SQL Server T-SQL (BULK INSERT / OPENROWSET)
BULK INSERT staging_table
FROM 'C:\data\input.csv'
WITH (
  FIELDTERMINATOR = ',',
  ROWTERMINATOR = '\n',
  FIRSTROW = 2
);
```

**Pythonサンプルコード:**
```python
import csv
from pathlib import Path


def read_csv_example(file_path: str) -> None:
    """CSVファイル読み込みの例"""
    
    # ファイルを開いて行ごとに処理
    with file.open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # 行を処理
            log.info(f"Processing: {row}")
            
            # DBに挿入
            db.execute("""
                INSERT INTO staging_table (col1, col2, col3)
                VALUES (:col1, :col2, :col3)
            """, **row)


def read_file_lines(file_path: str) -> None:
    """テキストファイル行読み込みの例"""
    
    with file.open(file_path, mode='r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            
            # 空行スキップ
            if not line:
                continue
            
            # 行を処理
            log.info(f"Line {line_number}: {line}")
```

#### 4.8.2 ファイル書き込み

**DB固有構文:**
```sql
-- Oracle PL/SQL (UTL_FILE)
DECLARE
  v_file UTL_FILE.FILE_TYPE;
  v_dir VARCHAR2(100) := 'DATA_DIR';
  v_filename VARCHAR2(100) := 'output.csv';
BEGIN
  v_file := UTL_FILE.FOPEN(v_dir, v_filename, 'W');
  
  -- ヘッダー行
  UTL_FILE.PUT_LINE(v_file, 'customer_id,name,amount');
  
  -- データ行
  FOR rec IN (SELECT customer_id, name, amount FROM customers) LOOP
    UTL_FILE.PUT_LINE(v_file, 
      rec.customer_id || ',' || rec.name || ',' || rec.amount);
  END LOOP;
  
  UTL_FILE.FCLOSE(v_file);
EXCEPTION
  WHEN OTHERS THEN
    IF UTL_FILE.IS_OPEN(v_file) THEN
      UTL_FILE.FCLOSE(v_file);
    END IF;
    RAISE;
END;

-- SQL Server T-SQL (BCP / SQLCMD)
-- 通常は外部ツールを使用
```

**Pythonサンプルコード:**
```python
import csv


def write_csv_example(file_path: str) -> None:
    """CSVファイル書き込みの例"""
    
    with file.open(file_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # ヘッダー行
        writer.writerow(['customer_id', 'name', 'amount'])
        
        # データ行
        for rec in db.query("""
            SELECT customer_id, name, amount FROM customers
        """):
            writer.writerow([rec.customer_id, rec.name, rec.amount])


def write_log_example(file_path: str, message: str) -> None:
    """ログファイル追記の例"""
    
    with file.open(file_path, mode='a', encoding='utf-8') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp}: {message}\n")
```

#### 4.8.3 ファイル操作（存在確認、削除等）

**DB固有構文:**
```sql
-- Oracle PL/SQL (UTL_FILE)
DECLARE
  v_exists BOOLEAN;
BEGIN
  -- ファイル存在確認
  v_exists := UTL_FILE.FGETATTR(v_dir, v_filename, v_exists, v_length, v_blocksize);
  
  -- ファイル削除
  UTL_FILE.FREMOVE(v_dir, v_filename);
  
  -- ファイルコピー
  UTL_FILE.FCOPY(v_src_dir, v_src_file, v_dest_dir, v_dest_file);
  
  -- ファイルリネーム
  UTL_FILE.FRENAME(v_dir, v_old_name, v_dir, v_new_name);
END;
```

**Pythonサンプルコード:**
```python
from pathlib import Path
import shutil


def file_operations_example() -> None:
    """ファイル操作の例"""
    
    src_path = "/data/input/source.csv"
    dest_path = "/data/output/destination.csv"
    
    # ファイル存在確認
    if file.exists(src_path):
        log.info(f"File exists: {src_path}")
    
    # ファイルサイズ取得
    size = file.size(src_path)
    log.info(f"File size: {size} bytes")
    
    # ファイルコピー
    file.copy(src_path, dest_path)
    
    # ファイルリネーム（移動）
    file.rename(src_path, "/data/archive/source_backup.csv")
    
    # ファイル削除
    file.remove(dest_path)
    
    # ディレクトリ作成
    file.makedirs("/data/output/new_dir")
```

### 5.9 動的SQL

**DB固有構文:**
```sql
-- Oracle PL/SQL
DECLARE
  v_sql VARCHAR2(1000);
  v_count NUMBER;
  v_table_name VARCHAR2(100) := 'customers';
BEGIN
  -- 動的SELECT（INTO）
  v_sql := 'SELECT COUNT(*) FROM ' || v_table_name || ' WHERE status = :1';
  EXECUTE IMMEDIATE v_sql INTO v_count USING 'active';
  
  -- 動的DML
  v_sql := 'UPDATE ' || v_table_name || ' SET updated_at = SYSDATE WHERE id = :1';
  EXECUTE IMMEDIATE v_sql USING 123;
  
  -- 動的DDL
  EXECUTE IMMEDIATE 'CREATE TABLE temp_' || v_table_name || ' AS SELECT * FROM ' || v_table_name;
END;

-- SQL Server T-SQL
DECLARE @sql NVARCHAR(MAX);
DECLARE @count INT;
DECLARE @table_name NVARCHAR(100) = 'customers';

-- 動的SELECT（OUTPUT）
SET @sql = N'SELECT @cnt = COUNT(*) FROM ' + QUOTENAME(@table_name) + N' WHERE status = @status';
EXEC sp_executesql @sql, N'@cnt INT OUTPUT, @status VARCHAR(10)', @count OUTPUT, 'active';

-- 動的DML
SET @sql = N'UPDATE ' + QUOTENAME(@table_name) + N' SET updated_at = GETDATE() WHERE id = @id';
EXEC sp_executesql @sql, N'@id INT', 123;

-- PostgreSQL PL/pgSQL
DECLARE
  v_sql TEXT;
  v_count INTEGER;
  v_table_name TEXT := 'customers';
BEGIN
  -- 動的SELECT（INTO）
  v_sql := 'SELECT COUNT(*) FROM ' || quote_ident(v_table_name) || ' WHERE status = $1';
  EXECUTE v_sql INTO v_count USING 'active';
  
  -- 動的DML
  v_sql := 'UPDATE ' || quote_ident(v_table_name) || ' SET updated_at = NOW() WHERE id = $1';
  EXECUTE v_sql USING 123;
END;

-- MySQL
PREPARE stmt FROM 'SELECT COUNT(*) INTO @cnt FROM customers WHERE status = ?';
SET @status = 'active';
EXECUTE stmt USING @status;
DEALLOCATE PREPARE stmt;
```

**Pythonサンプルコード:**
```python
def dynamic_query_example(table_name: str, status: str) -> int:
    """
    動的SQLの例
    
    Args:
        table_name: テーブル名（許可リストで検証済みの値のみ）
        status: 検索条件
    
    Returns:
        件数
    
    Note:
        SQLインジェクション対策として、table_nameは許可リストで検証する。
        ユーザー入力をそのままテーブル名に使用してはならない。
    """
    # 許可リストによる検証（SQLインジェクション対策）
    ALLOWED_TABLES = {'customers', 'orders', 'products'}
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    
    # 動的SQL（テーブル名は検証済み、パラメータはバインド変数）
    result = db.query_one(f"""
        SELECT COUNT(*) as cnt FROM {table_name} WHERE status = :status
    """, status=status)
    
    return result.cnt


def dynamic_update_example(table_name: str, record_id: int) -> int:
    """
    動的UPDATE文の例
    
    Args:
        table_name: テーブル名（許可リストで検証済み）
        record_id: 更新対象のID
    
    Returns:
        更新件数
    """
    ALLOWED_TABLES = {'customers', 'orders', 'products'}
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    
    result = db.execute(f"""
        UPDATE {table_name} SET updated_at = CURRENT_TIMESTAMP WHERE id = :id
    """, id=record_id)
    
    return result.rowcount


def dynamic_column_example(columns: List[str], table_name: str) -> List[dict]:
    """
    動的カラム選択の例
    
    Args:
        columns: 取得するカラム名のリスト（許可リストで検証済み）
        table_name: テーブル名
    
    Returns:
        結果リスト
    """
    ALLOWED_TABLES = {'customers', 'orders'}
    ALLOWED_COLUMNS = {
        'customers': {'id', 'name', 'email', 'status', 'created_at'},
        'orders': {'id', 'customer_id', 'total', 'status', 'order_date'},
    }
    
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    
    for col in columns:
        if col not in ALLOWED_COLUMNS[table_name]:
            raise ValueError(f"Invalid column name: {col}")
    
    column_list = ", ".join(columns)
    return db.fetch_all(f"""
        SELECT {column_list} FROM {table_name}
    """)
```

**注意事項:**
- 動的SQLはSQLインジェクションのリスクがあるため、慎重に使用する
- テーブル名、カラム名は必ず許可リストで検証する
- ユーザー入力は必ずバインド変数として渡す
- 可能な限り静的SQLを使用し、動的SQLは最小限にする

### 5.10 バルク操作

**DB固有構文:**
```sql
-- Oracle PL/SQL（FORALL）
DECLARE
  TYPE t_ids IS TABLE OF NUMBER INDEX BY PLS_INTEGER;
  v_ids t_ids;
BEGIN
  -- 配列に値を設定
  v_ids(1) := 1;
  v_ids(2) := 2;
  v_ids(3) := 3;
  
  -- バルクUPDATE
  FORALL i IN v_ids.FIRST..v_ids.LAST
    UPDATE customers SET status = 'inactive' WHERE customer_id = v_ids(i);
  
  -- バルクINSERT
  FORALL i IN v_ids.FIRST..v_ids.LAST
    INSERT INTO audit_log (customer_id, action, created_at)
    VALUES (v_ids(i), 'deactivated', SYSDATE);
  
  -- バルクDELETE
  FORALL i IN v_ids.FIRST..v_ids.LAST
    DELETE FROM temp_data WHERE customer_id = v_ids(i);
  
  -- BULK COLLECT（バルク取得）
  SELECT customer_id BULK COLLECT INTO v_ids
  FROM customers WHERE status = 'active';
END;

-- SQL Server T-SQL（テーブル値パラメータ）
-- 事前にテーブル型を定義
CREATE TYPE dbo.IdTableType AS TABLE (id INT);

-- プロシージャ内で使用
CREATE PROCEDURE bulk_update_customers
  @ids dbo.IdTableType READONLY
AS
BEGIN
  UPDATE c SET c.status = 'inactive'
  FROM customers c
  INNER JOIN @ids i ON c.customer_id = i.id;
  
  INSERT INTO audit_log (customer_id, action, created_at)
  SELECT id, 'deactivated', GETDATE() FROM @ids;
END;

-- PostgreSQL PL/pgSQL（UNNEST）
DO $$
DECLARE
  v_ids INTEGER[] := ARRAY[1, 2, 3];
BEGIN
  -- バルクUPDATE
  UPDATE customers SET status = 'inactive'
  WHERE customer_id = ANY(v_ids);
  
  -- バルクINSERT
  INSERT INTO audit_log (customer_id, action, created_at)
  SELECT unnest(v_ids), 'deactivated', NOW();
END $$;

-- MySQL（INSERT ... ON DUPLICATE KEY UPDATE でバルク処理）
INSERT INTO customers (customer_id, status, updated_at)
VALUES 
  (1, 'inactive', NOW()),
  (2, 'inactive', NOW()),
  (3, 'inactive', NOW())
ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = VALUES(updated_at);
```

**Pythonサンプルコード:**
```python
def bulk_update_example(customer_ids: List[int], new_status: str) -> int:
    """
    バルクUPDATEの例
    
    Args:
        customer_ids: 更新対象の顧客IDリスト
        new_status: 新しいステータス
    
    Returns:
        更新件数
    """
    if not customer_ids:
        return 0
    
    # 方法1: execute_many（1件ずつ実行、バッチ化）
    result = db.execute_many("""
        UPDATE customers SET status = :status, updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = :customer_id
    """, [{"customer_id": cid, "status": new_status} for cid in customer_ids])
    
    return result.total_rowcount


def bulk_update_with_in_clause(customer_ids: List[int], new_status: str) -> int:
    """
    IN句を使ったバルクUPDATEの例
    
    Args:
        customer_ids: 更新対象の顧客IDリスト
        new_status: 新しいステータス
    
    Returns:
        更新件数
    """
    if not customer_ids:
        return 0
    
    # 方法2: IN句で一括更新（大量データには注意）
    result = db.execute("""
        UPDATE customers SET status = :status, updated_at = CURRENT_TIMESTAMP
        WHERE customer_id IN (:customer_ids)
    """, status=new_status, customer_ids=customer_ids)
    
    return result.rowcount


def bulk_insert_example(records: List[dict]) -> int:
    """
    バルクINSERTの例
    
    Args:
        records: 挿入するレコードのリスト
    
    Returns:
        挿入件数
    """
    if not records:
        return 0
    
    result = db.execute_many("""
        INSERT INTO audit_log (customer_id, action, created_at)
        VALUES (:customer_id, :action, CURRENT_TIMESTAMP)
    """, records)
    
    return result.total_rowcount


def bulk_upsert_example(records: List[dict]) -> int:
    """
    バルクUPSERTの例
    
    Args:
        records: 挿入/更新するレコードのリスト
    
    Returns:
        処理件数
    """
    if not records:
        return 0
    
    # PostgreSQL: ON CONFLICT
    # MySQL: ON DUPLICATE KEY UPDATE
    # SQL Server: MERGE
    result = db.execute_many("""
        INSERT INTO customers (customer_id, name, status, updated_at)
        VALUES (:customer_id, :name, :status, CURRENT_TIMESTAMP)
        ON CONFLICT (customer_id) DO UPDATE SET
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
    """, records)
    
    return result.total_rowcount


def bulk_delete_example(customer_ids: List[int]) -> int:
    """
    バルクDELETEの例
    
    Args:
        customer_ids: 削除対象の顧客IDリスト
    
    Returns:
        削除件数
    """
    if not customer_ids:
        return 0
    
    result = db.execute("""
        DELETE FROM temp_data WHERE customer_id IN (:customer_ids)
    """, customer_ids=customer_ids)
    
    return result.rowcount


def chunked_bulk_update(customer_ids: List[int], new_status: str, chunk_size: int = 1000) -> int:
    """
    チャンク分割によるバルク更新の例
    
    大量データを処理する場合、メモリとロック時間を考慮して
    チャンクに分割して処理する。
    
    Args:
        customer_ids: 更新対象の顧客IDリスト
        new_status: 新しいステータス
        chunk_size: 1回あたりの処理件数
    
    Returns:
        総更新件数
    """
    total_updated = 0
    
    for i in range(0, len(customer_ids), chunk_size):
        chunk = customer_ids[i:i + chunk_size]
        
        with db.transaction():
            result = db.execute("""
                UPDATE customers SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id IN (:customer_ids)
            """, status=new_status, customer_ids=chunk)
            
            total_updated += result.rowcount
        
        log.info(f"Processed {min(i + chunk_size, len(customer_ids))}/{len(customer_ids)}")
    
    return total_updated
```

**パフォーマンス考慮事項:**

| 方法 | メリット | デメリット | 推奨ケース |
|------|----------|------------|------------|
| `execute_many` | 汎用的、トランザクション制御しやすい | 1件ずつ実行のオーバーヘッド | 中規模データ（〜10,000件） |
| IN句 | 高速、1回のSQL実行 | IN句の上限、大量データでメモリ圧迫 | 小規模データ（〜1,000件） |
| チャンク分割 | 大量データ対応、ロック時間短縮 | 実装が複雑 | 大規模データ（10,000件〜） |

---

## 6. DB固有構文のマッピング

### 5.1 変数定義

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| 整数変数 | `v_count NUMBER := 0` | `DECLARE @count INT = 0` | `v_count INTEGER := 0` | `count: int = 0` |
| 文字列変数 | `v_name VARCHAR2(100)` | `DECLARE @name VARCHAR(100)` | `v_name VARCHAR(100)` | `name: Optional[str] = None` |
| 小数変数 | `v_amount NUMBER(10,2)` | `DECLARE @amount DECIMAL(10,2)` | `v_amount NUMERIC(10,2)` | `amount: Decimal` |
| 日付変数 | `v_date DATE := SYSDATE` | `DECLARE @date DATETIME = GETDATE()` | `v_date DATE := CURRENT_DATE` | `current_date: date = date.today()` |
| 定数 | `c_rate CONSTANT NUMBER := 0.1` | `-- 定数なし（変数で代用）` | `c_rate CONSTANT NUMERIC := 0.1` | `RATE: Decimal = Decimal("0.1")` |

### 5.2 条件分岐

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| IF-THEN | `IF cond THEN ... END IF;` | `IF cond BEGIN ... END` | `IF cond THEN ... END IF;` | `if cond: ...` |
| IF-ELSE | `IF cond THEN ... ELSE ... END IF;` | `IF cond ... ELSE ...` | `IF cond THEN ... ELSE ... END IF;` | `if cond: ... else: ...` |
| ELSIF | `ELSIF cond THEN ...` | `ELSE IF cond ...` | `ELSIF cond THEN ...` | `elif cond: ...` |
| CASE | `CASE expr WHEN ... END` | `CASE expr WHEN ... END` | `CASE expr WHEN ... END` | `match expr: case ...:` または辞書 |

### 5.3 ループ

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| FOR範囲 | `FOR i IN 1..10 LOOP ... END LOOP;` | `-- WHILE で代用` | `FOR i IN 1..10 LOOP ... END LOOP;` | `for i in range(1, 11):` |
| WHILE | `WHILE cond LOOP ... END LOOP;` | `WHILE cond BEGIN ... END` | `WHILE cond LOOP ... END LOOP;` | `while cond: ...` |
| 無限ループ | `LOOP ... END LOOP;` | `WHILE 1=1 BEGIN ... END` | `LOOP ... END LOOP;` | `while True: ...` |
| EXIT | `EXIT WHEN cond;` | `IF cond BREAK;` | `EXIT WHEN cond;` | `if cond: break` |
| CONTINUE | `CONTINUE WHEN cond;` | `IF cond CONTINUE;` | `CONTINUE WHEN cond;` | `if cond: continue` |

### 5.4 カーソル

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| 宣言 | `CURSOR c IS SELECT ...` | `DECLARE c CURSOR FOR SELECT ...` | `c CURSOR FOR SELECT ...` | `db.cursor("SELECT ...")` |
| OPEN | `OPEN c;` | `OPEN c;` | `OPEN c;` | `for row in cursor:` |
| FETCH | `FETCH c INTO v;` | `FETCH NEXT FROM c INTO @v;` | `FETCH c INTO v;` | `（イテレータで抽象化）` |
| CLOSE | `CLOSE c;` | `CLOSE c; DEALLOCATE c;` | `CLOSE c;` | `（with文で自動）` |
| FOR LOOP | `FOR rec IN c LOOP ... END LOOP;` | `-- WHILE で代用` | `FOR rec IN c LOOP ... END LOOP;` | `for rec in db.query(...):` |

### 5.5 例外処理

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| 例外捕捉 | `EXCEPTION WHEN ... THEN ...` | `BEGIN TRY ... END TRY BEGIN CATCH ... END CATCH` | `EXCEPTION WHEN ... THEN ...` | `try: ... except ...: ...` |
| 例外発生 | `RAISE_APPLICATION_ERROR(-20001, 'msg')` | `THROW 50001, 'msg', 1` | `RAISE EXCEPTION 'msg'` | `raise CustomError('msg')` |
| 再スロー | `RAISE;` | `THROW;` | `RAISE;` | `raise` |

### 5.6 トランザクション

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| コミット | `COMMIT;` | `COMMIT TRANSACTION;` | `COMMIT;` | `db.commit()` または `with db.transaction():` |
| ロールバック | `ROLLBACK;` | `ROLLBACK TRANSACTION;` | `ROLLBACK;` | `db.rollback()` |
| セーブポイント | `SAVEPOINT sp;` | `SAVE TRANSACTION sp;` | `SAVEPOINT sp;` | `tx.savepoint("sp")` |
| ロールバック先 | `ROLLBACK TO sp;` | `ROLLBACK TRANSACTION sp;` | `ROLLBACK TO sp;` | `tx.rollback_to("sp")` |

### 5.7 ファイル操作

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | Python |
|------|---------------|------------------|---------------------|--------|
| ファイル読込 | `UTL_FILE.FOPEN/GET_LINE` | `BULK INSERT / OPENROWSET` | `COPY / pg_read_file` | `file.open(path, 'r')` |
| ファイル書込 | `UTL_FILE.FOPEN/PUT_LINE` | `BCP / xp_cmdshell` | `COPY / pg_write_file` | `file.open(path, 'w')` |
| ファイル存在 | `UTL_FILE.FGETATTR` | `xp_fileexist` | `pg_stat_file` | `file.exists(path)` |
| ファイル削除 | `UTL_FILE.FREMOVE` | `xp_cmdshell 'del ...'` | `pg_file_unlink` | `file.remove(path)` |

**注意:** PostgreSQLの`pg_read_file`、`pg_write_file`は管理者権限が必要です。一般的なアプリケーションではアプリケーション層でファイル操作を行うことを推奨します。

### 5.8 動的SQL

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | MySQL | Python |
|------|---------------|------------------|---------------------|-------|--------|
| 動的実行 | `EXECUTE IMMEDIATE sql` | `EXEC sp_executesql @sql` | `EXECUTE sql` | `PREPARE/EXECUTE` | `db.execute(f"...")` |
| パラメータ | `USING param1, param2` | `@param1, @param2` | `USING $1, $2` | `USING @var` | `db.execute(sql, **params)` |
| 結果取得 | `INTO var` | `@var OUTPUT` | `INTO var` | `INTO @var` | `db.query_one(sql)` |
| 識別子引用 | `DBMS_ASSERT.SIMPLE_SQL_NAME` | `QUOTENAME()` | `quote_ident()` | バッククォート | 許可リスト検証 |

### 5.9 バルク操作

| 概念 | Oracle PL/SQL | SQL Server T-SQL | PostgreSQL PL/pgSQL | MySQL | Python |
|------|---------------|------------------|---------------------|-------|--------|
| バルクINSERT | `FORALL ... INSERT` | テーブル値パラメータ | `INSERT ... SELECT` | `INSERT ... VALUES (),()`| `db.execute_many()` |
| バルクUPDATE | `FORALL ... UPDATE` | `UPDATE ... JOIN @tvp` | `UPDATE ... WHERE IN` | `UPDATE ... WHERE IN` | `db.execute_many()` |
| バルクDELETE | `FORALL ... DELETE` | `DELETE ... JOIN @tvp` | `DELETE ... WHERE IN` | `DELETE ... WHERE IN` | `db.execute_many()` |
| バルク取得 | `BULK COLLECT INTO` | `SELECT INTO @table` | `ARRAY_AGG` | `GROUP_CONCAT` | `db.fetch_all()` |

---

## 6. 変換例

### 6.1 月次請求処理（複合例）

**元のOracle PL/SQL:**
```sql
CREATE OR REPLACE PROCEDURE process_monthly_billing IS
  -- カーソル定義
  CURSOR c_customers IS
    SELECT customer_id, billing_type, email
    FROM customers
    WHERE status = 'active';
  
  -- 変数定義
  v_total NUMBER(10,2);
  v_discount NUMBER(10,2);
  v_invoice_id NUMBER;
  v_file UTL_FILE.FILE_TYPE;
  v_line VARCHAR2(4000);
  
  -- カスタム例外
  e_no_transactions EXCEPTION;
  
BEGIN
  -- ログファイルを開く
  v_file := UTL_FILE.FOPEN('LOG_DIR', 'billing_' || TO_CHAR(SYSDATE, 'YYYYMMDD') || '.log', 'W');
  UTL_FILE.PUT_LINE(v_file, 'Billing process started: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS'));
  
  -- 顧客ごとに処理
  FOR rec IN c_customers LOOP
    BEGIN
      SAVEPOINT before_customer;
      
      -- 当月の取引合計を取得
      SELECT NVL(SUM(amount), 0) INTO v_total
      FROM transactions
      WHERE customer_id = rec.customer_id
        AND transaction_date >= TRUNC(SYSDATE, 'MM')
        AND transaction_date < ADD_MONTHS(TRUNC(SYSDATE, 'MM'), 1);
      
      -- 取引がない場合はスキップ
      IF v_total = 0 THEN
        UTL_FILE.PUT_LINE(v_file, 'No transactions for customer: ' || rec.customer_id);
        CONTINUE;
      END IF;
      
      -- 割引計算
      IF rec.billing_type = 'premium' THEN
        v_discount := v_total * 0.1;
      ELSIF v_total > 100000 THEN
        v_discount := v_total * 0.05;
      ELSE
        v_discount := 0;
      END IF;
      
      -- 請求書作成
      INSERT INTO invoices (customer_id, amount, discount, billing_date, status)
      VALUES (rec.customer_id, v_total, v_discount, SYSDATE, 'pending')
      RETURNING invoice_id INTO v_invoice_id;
      
      -- ログ出力
      UTL_FILE.PUT_LINE(v_file, 
        'Invoice created: ' || v_invoice_id || 
        ', Customer: ' || rec.customer_id || 
        ', Amount: ' || v_total || 
        ', Discount: ' || v_discount);
      
      COMMIT;
      
    EXCEPTION
      WHEN OTHERS THEN
        ROLLBACK TO before_customer;
        UTL_FILE.PUT_LINE(v_file, 
          'Error for customer ' || rec.customer_id || ': ' || SQLERRM);
    END;
  END LOOP;
  
  UTL_FILE.PUT_LINE(v_file, 'Billing process completed: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS'));
  UTL_FILE.FCLOSE(v_file);
  
EXCEPTION
  WHEN OTHERS THEN
    IF UTL_FILE.IS_OPEN(v_file) THEN
      UTL_FILE.FCLOSE(v_file);
    END IF;
    RAISE;
END;
/
```

**YQL定義:**
```yaml
procedures:
  process_monthly_billing:
    label: "月次請求処理"
    description: |
      アクティブな顧客に対して、当月の取引を集計し、
      請求書を作成する。プレミアム顧客または高額利用者には
      割引を適用する。処理ログはファイルに出力される。
    
    parameters: []  # パラメータなし
    
    returns:
      type: void
    
    dependencies:
      tables:
        - customers
        - transactions
        - invoices
      files:
        - "/log/billing_YYYYMMDD.log"
    
    python_sample: |
      from decimal import Decimal
      from datetime import date, datetime
      from typing import Optional
      from dataclasses import dataclass
      
      
      @dataclass
      class CustomerRow:
          """顧客レコード"""
          customer_id: int
          billing_type: str
          email: str
      
      
      def process_monthly_billing() -> None:
          """
          月次請求処理
          
          アクティブな顧客に対して、当月の取引を集計し、
          請求書を作成する。プレミアム顧客または高額利用者には
          割引を適用する。
          
          処理ログはファイルに出力される。
          
          Raises:
              DatabaseError: DB操作に失敗した場合
              FileError: ログファイルの操作に失敗した場合
          """
          log_filename = f"billing_{date.today().strftime('%Y%m%d')}.log"
          log_path = f"/log/{log_filename}"
          
          try:
              with file.open(log_path, mode='w', encoding='utf-8') as log_file:
                  log_file.write(f"Billing process started: {datetime.now()}\n")
                  
                  # アクティブな顧客を取得
                  for customer in db.cursor("""
                      SELECT customer_id, billing_type, email
                      FROM customers
                      WHERE status = 'active'
                  """, row_type=CustomerRow):
                      
                      try:
                          process_customer_billing(customer, log_file)
                      except DatabaseError as e:
                          log_file.write(f"Error for customer {customer.customer_id}: {e}\n")
                  
                  log_file.write(f"Billing process completed: {datetime.now()}\n")
          
          except FileError:
              raise
      
      
      def process_customer_billing(customer: CustomerRow, log_file) -> None:
          """
          顧客ごとの請求処理
          
          Args:
              customer: 顧客情報
              log_file: ログファイルハンドル
          """
          with db.transaction() as tx:
              tx.savepoint("before_customer")
              
              try:
                  # 当月の取引合計を取得
                  total = get_monthly_total(customer.customer_id)
                  
                  # 取引がない場合はスキップ
                  if total == Decimal("0"):
                      log_file.write(f"No transactions for customer: {customer.customer_id}\n")
                      return
                  
                  # 割引計算
                  discount = calculate_discount(customer.billing_type, total)
                  
                  # 請求書作成
                  invoice_id = create_invoice(
                      customer_id=customer.customer_id,
                      amount=total,
                      discount=discount
                  )
                  
                  # ログ出力
                  log_file.write(
                      f"Invoice created: {invoice_id}, "
                      f"Customer: {customer.customer_id}, "
                      f"Amount: {total}, "
                      f"Discount: {discount}\n"
                  )
                  
              except Exception:
                  tx.rollback_to("before_customer")
                  raise
      
      
      def get_monthly_total(customer_id: int) -> Decimal:
          """当月の取引合計を取得"""
          result = db.query_one("""
              SELECT COALESCE(SUM(amount), 0) as total
              FROM transactions
              WHERE customer_id = :customer_id
                AND transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
                AND transaction_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
          """, customer_id=customer_id)
          return result.total
      
      
      def calculate_discount(billing_type: str, total: Decimal) -> Decimal:
          """割引額を計算"""
          if billing_type == 'premium':
              return total * Decimal("0.1")
          elif total > Decimal("100000"):
              return total * Decimal("0.05")
          else:
              return Decimal("0")
      
      
      def create_invoice(customer_id: int, amount: Decimal, discount: Decimal) -> int:
          """請求書を作成"""
          result = db.execute("""
              INSERT INTO invoices (customer_id, amount, discount, billing_date, status)
              VALUES (:customer_id, :amount, :discount, CURRENT_DATE, 'pending')
              RETURNING invoice_id
          """, customer_id=customer_id, amount=amount, discount=discount)
          return result.invoice_id
    
    original_code:
      oracle: |
        CREATE OR REPLACE PROCEDURE process_monthly_billing IS
          ...
        END;
    
    metadata:
      created_by: "system"
      version: "1.0.0"
      tags:
        - "batch"
        - "billing"
        - "monthly"
```

---

## 7. 利用シーン

### 7.1 AI解析での活用

**プロンプト例:**
```
以下のストアドプロシージャについて、以下の観点で解析してください：
1. ビジネスロジックの妥当性
2. パフォーマンス上の問題点
3. エラーハンドリングの改善点
4. セキュリティ上の懸念

## Pythonサンプルコード（ロジック説明）
[python_sample の内容]

## 元のOracle PL/SQL
[original_code の内容]
```

### 7.2 移行計画での活用

**確認事項:**
- 依存するテーブル/ビュー
- 使用しているファイルパス
- 外部サービスとの連携
- トランザクション制御の方式

### 7.3 ドキュメント生成での活用

- Pythonサンプルコードからフローチャート生成
- 依存関係図の自動生成
- テストケースの設計支援

---

## 8. 実装時の注意事項

### 8.1 Pythonサンプルコードの品質

| 観点 | 推奨事項 |
|------|----------|
| **型ヒント** | 必須。すべての引数と戻り値に型を付ける |
| **docstring** | 必須。Google形式で記述 |
| **関数分割** | 1関数1責務。長い処理は分割する |
| **命名規則** | snake_case。意味のある名前を付ける |
| **エラー処理** | 明示的に例外を定義・捕捉する |

### 8.2 元コードとの対応

| 観点 | 推奨事項 |
|------|----------|
| **ロジックの一致** | Pythonコードは元コードと同じロジックを表現する |
| **簡略化** | 冗長な部分は簡略化してよい（可読性優先） |
| **コメント** | 元コードとの対応が分かるようにコメントを付ける |

### 8.3 DB操作の抽象化

| 抽象化 | 用途 |
|--------|------|
| `db.query(sql, **params)` | SELECT（複数行） |
| `db.query_one(sql, **params)` | SELECT（単一行） |
| `db.cursor(sql, **params)` | カーソル（イテレータ） |
| `db.fetch_all(sql, **params)` | SELECT（全件をリストで取得） |
| `db.execute(sql, **params)` | INSERT/UPDATE/DELETE（単一） |
| `db.execute_many(sql, params_list)` | INSERT/UPDATE/DELETE（バルク） |
| `db.transaction()` | トランザクション開始 |
| `tx.savepoint(name)` | セーブポイント |
| `tx.rollback_to(name)` | ロールバック |
| `db.output(message)` | DBMS_OUTPUT相当（デバッグ出力） |

**`db.query()` と `db.cursor()` の使い分け:**

| メソッド | 用途 | メモリ使用 |
|----------|------|-----------|
| `db.query()` | 結果セットを直接イテレート | 低（ストリーミング） |
| `db.cursor()` | 明示的なカーソル操作 | 低（ストリーミング） |
| `db.fetch_all()` | 全件をリストで取得 | 高（全件メモリ） |

```python
# db.query() - 結果セットを直接イテレート（推奨）
for row in db.query("SELECT * FROM customers"):
    process(row)

# db.cursor() - 明示的なカーソル（型指定やオプション指定時）
for row in db.cursor("SELECT * FROM customers", row_type=CustomerRow):
    process(row)

# db.fetch_all() - 全件をリストで取得（小規模データ向け）
customers = db.fetch_all("SELECT * FROM customers")
```

### 8.4 ファイル操作の抽象化

| 抽象化 | 用途 |
|--------|------|
| `file.open(path, mode)` | ファイルを開く |
| `file.exists(path)` | 存在確認 |
| `file.size(path)` | サイズ取得 |
| `file.copy(src, dest)` | コピー |
| `file.rename(src, dest)` | リネーム/移動 |
| `file.remove(path)` | 削除 |
| `file.makedirs(path)` | ディレクトリ作成 |

**注意:** ファイル操作は必ず `with` 文を使用してリソースを適切に解放してください。

```python
# 推奨: with文を使用
with file.open(path, mode='r') as f:
    for line in f:
        process(line)

# 非推奨: with文なし（リソースリークの可能性）
f = file.open(path, mode='r')
# ...
f.close()  # 例外発生時にcloseされない可能性
```

### 8.5 ログ出力の抽象化

| 抽象化 | 用途 | 出力先 |
|--------|------|--------|
| `log.debug(message)` | デバッグ情報 | アプリケーションログ |
| `log.info(message)` | 情報メッセージ | アプリケーションログ |
| `log.warning(message)` | 警告メッセージ | アプリケーションログ |
| `log.error(message)` | エラーメッセージ | アプリケーションログ |
| `db.output(message)` | DB出力（DBMS_OUTPUT相当） | DBセッション出力 |
| `file.write()` | ファイル出力 | 指定ファイル |

**使い分け:**

```python
# アプリケーションログ（標準的なログ出力）
log.info("処理を開始します")
log.warning("データが見つかりません")
log.error(f"エラーが発生しました: {e}")

# DB出力（DBMS_OUTPUT相当、デバッグ用）
db.output("デバッグ: 変数の値を確認")

# ファイル出力（処理ログ、結果ファイル）
with file.open("/log/process.log", mode='a') as f:
    f.write(f"{datetime.now()}: 処理完了\n")
```

**DB固有のログ出力との対応:**

| Python | Oracle | SQL Server | PostgreSQL |
|--------|--------|------------|------------|
| `log.info()` | アプリ層 | アプリ層 | アプリ層 |
| `db.output()` | `DBMS_OUTPUT.PUT_LINE` | `PRINT` | `RAISE NOTICE` |

### 8.6 他仕様書との連携

この仕様書は以下の仕様書と連携します：

| 仕様書 | 連携内容 |
|--------|----------|
| `specs/schema.md` | データ型定義、テーブル定義の参照 |
| `specs/select.md` | SELECT文の構文 |
| `specs/insert.md` | INSERT文の構文 |
| `specs/update.md` | UPDATE文の構文 |
| `specs/delete.md` | DELETE文の構文 |
| `specs/import.md` | using機能によるスキーマ/マクロの参照 |

**using機能との連携（将来対応）:**

```yaml
# プロシージャ定義でのusing
using:
  - "schemas/ecommerce.yql"          # スキーマ定義
  - "procedures/common.yql"          # 共通プロシージャ
  - "macros/date_functions.yql"      # マクロ

procedures:
  my_procedure:
    # スキーマ定義を参照した型チェックが可能
    # 共通プロシージャを呼び出し可能
    # マクロを使用可能
```

---

**バージョン**: 1.1.0  
**最終更新**: 2024-12-20  
**ステータス**: ドラフト

