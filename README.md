# 34_tochinomiphoto_get
とちのみの写真をGETするためのプログラム

## セットアップ（macOS・仮想環境）
1. リポジトリへ移動: `cd "/Users/choisc/Library/Mobile Documents/com~apple~CloudDocs/github/34_tochinomiphoto_get"`
2. 仮想環境を作成: `python3 -m venv .venv`
3. 仮想環境を有効化: `source .venv/bin/activate`
4. 依存をインストール: `pip install -r requirements.txt`
   - 終了時は `deactivate` で仮想環境を抜けられます。

## 使い方（簡略）
- Chrome をリモートデバッグで起動: `./start_chrome.sh`（デフォルトで https://ephoto.jp/ を開く。別の URL にしたい場合は引数に指定）  
  - PORT 環境変数でポート変更可（デフォルト 9222）  
  - PROFILE_DIR 環境変数で専用プロファイルの保存先変更可（デフォルト `~/.chrome-selenium`）
- 起動した Chrome でログインし、保存を開始したい画像を表示する
- 別ターミナルで `python main.py` を実行する（実行時に「何枚保存するか」「ファイル名の頭文字」を聞かれる）
