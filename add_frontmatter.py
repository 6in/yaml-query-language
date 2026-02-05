#!/usr/bin/env python3
import os

def add_front_matter(file_path):
    """YAML Front Matter を追加"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既に Front Matter がある場合はスキップ
    if content.startswith('---'):
        return False
    
    # ファイル名から title を生成
    filename = os.path.basename(file_path)
    title = filename.replace('.md', '').replace('-', ' ').title()
    
    # Front Matter を追加
    front_matter = f"""---
layout: default
title: {title}
---

"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)
    
    return True

# docs/ 配下のすべての .md ファイルを処理
docs_dir = 'docs'
count = 0

for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith('.md'):
            file_path = os.path.join(root, file)
            if add_front_matter(file_path):
                count += 1
                print(f"✓ {file_path}")

print(f"\n合計 {count} ファイルを更新しました。")
