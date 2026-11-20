# ETOI ウェブメディア
名画を、仕事と人生の言葉で読み解くメディア。公開は GitHub Pages（main ブランチの docs/）。
- 記事化：`python3 tools/import_post.py <etoi-images/posts/NN> <元画像フォルダ>`（meta/NN.json が必要）
- ビルド：`python3 tools/build.py` → docs/
- 設定：site.json（base_url, base_path, line_url, ga_id）、themes.json
