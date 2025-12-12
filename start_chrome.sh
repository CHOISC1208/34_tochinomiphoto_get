#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-9222}"
PROFILE_DIR="${PROFILE_DIR:-$HOME/.chrome-selenium}"
URL="${1:-https://ephoto.jp/}"

mkdir -p "$PROFILE_DIR"

echo "Starting Chrome with remote debugging on port ${PORT}"
echo "User data dir: ${PROFILE_DIR}"
echo "Initial URL   : ${URL}"

# macOS は open -na が安定
if [[ "$OSTYPE" == "darwin"* ]]; then
  # 既存プロセスが邪魔するので、できれば事前にChromeを閉じるの推奨
  open -na "Google Chrome" --args \
    --remote-debugging-port="$PORT" \
    --user-data-dir="$PROFILE_DIR" \
    "$URL"
else
  # Linux等
  if command -v google-chrome >/dev/null 2>&1; then
    google-chrome \
      --remote-debugging-port="$PORT" \
      --user-data-dir="$PROFILE_DIR" \
      "$URL" >/dev/null 2>&1 &
  else
    echo "google-chrome が見つかりません" >&2
    exit 1
  fi
fi

echo "Chrome を起動しました。ログインと対象ページの表示を行ってください。"
