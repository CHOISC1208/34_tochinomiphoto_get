# 34_tochinomiphoto_get
とちのみの写真をGETするためのプログラム

## 使い方（簡略）
- Chrome をリモートデバッグで起動: `./start_chrome.sh`（デフォルトで https://ephoto.jp/ を開く。別の URL にしたい場合は引数に指定）  
  - PORT 環境変数でポート変更可（デフォルト 9222）  
  - PROFILE_DIR 環境変数で専用プロファイルの保存先変更可（デフォルト `~/.chrome-selenium`）
- 起動した Chrome でログインし、保存を開始したい画像を表示する
- 別ターミナルで `python main.py` を実行する
