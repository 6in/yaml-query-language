# ブラウザでPythonを動かす：Pyodideを使った実践的な実装ガイド

## はじめに

ブラウザ上でPythonコードを実行したい。そんなニーズは、Playgroundツール、データ可視化、教育ツールなど、様々な場面で発生します。この記事では、**Pyodide**を使ってブラウザ上でPythonモジュールを実行するための実践的な実装方法を解説します。

特に、複数のPythonモジュールから構成されるプロジェクトをブラウザで動かすための、**モジュールのバンドル方法**と**読み込み方法**に焦点を当てます。

## 実装の全体像

ブラウザでPythonモジュールを実行するには、以下の手順を踏みます：

### 実装手順のサマリ

1. **Pythonモジュールのバンドル**
   - 複数の`.py`ファイルを`tar.gz`アーカイブにまとめる
   - モジュール構造（ディレクトリ階層）を保持する

2. **Pyodideの初期化**
   - Pyodideのローダーを読み込む
   - Pyodideランタイムを初期化
   - 必要なパッケージをインストール（`loadPackage()`または`micropip`）

3. **モジュールの読み込み**
   - `fetch`で`tar.gz`ファイルを取得
   - Pyodideの仮想ファイルシステムに書き込み
   - Pythonで解凍して`sys.path`に追加

4. **JavaScriptからPythonの呼び出し**
   - `pyodide.runPython()`でPythonコードを実行
   - JSONでデータをやり取り
   - エラーハンドリング

### 全体の流れ

```
[開発環境]
  ↓
1. Pythonモジュールをtar.gzにバンドル
  ↓
[Webサーバー]
  ↓
2. HTML/JavaScriptでPyodideを初期化
  ↓
3. tar.gzをfetchで取得
  ↓
4. 仮想ファイルシステムに展開
  ↓
5. Pythonモジュールをインポート
  ↓
6. JavaScriptからPython関数を呼び出し
```

この記事では、各ステップを順を追って詳しく解説します。

## Pyodideとは

[Pyodide](https://pyodide.org/)は、CPythonをWebAssemblyにコンパイルしたプロジェクトです。これにより、ブラウザ上でPythonコードを実行できるようになります。

### 基本的な使い方

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
<script>
  async function main() {
    let pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
    });
    console.log(pyodide.runPython("import sys; sys.version"));
  }
  main();
</script>
```

しかし、実際のプロジェクトでは、単純なPythonコードだけでなく、**複数のモジュールから構成されるパッケージ**を動かしたいことが多いでしょう。

## 課題：複数モジュールの読み込み

例えば、以下のような構造のPythonプロジェクトがあるとします：

```
myproject/
├── src/
│   └── mymodule/
│       ├── __init__.py
│       ├── parser.py
│       └── generator/
│           ├── __init__.py
│           └── base.py
```

このような構造をブラウザで動かすには、以下の課題があります：

1. **モジュール構造の保持**: 相対インポート（`from .generator import base`）が動作する必要がある
2. **ファイルの配布**: 複数の`.py`ファイルを効率的に配布する必要がある
3. **読み込み方法**: Pyodideの仮想ファイルシステムに正しく配置する必要がある

## 解決策：tar.gzアーカイブを使ったバンドル

### 1. Pythonモジュールをtar.gzにバンドルする

まず、Pythonモジュールを`tar.gz`アーカイブにまとめるスクリプトを作成します。

```python
#!/usr/bin/env python3
"""Bundle Python modules into a tar.gz file for Pyodide."""

import tarfile
from pathlib import Path

# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODULE_SRC = PROJECT_ROOT / "src" / "mymodule"
OUTPUT_FILE = Path(__file__).parent / "mymodule-bundle.tar.gz"


def bundle_modules():
    """モジュールをtar.gzにまとめる"""
    print(f"Bundling modules from {MODULE_SRC}...")
    
    with tarfile.open(OUTPUT_FILE, 'w:gz') as tar:
        # モジュールディレクトリ内のすべての.pyファイルを追加
        for file_path in MODULE_SRC.rglob('*.py'):
            # アーカイブ内のパス: mymodule/__init__.py, mymodule/generator/base.py など
            # モジュール構造を保持するため、src/からの相対パスを使用
            arcname = file_path.relative_to(MODULE_SRC.parent)
            tar.add(file_path, arcname=arcname)
            print(f"  Added: {arcname}")
    
    print(f"✅ Bundled modules to {OUTPUT_FILE}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size} bytes")


if __name__ == "__main__":
    bundle_modules()
```

**重要なポイント**：

- `arcname`は、モジュール構造を保持するために`src/`からの相対パスを使用します
- これにより、`import mymodule`や`from mymodule.generator import base`が正しく動作します

### 2. バンドルスクリプトの実行

```bash
python3 bundle_modules.py
```

これで`mymodule-bundle.tar.gz`が生成されます。このファイルをWebサーバーに配置します。

## ブラウザでの読み込み方法

### 1. Pyodideの初期化

```javascript
let pyodide;

async function initPyodide() {
    // Pyodideのローダーを待つ
    while (typeof window.loadPyodide === 'undefined') {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Pyodideの初期化
    pyodide = await window.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
    });
    
    // 必要なパッケージをインストール（例: PyYAML）
    await pyodide.loadPackage("pyyaml");
    
    console.log('Pyodide initialized');
}
```

### パッケージのインストール方法

Pyodideには、パッケージをインストールする方法が2つあります：

#### 方法1: `loadPackage()` - 事前ビルド済みパッケージ

Pyodideに事前にビルド済みのパッケージをインストールする方法です。主にC拡張を含むパッケージや、よく使われるパッケージが対象です。

```javascript
// 単一パッケージ
await pyodide.loadPackage("numpy");

// 複数パッケージ
await pyodide.loadPackage(["numpy", "pandas", "matplotlib"]);
```

**利用可能なパッケージ**: [Pyodide Packages](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) を参照

#### 方法2: `micropip` - PyPIからのインストール

`micropip`を使うと、PyPIから純粋なPythonパッケージをインストールできます。これは、Pyodideに事前ビルドされていないパッケージを追加する際に便利です。

```javascript
// micropipをインポート
await pyodide.loadPackage("micropip");

// Pythonコードでmicropipを使用
pyodide.runPython(`
import micropip
await micropip.install('requests')
await micropip.install('beautifulsoup4')
`);

// または、JavaScriptから直接呼び出す
const micropip = pyodide.pyimport("micropip");
await micropip.install("requests");
```

**micropipの制限事項**：

- **純粋なPythonパッケージのみ**: C拡張を含むパッケージはインストールできません
- **互換性**: すべてのPyPIパッケージが動作するわけではありません
- **パフォーマンス**: ブラウザでダウンロード・インストールするため、時間がかかる場合があります

**使用例**：

```javascript
async function installCustomPackage() {
    // micropipをロード
    await pyodide.loadPackage("micropip");
    
    // Pythonコードでインストール
    await pyodide.runPythonAsync(`
import micropip
await micropip.install('python-dateutil')
    `);
    
    // インストール後、使用可能
    pyodide.runPython(`
from dateutil import parser
date = parser.parse("2024-01-01")
print(date)
    `);
}
```

**どちらを使うべきか**：

- **`loadPackage()`**: 事前ビルド済みのパッケージ（numpy, pandas, matplotlibなど）や、C拡張を含むパッケージ
- **`micropip`**: 純粋なPythonパッケージで、Pyodideに含まれていないもの

### 2. tar.gzアーカイブの読み込みと展開

```javascript
async function loadPythonModule() {
    try {
        // tar.gzファイルをfetchで読み込む
        // キャッシュ回避のためタイムスタンプを追加
        const timestamp = new Date().getTime();
        const response = await fetch(`mymodule-bundle.tar.gz?v=${timestamp}`, {
            cache: 'no-cache'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load bundle: ${response.statusText}`);
        }
        
        // ArrayBufferに変換
        const arrayBuffer = await response.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        
        // Pyodideの仮想ファイルシステムにtar.gzを書き込む
        pyodide.FS.writeFile('/mymodule-bundle.tar.gz', uint8Array);
        
        // Pythonでtar.gzを解凍して仮想ファイルシステムに展開
        pyodide.runPython(`
import tarfile
import sys

# tar.gzを解凍
with tarfile.open('/mymodule-bundle.tar.gz', 'r:gz') as tar:
    tar.extractall('/')

# sys.pathに追加（srcディレクトリを追加）
# これにより、import mymoduleが動作する
sys.path.insert(0, '/')

# モジュールをインポートして確認
import mymodule
print(f'✅ Module loaded: {mymodule.__name__}')
        `);
        
        console.log('✅ Python module loaded');
    } catch (error) {
        console.error('Error loading Python module:', error);
        throw error;
    }
}
```

**重要なポイント**：

1. **仮想ファイルシステム**: Pyodideは独自の仮想ファイルシステム（VFS）を持っています。`pyodide.FS.writeFile()`でファイルを書き込めます
2. **解凍**: Pythonの`tarfile`モジュールを使って解凍します（Pyodideに標準で含まれています）
3. **sys.path**: `sys.path.insert(0, '/')`で、解凍したモジュールをインポート可能にします

### 3. JavaScriptからPython関数を呼び出す

モジュールが読み込まれたら、JavaScriptからPython関数を呼び出せます。

```javascript
async function callPythonFunction(input) {
    try {
        // Pythonコードを文字列として構築
        const pythonCode = `
from mymodule import parse, generate_output
import json

input_data = ${JSON.stringify(input)}

try:
    result = parse(input_data)
    output = generate_output(result)
    result_dict = {"status": "success", "output": output}
except Exception as e:
    import traceback
    result_dict = {
        "status": "error",
        "message": str(e),
        "traceback": traceback.format_exc()
    }

json.dumps(result_dict)
        `;
        
        // Pythonコードを実行
        const resultJson = pyodide.runPython(pythonCode);
        const result = JSON.parse(resultJson);
        
        if (result.status === 'success') {
            return result.output;
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Python execution error:', error);
        throw error;
    }
}
```

**重要なポイント**：

1. **JSONでのデータ受け渡し**: PythonとJavaScript間でデータをやり取りするには、JSONを使います
2. **エラーハンドリング**: Pythonの例外をキャッチして、JavaScript側に伝えます
3. **文字列エスケープ**: `JSON.stringify()`を使って、JavaScriptの文字列をPythonコードに埋め込みます

## 完全な実装例

以下は、実際に動作する完全な例です。

### HTML

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Python in Browser</title>
</head>
<body>
    <h1>Python Module Runner</h1>
    <button id="run-btn">Run Python</button>
    <pre id="output"></pre>
    
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <script src="app.js"></script>
</body>
</html>
```

### JavaScript (app.js)

```javascript
let pyodide;
let moduleLoaded = false;

// 初期化
async function init() {
    // Pyodideのローダーを待つ
    while (typeof window.loadPyodide === 'undefined') {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Pyodideの初期化
    pyodide = await window.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
    });
    
    // 必要なパッケージをインストール
    // 方法1: 事前ビルド済みパッケージ
    await pyodide.loadPackage("pyyaml");
    
    // 方法2: micropipでPyPIからインストール（必要に応じて）
    // await pyodide.loadPackage("micropip");
    // await pyodide.runPythonAsync(`
    //     import micropip
    //     await micropip.install('requests')
    // `);
    
    // Pythonモジュールを読み込む
    await loadPythonModule();
    
    moduleLoaded = true;
    console.log('✅ Initialization complete');
}

// Pythonモジュールの読み込み
async function loadPythonModule() {
    const timestamp = new Date().getTime();
    const response = await fetch(`mymodule-bundle.tar.gz?v=${timestamp}`, {
        cache: 'no-cache'
    });
    
    if (!response.ok) {
        throw new Error(`Failed to load bundle: ${response.statusText}`);
    }
    
    const arrayBuffer = await response.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    
    pyodide.FS.writeFile('/mymodule-bundle.tar.gz', uint8Array);
    
    pyodide.runPython(`
import tarfile
import sys

with tarfile.open('/mymodule-bundle.tar.gz', 'r:gz') as tar:
    tar.extractall('/')

sys.path.insert(0, '/')
import mymodule
print('✅ Module loaded')
    `);
}

// Python関数の呼び出し
async function runPython(input) {
    if (!moduleLoaded) {
        throw new Error('Module not loaded yet');
    }
    
    const pythonCode = `
from mymodule import process
import json

input_data = ${JSON.stringify(input)}
result = process(input_data)
json.dumps(result)
    `;
    
    const resultJson = pyodide.runPython(pythonCode);
    return JSON.parse(resultJson);
}

// イベントハンドラ
document.getElementById('run-btn').addEventListener('click', async () => {
    const output = document.getElementById('output');
    output.textContent = 'Running...';
    
    try {
        const result = await runPython({ data: 'test' });
        output.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
        output.textContent = `Error: ${error.message}`;
    }
});

// 初期化を開始
init();
```

## ベストプラクティス

### 1. キャッシュ対策

ブラウザのキャッシュを回避するため、タイムスタンプをクエリパラメータに追加します：

```javascript
const timestamp = new Date().getTime();
const response = await fetch(`bundle.tar.gz?v=${timestamp}`, {
    cache: 'no-cache'
});
```

### 2. エラーハンドリング

Pythonのエラーを適切に処理します：

```javascript
const pythonCode = `
try:
    result = my_function()
    json.dumps({"status": "success", "data": result})
except Exception as e:
    import traceback
    json.dumps({
        "status": "error",
        "message": str(e),
        "traceback": traceback.format_exc()
    })
`;
```

### 3. ローディング状態の表示

Pyodideの初期化には時間がかかるため、ローディング状態を表示します：

```javascript
async function init() {
    showLoading('Initializing Pyodide...');
    pyodide = await loadPyodide({...});
    
    showLoading('Loading packages...');
    await pyodide.loadPackage("pyyaml");
    
    showLoading('Loading modules...');
    await loadPythonModule();
    
    hideLoading();
}
```

### 4. モジュール構造の保持

バンドル時に、モジュール構造を正しく保持します：

```python
# 正しい例：モジュール構造を保持
arcname = file_path.relative_to(MODULE_SRC.parent)  # src/mymodule/...

# 間違った例：構造が崩れる
arcname = file_path.name  # __init__.py, base.py など（構造が失われる）
```

### 5. パッケージインストールの選択

パッケージをインストールする際は、用途に応じて適切な方法を選択します：

```javascript
// 事前ビルド済みパッケージ（推奨）
// - 高速
// - C拡張を含むパッケージも利用可能
// - ただし、利用可能なパッケージが限られる
await pyodide.loadPackage("numpy");

// micropip（補完的に使用）
// - PyPIからインストール可能
// - ただし、純粋なPythonパッケージのみ
// - インストールに時間がかかる場合がある
await pyodide.loadPackage("micropip");
await pyodide.runPythonAsync(`
    import micropip
    await micropip.install('requests')
`);
```

**推奨アプローチ**：

1. まず`loadPackage()`で利用可能か確認
2. 利用できない場合のみ`micropip`を使用
3. 頻繁に使うパッケージは、バンドルに含めることを検討

## まとめ

この記事では、Pyodideを使ってブラウザ上でPythonモジュールを実行する方法を解説しました。

**主なポイント**：

1. **バンドル**: Pythonモジュールを`tar.gz`にまとめる
2. **読み込み**: `fetch`で取得し、Pyodideの仮想ファイルシステムに展開
3. **パッケージ管理**: `loadPackage()`で事前ビルド済みパッケージ、`micropip`でPyPIパッケージをインストール
4. **実行**: `pyodide.runPython()`でPythonコードを実行
5. **データ受け渡し**: JSONを使ってPythonとJavaScript間でデータをやり取り

この方法を使えば、複雑なPythonプロジェクトでもブラウザ上で実行できます。Playgroundツール、データ可視化、教育ツールなど、様々な用途に応用できるでしょう。

## 参考リンク

- [Pyodide公式ドキュメント](https://pyodide.org/)
- [Pyodide GitHub](https://github.com/pyodide/pyodide)
- [WebAssembly](https://webassembly.org/)

