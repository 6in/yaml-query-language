# Pyodideブログ トピックサマリ

[Pyodide公式ブログ](https://blog.pyodide.org)の公開日別トピックサマリです。

## 2025年

### October 20, 2025 - Pyodide 0.29 Release
**著者**: Gyeongjae Choi, Hood Chatham, Agriya Khetarpal  
**読了時間**: 4分

**主な変更点**:
- **`toJs()`と`to_js()`のデフォルト動作変更**: 辞書を`Object`に変換するように変更（以前は`Map`）
- 旧動作を使用する場合は`toJsLiteralMap: true`を`loadPyodide()`に渡す
- 将来的には旧動作は削除予定

### August 14, 2025 - JSPI and function pointer cast handling
**著者**: Hood Chatham  
**読了時間**: 6分

**トピック**: JSPI（JavaScript Promise Integration）とEmscriptenの統合
- `wasm32-unknown-emscripten`ターゲットでのJSPI使用
- JavaScriptフレームの問題とその解決方法
- Emscripten環境での実装詳細

### July 4, 2025 - Pyodide 0.28 Release
**著者**: Gyeongjae Choi, Hood Chatham, Agriya Khetarpal  
**読了時間**: 8分

**主な変更点**:
- **Pyodide ABIの標準化**: PEP 776とPEP 783の策定
- CPython 3.14からEmscriptenがtier 3ターゲットとして復帰
- Pythonバージョンごとに1つのABIを定義
- パッケージの互換性向上

### July 3, 2025 - Integrating JSPI with the WebAssembly C Runtime
**著者**: Hood Chatham  
**読了時間**: 10分

**トピック**: JSPIとWebAssembly Cランタイムの統合
- `wasm32-unknown-unknown`ターゲットでのJSPI使用
- CプログラムでのJSPI実装詳細
- libcを使用しない環境での制限事項

### June 30, 2025 - JavaScript Promise Integration in Pyodide
**著者**: Hood Chatham  
**読了時間**: 5分

**トピック**: JavaScript Promise Integration (JSPI) の導入
- 同期/非同期の問題（sync/async problem）の解決
- Pythonの同期コードとJavaScriptの非同期APIの橋渡し
- `event_loop.run_until_complete()`の実装
- 新しいPyodide APIの紹介

### January 1, 2025 - Pyodide 0.27 Release
**著者**: Gyeongjae Choi, Hood Chatham, Agriya Khetarpal  
**読了時間**: 6分

**主な変更点**:
- **新メンテナー**: Agriya Khetarpalが参加（NumPy、SciPy、scikit-learnの貢献者）
- **ビルドシステムの改善**: `pyodide-build`とPyodideランタイムの分離
- パッケージビルドの柔軟性向上
- 長期的な安定性の向上

## 2024年

### July 27, 2024 - Visual Low/No Code Data Preparation and Analysis Web App Built with Pyodide and React
**著者**: Raul Andrial  
**読了時間**: 4分

**トピック**: Pyodideを使った実世界のアプリケーション例
- ドラッグ&ドロップインターフェースによるデータ分析アプリ
- pandas、matplotlib、scikit-learnを使用
- コード不要でデータ分析が可能

### May 27, 2024 - Pyodide 0.26 Release
**著者**: Hood Chatham, Gyeongjae Choi  
**読了時間**: 11分

**主な変更点**:
- **Python 3.12のサポート**
- 外部関数インターフェースの改善
- ビルドシステムの改善
- スタック切り替えの大幅な改善
- PyCon 2024でのWebAssemblyサミット参加

### April 8, 2024 - marimo: a reactive Python notebook that runs in the browser
**著者**: Akshay Agrawal, Myles Scolnick  
**読了時間**: 7分

**トピック**: marimoのPyodideへの移植
- リアクティブなPythonノートブック
- 再現性、対話性、保守性、共有性の問題解決
- Pyodideによるブラウザ上での実行
- コンピューティングのアクセシビリティ向上

### January 18, 2024 - Pyodide 0.25.0 release
**著者**: Pyodide team  
**読了時間**: 3分

**主な変更点**:
- **requestsライブラリのサポート**: 長年要望されていたHTTPクライアントライブラリ
- **JS Promise統合の実験的サポート**: 非同期処理の改善
- ビルドシステムの改善

## まとめ

### 主なトピックカテゴリ

1. **リリースノート** (0.25, 0.26, 0.27, 0.28, 0.29)
   - 新機能の追加
   - パフォーマンス改善
   - 互換性の向上

2. **JSPI（JavaScript Promise Integration）**
   - 同期/非同期の問題解決
   - WebAssembly Cランタイムとの統合
   - 実装詳細

3. **標準化とABI**
   - PEP 776, PEP 783の策定
   - CPythonとの統合
   - 長期的な互換性の確保

4. **実世界のアプリケーション例**
   - marimo（ノートブック）
   - データ分析アプリ（React + Pyodide）

### 参考リンク

- [Pyodide公式ブログ](https://blog.pyodide.org)
- [Pyodide公式ドキュメント](https://pyodide.org/)
- [Pyodide GitHub](https://github.com/pyodide/pyodide)


