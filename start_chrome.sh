#!/usr/bin/env bash
set -euo pipefail

# 環境変数で上書き可能
PORT="${PORT:-9222}"
PROFILE_DIR="${PROFILE_DIR:-$HOME/.chrome-selenium}"

# Chrome 実行ファイルを探す（macOS / Linux）
if command -v google-chrome >/dev/null 2>&1; then
  CHROME_BIN="google-chrome"
elif [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
  echo "Google Chrome が見つかりませんでした。PATH かパスを指定してください。" >&2
  exit 1
fi

mkdir -p "$PROFILE_DIR"

# デフォルトで ephoto を開く。引数があればそれを優先。
URL="${1:-https://ephoto.jp/}"
echo "Starting Chrome with remote debugging on port ${PORT}"
echo "User data dir: ${PROFILE_DIR}"
echo "Initial URL   : ${URL}"

"$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  "$URL" >/dev/null 2>&1 &

echo "Chrome を起動しました。ログインと対象ページの表示を行ってください。"
