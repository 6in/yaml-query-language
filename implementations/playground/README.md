# YQL Playground

ブラウザ上でYQLを試せるPlaygroundツールです。Pyodideを使用して、サーバーサイドなしでPythonコードを実行します。

## 機能

- YQLコードの編集と実行
- 複数データベース（PostgreSQL, MySQL, SQL Server, Oracle）へのSQL変換
- リアルタイムでのSQL生成結果の表示
- エラーメッセージの表示

## 使い方

1. `index.html` をブラウザで開く
2. YQLコードを入力
3. データベースを選択
4. "Run" ボタンをクリック
5. 生成されたSQLを確認

## 開発

### ローカル開発サーバー

```bash
# Python 3の場合
python -m http.server 8000

# Node.jsの場合
npx serve .
```

ブラウザで `http://localhost:8000` にアクセス

### ファイル構成

```
playground/
├── index.html              # メインHTML
├── playground.js           # JavaScriptロジック
├── playground.css          # スタイリング
├── bundle_yql_tar.py       # YQL Pythonモジュールをtar.gzにバンドルするスクリプト
├── yql-bundle.tar.gz       # YQL Pythonモジュール（バンドル済み）
└── README.md               # このファイル
```

### バンドルの再生成

YQL Pythonモジュールを更新した場合は、以下のコマンドでバンドルを再生成してください：

```bash
cd implementations/playground
python3 bundle_yql_tar.py
```

## 技術スタック

- **Pyodide**: PythonのWebAssembly実装
- **PyYAML**: YAMLパーサー（Pyodide経由で利用）

## GitHub Pagesでの公開

詳細は [`docs/playground/README.md`](../../docs/playground/README.md) を参照してください。

### クイックスタート

1. GitHubリポジトリのSettings > Pagesで以下を設定：
   - Source: `Deploy from a branch` → Branch: `main`, Folder: `/docs`
   - または Source: `GitHub Actions`（自動デプロイを使用する場合）

2. 数分後、`https://[username].github.io/[repo-name]/playground/` でアクセス可能になります

## 注意事項

- 初回ロードに時間がかかります（~10秒）
- インターネット接続が必要です（CDNからPyodideを読み込みます）

