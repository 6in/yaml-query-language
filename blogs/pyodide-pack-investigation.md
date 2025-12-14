# pyodide-pack 調査レポート

## 調査目的

Playgroundで`pyodide-pack`を使用できるかどうかを調査し、現在の手動tar.gz方式との比較を行う。

## 調査結果

### pyodide-packとは

`pyodide-pack`は、Pyodide公式のバンドルツールです。Pythonアプリケーションを実行し、使用されるモジュールを自動検出して、最小限のバンドルを作成します。

### インストール

```bash
pip install pyodide-pack
```

インストールは成功しました。

### 使用方法

`pyodide-pack`は以下のような仕組みで動作します：

1. **エントリーポイント**: 実行するPythonスクリプトを指定
2. **Node.js環境での実行**: 指定したスクリプトをNode.js環境で実行し、使用されるモジュールを検出
3. **バンドル生成**: 検出されたモジュールと依存関係をバンドルにまとめる

### 実際の試行結果

#### 1. コマンドライン実行

```bash
pyodide pack test_yql_import.py
```

**問題点**:
- `pyodide`コマンドは存在するが、`pack`サブコマンドでエラーが発生
- バージョン互換性の問題がある可能性

#### 2. Python APIからの実行

```python
from pyodide_pack.cli import main
from pathlib import Path
main(Path('test_yql_import.py'), requirement_path=Path('requirements.txt'))
```

**問題点**:
- Node.js環境とPyodideパッケージが必要
- `discovery.js`テンプレートファイルが見つからない
- セットアップが複雑

### 必要な環境

`pyodide-pack`を使用するには以下が必要です：

1. **Node.js**: Node.js環境が必要
2. **Pyodideパッケージ**: `node_modules/pyodide`が必要
3. **requirements.txt**: 依存関係を記載したファイル
4. **エントリーポイント**: 実行するPythonスクリプト

### 現在の手動tar.gz方式との比較

| 項目 | 手動tar.gz方式 | pyodide-pack方式 |
|------|---------------|------------------|
| **セットアップ** | シンプル（Pythonのみ） | 複雑（Node.js + Pyodideパッケージ） |
| **依存関係の検出** | 手動 | 自動 |
| **バンドルサイズ** | 全ファイルを含む | 最適化された最小バンドル |
| **動作確認** | ✅ 動作確認済み | ⚠️ セットアップ未完了 |
| **メンテナンス** | 手動管理が必要 | 自動化可能 |

### 結論

**現時点での推奨**:

1. **Playgroundでの使用**: 現時点では**手動tar.gz方式を継続**することを推奨
   - シンプルで確実に動作する
   - セットアップが不要
   - 既に動作確認済み

2. **pyodide-packの導入**: 将来的に検討可能
   - Node.js環境のセットアップが必要
   - Pyodideパッケージの準備が必要
   - より最適化されたバンドルが期待できる

### 次のステップ（pyodide-packを試す場合）

1. **Node.js環境のセットアップ**
   ```bash
   npm install pyodide
   ```

2. **Pyodideパッケージの準備**
   - `node_modules/pyodide`ディレクトリが必要

3. **エントリーポイントスクリプトの作成**
   - YQLモジュールを使用するテストスクリプト

4. **バンドルの生成とテスト**
   - 生成されたバンドルをPlaygroundで読み込む
   - 動作確認

### 参考情報

- [pyodide-pack PyPI](https://pypi.org/project/pyodide-pack/)
- `pyodide-pack`は比較的新しいツール（v0.2.0）
- ドキュメントがまだ不十分な可能性

