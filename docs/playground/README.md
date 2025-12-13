# YQL Playground

ブラウザ上でYQLを試せるPlaygroundツールです。Pyodideを使用して、サーバーサイドなしでPythonコードを実行します。

## アクセス

GitHub Pagesで公開されている場合は、以下のURLからアクセスできます：

```
https://[username].github.io/[repo-name]/playground/
```

## 機能

- YQLコードの編集と実行
- 複数データベース（PostgreSQL, MySQL, SQL Server, Oracle）へのSQL変換
- リアルタイムでのSQL生成結果の表示
- エラーメッセージの表示

## 使い方

1. ブラウザでPlaygroundを開く
2. YQLコードを入力（またはサンプルを選択）
3. データベースを選択
4. "Run" ボタンをクリック
5. 生成されたSQLを確認

## 開発

### ローカル開発

```bash
cd implementations/playground
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000` にアクセス

### バンドルの再生成

YQL Pythonモジュールを更新した場合は、以下のコマンドでバンドルを再生成してください：

```bash
cd implementations/playground
python3 bundle_yql_tar.py
```

その後、`yql-bundle.tar.gz`を`docs/playground/`にコピーしてください。

## GitHub Pagesでの公開

### 手動デプロイ

1. `implementations/playground/`のファイルを`docs/playground/`にコピー
2. GitHubリポジトリのSettings > Pagesで以下を設定：
   - Source: `Deploy from a branch`
   - Branch: `main` (または`master`)
   - Folder: `/docs`
3. 保存後、数分で `https://[username].github.io/[repo-name]/playground/` でアクセス可能になります

### 自動デプロイ（GitHub Actions）

`.github/workflows/deploy-playground.yml`が設定されている場合、`implementations/playground/`または`implementations/python/src/yql/`に変更をプッシュすると自動的にデプロイされます。

初回のみ、GitHubリポジトリのSettings > Pagesで以下を設定してください：
- Source: `GitHub Actions`

## 技術スタック

- **Pyodide**: PythonのWebAssembly実装
- **PyYAML**: YAMLパーサー（Pyodide経由で利用）
- **Monaco Editor**: コードエディタ

## 注意事項

- 初回ロードに時間がかかります（~10秒）
- インターネット接続が必要です（CDNからPyodideを読み込みます）

