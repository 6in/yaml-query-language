# YQL Playground 実装提案

## 概要

PythonのWASM実装（Pyodide）を利用して、ブラウザ上でYQLを試せるPlaygroundツールを作成します。

## 技術選定

### 推奨: Pyodide

**Pyodide**は、CPythonインタープリタをWebAssemblyにコンパイルしたプロジェクトで、ブラウザ上でPythonコードを直接実行できます。

**メリット:**
- サーバーサイド不要（完全にクライアントサイドで動作）
- 標準的なPython環境（CPython互換）
- PyYAMLなどの主要ライブラリが利用可能
- CDNから簡単に読み込める
- アクティブに開発・メンテナンスされている

**デメリット:**
- 初期ロード時間が長い（~10MB）
- 実行速度がネイティブより3～5倍遅い
- すべてのPythonパッケージが利用可能ではない

### 代替案

- **PyScript**: Pyodideをベースにしたフレームワーク（HTML内に直接Pythonコードを記述可能）
- **JupyterLite**: Jupyter Notebookの軽量版（より高機能だが複雑）

## 実装アーキテクチャ

### 1. 基本的な構成

```
playground/
├── index.html          # メインHTML
├── playground.js       # JavaScriptロジック
├── playground.css      # スタイリング
└── yql-code.js        # YQL Pythonコード（文字列として埋め込み）
```

### 2. 実装の流れ

1. **Pyodideの読み込み**
   ```html
   <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
   ```

2. **Pyodideの初期化**
   ```javascript
   let pyodide;
   async function initPyodide() {
       pyodide = await loadPyodide({
           indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
       });
       
       // PyYAMLをインストール
       await pyodide.loadPackage("pyyaml");
       
       // YQLモジュールを読み込む
       await loadYQLModule();
   }
   ```

3. **YQLモジュールの読み込み**

   方法A: ソースコードを文字列として埋め込み
   ```javascript
   async function loadYQLModule() {
       // YQLのPythonソースコードを文字列として読み込む
       const yqlCode = await fetch('yql-module.py').then(r => r.text());
       
       // Pyodideのファイルシステムに書き込む
       pyodide.FS.writeFile('/yql/__init__.py', yqlCode);
       pyodide.FS.writeFile('/yql/parser.py', parserCode);
       pyodide.FS.writeFile('/yql/generator/__init__.py', generatorCode);
       // ... 他のモジュール
       
       // Pythonパスに追加
       pyodide.runPython(`
           import sys
           sys.path.insert(0, '/')
           import yql
       `);
   }
   ```

   方法B: バンドルされたモジュールを読み込む（推奨）
   ```javascript
   async function loadYQLModule() {
       // すべてのYQLモジュールを1つのファイルにまとめる
       const yqlBundle = await fetch('yql-bundle.py').then(r => r.text());
       pyodide.runPython(yqlBundle);
   }
   ```

4. **YQLコードの実行**
   ```javascript
   async function runYQL(yqlCode, dialect = 'postgresql') {
       const pythonCode = `
from yql import parse, generate_sql, Dialect

yql_content = ${JSON.stringify(yqlCode)}
dialect = Dialect.${dialect.toUpperCase()}

try:
    query = parse(yql_content)
    sql = generate_sql(query, dialect)
    print(sql)
except Exception as e:
    print(f"Error: {e}")
       `;
       
       const result = pyodide.runPython(pythonCode);
       return result;
   }
   ```

### 3. UI構成

```
┌─────────────────────────────────────────┐
│  YQL Playground                         │
├─────────────────────────────────────────┤
│  [Dialect: PostgreSQL ▼] [Run] [Clear] │
├─────────────────────────────────────────┤
│  YQL Editor (左側)                      │
│  ┌─────────────────────────────────┐   │
│  │ query:                          │   │
│  │   select:                       │   │
│  │     - id: c.id                  │   │
│  │   from: { c: customers }        │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  Generated SQL (右側)                   │
│  ┌─────────────────────────────────┐   │
│  │ SELECT c.id AS id               │   │
│  │ FROM customers c                │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 実装の詳細

### ステップ1: YQLモジュールのバンドル

YQLのPython実装を1つのファイルにまとめるスクリプトを作成：

```python
# scripts/bundle_yql.py
import os
import re

def bundle_yql_modules():
    """YQLモジュールを1つのファイルにまとめる"""
    src_dir = "src/yql"
    output = []
    
    # モジュールを順番に読み込む
    modules = [
        "ast.py",
        "parser.py",
        "generator/base.py",
        "generator/postgresql.py",
        "generator/mysql.py",
        "generator/sqlserver.py",
        "generator/oracle.py",
        "__init__.py",
    ]
    
    for module in modules:
        path = os.path.join(src_dir, module)
        with open(path, 'r') as f:
            content = f.read()
            # import文を調整（相対importを絶対importに）
            content = re.sub(r'from \.(\w+) import', r'from yql.\1 import', content)
            output.append(f"# === {module} ===\n{content}\n")
    
    return "\n".join(output)
```

### ステップ2: HTML/JavaScript実装

```html
<!DOCTYPE html>
<html>
<head>
    <title>YQL Playground</title>
    <link rel="stylesheet" href="playground.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>YQL Playground</h1>
            <div class="controls">
                <select id="dialect">
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                    <option value="sqlserver">SQL Server</option>
                    <option value="oracle">Oracle</option>
                </select>
                <button id="run-btn">Run</button>
                <button id="clear-btn">Clear</button>
            </div>
        </header>
        
        <div class="editor-container">
            <div class="editor-panel">
                <h2>YQL</h2>
                <textarea id="yql-editor" placeholder="Enter YQL code here..."></textarea>
            </div>
            <div class="result-panel">
                <h2>Generated SQL</h2>
                <pre id="sql-output"></pre>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
    <script src="playground.js"></script>
</body>
</html>
```

```javascript
// playground.js
let pyodide;
let yqlModuleLoaded = false;

async function init() {
    // Pyodideの初期化
    pyodide = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
    });
    
    // PyYAMLのインストール
    await pyodide.loadPackage("pyyaml");
    
    // YQLモジュールの読み込み
    await loadYQLModule();
    
    // UIイベントの設定
    document.getElementById('run-btn').addEventListener('click', runYQL);
    document.getElementById('clear-btn').addEventListener('click', clearEditor);
}

async function loadYQLModule() {
    // YQLバンドルファイルを読み込む
    const response = await fetch('yql-bundle.py');
    const yqlCode = await response.text();
    
    // Pyodideで実行
    pyodide.runPython(yqlCode);
    yqlModuleLoaded = true;
    
    console.log('YQL module loaded');
}

async function runYQL() {
    if (!yqlModuleLoaded) {
        alert('YQL module is still loading...');
        return;
    }
    
    const yqlCode = document.getElementById('yql-editor').value;
    const dialect = document.getElementById('dialect').value;
    
    const pythonCode = `
from yql import parse, generate_sql, Dialect
import json

yql_content = ${JSON.stringify(yqlCode)}
dialect_name = ${JSON.stringify(dialect)}

try:
    query = parse(yql_content)
    dialect_enum = getattr(Dialect, dialect_name.upper())
    sql = generate_sql(query, dialect_enum)
    result = {"status": "success", "sql": sql}
except Exception as e:
    result = {"status": "error", "message": str(e)}

json.dumps(result)
    `;
    
    try {
        const resultJson = pyodide.runPython(pythonCode);
        const result = JSON.parse(resultJson);
        
        const output = document.getElementById('sql-output');
        if (result.status === 'success') {
            output.textContent = result.sql;
            output.className = 'success';
        } else {
            output.textContent = `Error: ${result.message}`;
            output.className = 'error';
        }
    } catch (error) {
        document.getElementById('sql-output').textContent = `Error: ${error.message}`;
    }
}

function clearEditor() {
    document.getElementById('yql-editor').value = '';
    document.getElementById('sql-output').textContent = '';
}

// 初期化
init();
```

## 実装の課題と解決策

### 課題1: モジュールの依存関係

**問題**: YQLモジュールは複数のファイルに分かれており、相対importを使用している。

**解決策**: 
- バンドルスクリプトで1つのファイルにまとめる
- 相対importを絶対importに変換

### 課題2: 初期ロード時間

**問題**: Pyodideの初期ロードに時間がかかる（~10秒）。

**解決策**:
- ローディングインジケーターを表示
- プログレスバーで進捗を表示
- Service Workerでキャッシュ

### 課題3: エラーハンドリング

**問題**: Pythonのエラーを適切に表示する必要がある。

**解決策**:
- try-exceptでエラーをキャッチ
- エラーメッセージをJSONで返す
- シンタックスハイライトでエラー行を強調

## 次のステップ

1. **プロトタイプの作成**
   - 最小限の機能で動作確認
   - YQLの基本的なSELECT文を実行

2. **UIの改善**
   - コードエディタ（Monaco EditorやCodeMirror）
   - シンタックスハイライト
   - エラーメッセージの改善

3. **機能拡張**
   - サンプルYQLの選択
   - SQLのコピー機能
   - 複数データベースの比較表示

4. **パフォーマンス最適化**
   - モジュールの遅延ロード
   - キャッシュの活用

## 参考リンク

- [Pyodide公式ドキュメント](https://pyodide.org/en/stable/)
- [Pyodide CDN](https://cdn.jsdelivr.net/pyodide/)
- [PyScript公式サイト](https://pyscript.net/)

