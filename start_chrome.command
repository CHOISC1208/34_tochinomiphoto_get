#!/bin/bash
# macOS Finder でダブルクリック実行する用。ターミナルを開いて Chrome を
# リモートデバッグモードで起動します。
set -euo pipefail

# このファイルのあるディレクトリに移動（スペース対応）
cd "$(cd "$(dirname "$0")" && pwd)"

# 環境変数で上書き可
PORT="${PORT:-9222}"
PROFILE_DIR="${PROFILE_DIR:-$HOME/.chrome-selenium}"

# Chrome 実行ファイルを探す
if command -v google-chrome >/dev/null 2>&1; then
  CHROME_BIN="google-chrome"
elif [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
  echo "Google Chrome が見つかりません。PATH かパスを指定してください。"
  read -rp "終了するには Enter を押してください。" _
  exit 1
fi

# 開きたいサイトを固定
URL="https://ephoto.jp/"

mkdir -p "$PROFILE_DIR"

echo "Chrome を起動します"
echo "  ポート       : $PORT"
echo "  プロファイル : $PROFILE_DIR"
echo "  初期 URL     : $URL"

"$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  "$URL" >/dev/null 2>&1 &

echo "起動しました。ここでログイン→最初の画像を表示してください。"
read -rp "ウィンドウを閉じるには Enter を押してください。" _
