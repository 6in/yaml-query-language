---
layout: default
title: Deployment
---

# GitHub Pages デプロイ手順

## 方法1: 自動デプロイ（推奨）

GitHub Actionsを使用して自動デプロイする方法です。

### 初回設定

1. GitHubリポジトリの **Settings** > **Pages** に移動
2. **Source** を `GitHub Actions` に設定
3. 保存

### 自動デプロイの動作

以下のファイルが変更されると、自動的にデプロイが実行されます：

- `implementations/playground/**` - Playgroundのファイル
- `implementations/python/src/yql/**` - YQL Pythonモジュール

デプロイは `.github/workflows/deploy-playground.yml` で定義されています。

### デプロイの確認

1. GitHubリポジトリの **Actions** タブでワークフローの実行状況を確認
2. デプロイが完了すると、数分で以下のURLでアクセス可能になります：
   ```
   https://[username].github.io/[repo-name]/playground/
   ```

## 方法2: 手動デプロイ

GitHub Actionsを使用しない場合の手動デプロイ方法です。

### 手順

1. YQLバンドルを再生成（必要に応じて）：
   ```bash
   cd implementations/playground
   python3 bundle_yql_tar.py
   ```

2. Playgroundファイルを`docs/playground/`にコピー：
   ```bash
   cd ../..
   mkdir -p docs/playground
   cp implementations/playground/index.html docs/playground/
   cp implementations/playground/playground.js docs/playground/
   cp implementations/playground/playground.css docs/playground/
   cp implementations/playground/yql-bundle.tar.gz docs/playground/
   ```

3. 変更をコミット・プッシュ：
   ```bash
   git add docs/playground/
   git commit -m "Update playground"
   git push
   ```

4. GitHubリポジトリの **Settings** > **Pages** で以下を設定：
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` (または`master`)
   - **Folder**: `/docs`

5. 数分後、`https://[username].github.io/[repo-name]/playground/` でアクセス可能になります

## トラブルシューティング

### 404エラーが表示される

- GitHub Pagesの設定を確認してください
- デプロイが完了するまで数分かかる場合があります
- ブラウザのキャッシュをクリアしてみてください

### yql-bundle.tar.gzが読み込めない

- `docs/playground/yql-bundle.tar.gz`が存在するか確認してください
- ファイルサイズが大きすぎる場合は、Git LFSを使用することを検討してください

### 自動デプロイが動作しない

- GitHub Actionsのワークフローが有効になっているか確認してください
- リポジトリのSettings > Actions > Generalで、ワークフローの実行が許可されているか確認してください

