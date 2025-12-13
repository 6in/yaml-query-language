#!/usr/bin/env python3
"""Bundle YQL Python modules into a tar.gz file for Pyodide."""

import tarfile
from pathlib import Path

# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent
YQL_SRC = PROJECT_ROOT / "implementations" / "python" / "src" / "yql"
OUTPUT_FILE = Path(__file__).parent / "yql-bundle.tar.gz"


def bundle_yql_modules():
    """YQLモジュールをtar.gzにまとめる"""
    print(f"Bundling YQL modules from {YQL_SRC}...")
    
    with tarfile.open(OUTPUT_FILE, 'w:gz') as tar:
        # yqlディレクトリ内のすべてのファイルを追加
        for file_path in YQL_SRC.rglob('*.py'):
            # アーカイブ内のパス: yql/ast.py, yql/generator/base.py など
            arcname = file_path.relative_to(YQL_SRC.parent)
            tar.add(file_path, arcname=arcname)
            print(f"  Added: {arcname}")
    
    print(f"✅ Bundled YQL modules to {OUTPUT_FILE}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size} bytes")


if __name__ == "__main__":
    bundle_yql_modules()

