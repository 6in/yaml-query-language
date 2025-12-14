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

### パフォーマンスの目安

Pyodideを使う際のパフォーマンス目安を理解しておくことは重要です：

- **初期化時間**: 約10-20秒（初回ロード時、インターネット接続に依存）
- **モジュール読み込み時間**: バンドルサイズに依存（1MBで約1-2秒）
- **実行時のパフォーマンス**: ネイティブPythonの約1/3-1/5程度
- **メモリ使用量**: 初期で約20-30MB、モジュール読み込み後は追加で10-50MB

これらの数値は目安であり、実際の環境やモジュールの複雑さによって変動します。

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

## 解決策：モジュールのバンドル方法

**注意**: この記事を執筆した時点では、Pyodide公式の`pyodide-pack`ツールの存在を知らず、手動でtar.gzを作成する方法を採用しました。後から`pyodide-pack`の存在を知り、調査を行いました。この記事では、**手動tar.gz方式**を詳しく説明しますが、公式ツールである**`pyodide-pack`**も選択肢として紹介します。

Pyodideでカスタムモジュールを読み込む方法は、主に2つあります：

1. **手動でtar.gzを作成する方法**（この記事で説明）
2. **`pyodide-pack`を使う方法**（公式ツール）

### 方法の比較

| 方法 | メリット | デメリット | 適用場面 |
|------|---------|-----------|---------|
| **手動tar.gz** | シンプル、制御しやすい、依存関係が少ない | 手動で管理が必要 | 小規模なモジュール、学習目的 |
| **pyodide-pack** | 依存関係を自動検出、最適化されたバンドル | セットアップがやや複雑 | 本番環境、大規模なプロジェクト |

**推奨**: 小規模なモジュールや学習目的では手動tar.gz、本番環境や大規模なプロジェクトでは`pyodide-pack`を使用することを推奨します。

### pyodide-packについて

[`pyodide-pack`](https://pypi.org/project/pyodide-pack/)は、Pyodide公式のバンドルツールです。使用するモジュールを自動検出し、最適化されたバンドルを作成します。

```bash
# インストール
pip install pyodide-pack

# バンドルの作成
pyodide-pack build mymodule
```

詳細は[pyodide-pack公式ドキュメント](https://pypi.org/project/pyodide-pack/)を参照してください。

---

## 方法1: 手動でtar.gzを作成する方法

### 1. Pythonモジュールをtar.gzにバンドルする

まず、Pythonモジュールを`tar.gz`アーカイブにまとめるスクリプトを作成します。

<details>
<summary>バンドルスクリプトの完全なコードを見る</summary>

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

</details>

**重要なポイント**：

- `arcname`は、モジュール構造を保持するために`src/`からの相対パスを使用します
- これにより、`import mymodule`や`from mymodule.generator import base`が正しく動作します

### 2. バンドルスクリプトの実行

```bash
python3 bundle_modules.py
```

これで`mymodule-bundle.tar.gz`が生成されます。このファイルをWebサーバーに配置します。

---

## 方法2: pyodide-packを使う方法（参考）

[`pyodide-pack`](https://pypi.org/project/pyodide-pack/)は、Pyodide公式のバンドルツールです。使用するモジュールを自動検出し、最適化されたバンドルを作成します。

```bash
# インストール
pip install pyodide-pack

# バンドルの作成（エントリーポイントを指定）
pyodide-pack build mymodule --entrypoint mymodule.main:run

# 生成されたバンドルをWebサーバーに配置
# dist/mymodule.whl が生成される
```

ブラウザでの読み込み：

```javascript
// micropipでwheelファイルをインストール
await pyodide.loadPackage("micropip");
await pyodide.runPythonAsync(`
import micropip
await micropip.install('./mymodule.whl')
`);
```

**注意**: `pyodide-pack`は比較的新しいツールで、セットアップがやや複雑な場合があります。詳細は[pyodide-pack公式ドキュメント](https://pypi.org/project/pyodide-pack/)を参照してください。

---

## ブラウザでの読み込み方法（手動tar.gz方式）

### 1. Pyodideの初期化

Pyodideのローダーを待ってから初期化します：

```javascript
let pyodide = await window.loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
});
await pyodide.loadPackage("pyyaml");
```

<details>
<summary>完全な初期化コードを見る</summary>

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

</details>

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
// micropipをロード
await pyodide.loadPackage("micropip");

// Pythonコードでmicropipを使用（runPythonAsyncを使用）
await pyodide.runPythonAsync(`
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
- **パフォーマンス**: ブラウザでダウンロード・インストールするため、時間がかかる場合があります（パッケージサイズに依存、通常は数秒〜数十秒）

**使用例**：

<details>
<summary>micropipの完全な使用例を見る</summary>

```javascript
async function installCustomPackage() {
    // micropipをロード
    await pyodide.loadPackage("micropip");
    
    // Pythonコードでインストール（runPythonAsyncを使用）
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

</details>

**どちらを使うべきか**：

- **`loadPackage()`**: 事前ビルド済みのパッケージ（numpy, pandas, matplotlibなど）や、C拡張を含むパッケージ
- **`micropip`**: 純粋なPythonパッケージで、Pyodideに含まれていないもの

### 2. tar.gzアーカイブの読み込みと展開

`fetch`でtar.gzを取得し、Pyodideの仮想ファイルシステムに展開します：

```javascript
const response = await fetch(`mymodule-bundle.tar.gz?v=${timestamp}`);
const uint8Array = new Uint8Array(await response.arrayBuffer());
pyodide.FS.writeFile('/mymodule-bundle.tar.gz', uint8Array);
pyodide.runPython(`
import tarfile
with tarfile.open('/mymodule-bundle.tar.gz', 'r:gz') as tar:
    tar.extractall('/')
sys.path.insert(0, '/')
import mymodule
`);
```

<details>
<summary>完全な読み込みコードを見る</summary>

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

</details>

**重要なポイント**：

1. **仮想ファイルシステム**: Pyodideは独自の仮想ファイルシステム（VFS）を持っています。`pyodide.FS.writeFile()`でファイルを書き込めます
2. **解凍**: Pythonの`tarfile`モジュールを使って解凍します（Pyodideに標準で含まれています）
3. **sys.path**: `sys.path.insert(0, '/')`で、解凍したモジュールをインポート可能にします

### 3. JavaScriptからPython関数を呼び出す

モジュールが読み込まれたら、JavaScriptからPython関数を呼び出せます。

```javascript
const pythonCode = `
from mymodule import parse
import json
result = parse(${JSON.stringify(input)})
json.dumps(result)
`;
const result = JSON.parse(pyodide.runPython(pythonCode));
```

<details>
<summary>完全な呼び出しコード（エラーハンドリング付き）を見る</summary>

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

</details>

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

<details>
<summary>完全なJavaScriptコードを見る</summary>

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

</details>

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

### 6. パフォーマンスの考慮事項

実運用時には、以下の点を考慮します：

- **初期化時間**: 初回ロード時は10-20秒かかるため、ローディング画面を表示
- **モジュールサイズ**: バンドルサイズを小さく保つ（1MB以下を推奨）
- **遅延読み込み**: 必要なモジュールのみを読み込む
- **キャッシュ戦略**: ブラウザキャッシュを活用して、2回目以降の読み込みを高速化

```javascript
// 遅延読み込みの例
async function loadModuleOnDemand(moduleName) {
    if (!loadedModules.has(moduleName)) {
        await loadPythonModule(moduleName);
        loadedModules.add(moduleName);
    }
}
```

### 7. セキュリティの考慮事項

ブラウザ上でPythonコードを実行する際は、セキュリティに注意が必要です。ただし、Pyodideは**ブラウザのサンドボックス環境**で動作するため、従来のサーバーサイドPythonとは異なる考慮事項があります。

#### Pyodideのセキュリティ特性

PyodideはWebAssemblyで動作し、以下の制限があります：

- **ファイルシステム**: 仮想ファイルシステム内のみアクセス可能（ブラウザ外部のファイルシステムにはアクセス不可）
- **システムコール**: `os.system()`や`subprocess`は動作しない、または制限される
- **ネットワーク**: CORSポリシーに従う（同一オリジンまたは適切なCORSヘッダーが必要）
- **`import os`**: モジュール自体は利用可能だが、システムコールは制限されるため、ローカル環境への影響はない

**重要なポイント**: `import os`などのチェックは**不要**です。ブラウザのサンドボックスにより、ローカル環境への影響はありません。

#### 実際のセキュリティリスク

Pyodideで注意すべき実際のリスクは以下です：

1. **コードインジェクション**: ユーザー入力を直接Pythonコードに埋め込む場合
2. **JavaScript相互運用**: PythonからJavaScriptの機能を呼び出す場合（`js`モジュール）

#### コードインジェクションの防止

ユーザー入力を直接Pythonコードに埋め込まないようにします：

```javascript
// ❌ 危険な例：ユーザー入力を直接埋め込み
const userInput = document.getElementById('input').value;
const pythonCode = `process(${userInput})`;  // コードインジェクションのリスク

// ✅ 安全な例：JSON.stringifyでエスケープ
const pythonCode = `
import json
input_data = ${JSON.stringify(userInput)}  # JSON.stringifyでエスケープ
process(input_data)
`;
```

#### JavaScript相互運用の制限

PythonからJavaScriptの機能を呼び出す場合は、必要最小限に制限します：

```python
# PythonからJavaScriptを呼び出す例
import js
from js import document, console

# 注意：JavaScriptの機能に直接アクセスできる
console.log("Hello from Python")
element = document.getElementById('my-element')
```

**推奨アプローチ**:
- ユーザーが提供するコードを実行する場合は、`js`モジュールへのアクセスを制限する
- 必要に応じて、実行可能なAPIを制限する

## デバッグ方法

### ブラウザの開発者ツールを使う

ブラウザの開発者ツール（F12）を使って、Pythonコードの実行をデバッグできます：

```javascript
// コンソールにPythonの出力を表示
pyodide.runPython(`
import sys
sys.stdout.write = lambda x: console.log(x)
print("This will appear in browser console")
`);

// Pythonのエラーをコンソールに表示
try {
    pyodide.runPython('1 / 0');
} catch (error) {
    console.error('Python error:', error);
}
```

### Pythonコードのデバッグ

Pythonコード内でデバッグ情報を出力します：

```javascript
const pythonCode = `
import json
import traceback

try:
    result = my_function()
    print(f"Debug: result = {result}")  # デバッグ情報
    json.dumps({"status": "success", "data": result})
except Exception as e:
    print(f"Error: {e}")  # エラー情報
    traceback.print_exc()  # スタックトレース
    json.dumps({"status": "error", "message": str(e)})
`;
```

### モジュールのインポート状態を確認

モジュールが正しく読み込まれているか確認します：

```javascript
pyodide.runPython(`
import sys
print("Python path:", sys.path)
print("Loaded modules:", list(sys.modules.keys()))
`);
```

## トラブルシューティング

### Q1: モジュールがインポートできない

**症状**: `ModuleNotFoundError: No module named 'mymodule'`

**原因と解決方法**:

1. **`sys.path`が正しく設定されていない**
   ```javascript
   // 解決方法: sys.pathを確認・修正
   pyodide.runPython(`
   import sys
   print("Current sys.path:", sys.path)
   sys.path.insert(0, '/')  # 必要に応じて追加
   `);
   ```

2. **モジュール構造が正しく保持されていない**
   - バンドルスクリプトで`arcname`が正しく設定されているか確認
   - `file_path.relative_to(MODULE_SRC.parent)`を使用しているか確認

3. **ファイルが正しく解凍されていない**
   ```javascript
   // 解決方法: ファイルシステムの内容を確認
   pyodide.runPython(`
   import os
   print("Files in /:", os.listdir('/'))
   `);
   ```

### Q2: `runPython()`でエラーが発生する

**症状**: `PythonError: ...`

**原因と解決方法**:

1. **構文エラー**
   - Pythonコードの構文を確認
   - ブラウザのコンソールでエラーメッセージを確認

2. **インポートエラー**
   - 必要なモジュールが読み込まれているか確認
   - `loadPackage()`で必要なパッケージをインストール

3. **実行時エラー**
   - エラーメッセージとスタックトレースを確認
   - Pythonコード内で`try-except`を使ってエラーハンドリング

### Q3: パッケージがインストールできない

**症状**: `micropip`でパッケージをインストールできない

**原因と解決方法**:

1. **C拡張を含むパッケージ**
   - `micropip`は純粋なPythonパッケージのみ対応
   - C拡張が必要な場合は、`loadPackage()`で利用可能か確認

2. **互換性の問題**
   - PyPIのパッケージがPyodideと互換性がない可能性
   - 代替パッケージを検討

3. **ネットワークエラー**
   - インターネット接続を確認
   - CORSポリシーに問題がないか確認

### Q4: パフォーマンスが遅い

**症状**: 初期化や実行に時間がかかる

**原因と解決方法**:

1. **初期化時間の短縮**
   - 必要なパッケージのみをインストール
   - バンドルサイズを小さく保つ

2. **実行時間の短縮**
   - 重い処理は非同期で実行
   - キャッシュを活用

3. **メモリ使用量の削減**
   - 不要なモジュールを読み込まない
   - 大きなデータを扱う場合は、チャンクに分割

### Q5: キャッシュの問題

**症状**: 更新したモジュールが反映されない

**原因と解決方法**:

1. **ブラウザキャッシュのクリア**
   - ハードリロード（Ctrl+Shift+R / Cmd+Shift+R）
   - 開発者ツールでキャッシュを無効化

2. **タイムスタンプの追加**
   ```javascript
   const timestamp = new Date().getTime();
   const response = await fetch(`bundle.tar.gz?v=${timestamp}`, {
       cache: 'no-cache'
   });
   ```

### Q6: エラーメッセージが読みにくい

**症状**: Pythonのエラーメッセージが理解しにくい

**解決方法**:

1. **エラーメッセージを整形**
   ```javascript
   function formatPythonError(error) {
       if (error.message.includes('PythonError')) {
           // Pythonのエラーメッセージを抽出
           const match = error.message.match(/PythonError: (.+)/);
           return match ? match[1] : error.message;
       }
       return error.message;
   }
   ```

2. **スタックトレースを表示**
   ```javascript
   const pythonCode = `
   try:
       my_function()
   except Exception as e:
       import traceback
       traceback.print_exc()
   `;
   ```

## まとめ

この記事では、Pyodideを使ってブラウザ上でPythonモジュールを実行する方法を解説しました。

**主なポイント**：

1. **バンドル**: Pythonモジュールを`tar.gz`にまとめる
2. **読み込み**: `fetch`で取得し、Pyodideの仮想ファイルシステムに展開
3. **パッケージ管理**: `loadPackage()`で事前ビルド済みパッケージ、`micropip`でPyPIパッケージをインストール
4. **実行**: `pyodide.runPython()`でPythonコードを実行
5. **データ受け渡し**: JSONを使ってPythonとJavaScript間でデータをやり取り
6. **セキュリティ**: ユーザー入力の検証とコードインジェクションの防止
7. **デバッグ**: ブラウザの開発者ツールとPythonのデバッグ機能を活用
8. **トラブルシューティング**: よくある問題と解決方法

この方法を使えば、複雑なPythonプロジェクトでもブラウザ上で実行できます。Playgroundツール、データ可視化、教育ツールなど、様々な用途に応用できるでしょう。

## 参考リンク

- [Pyodide公式ドキュメント](https://pyodide.org/)
- [Pyodide GitHub](https://github.com/pyodide/pyodide)
- [Pyodide Packages](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)
- [pyodide-pack](https://pypi.org/project/pyodide-pack/) - Pyodide公式のバンドルツール
- [WebAssembly](https://webassembly.org/)

