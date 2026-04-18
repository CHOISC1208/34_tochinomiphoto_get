#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-9222}"
URL="${1:-https://ephoto.jp/}"
PROFILE_DIR="${PROFILE_DIR:-$HOME/.chrome-selenium}"
REAL_DEFAULT="$HOME/Library/Application Support/Google/Chrome/Default"
SEL_DEFAULT="$PROFILE_DIR/Default"

# Chromeが起動中の場合は警告
if pgrep -x "Google Chrome" >/dev/null 2>&1; then
  echo "⚠️  Chromeが起動中です。Cmd+Q で完全終了してから再度実行してください。"
  exit 1
fi

echo "本物のChromeプロファイルを丸ごとコピー中（少し時間がかかります）..."
rm -rf "$SEL_DEFAULT"
cp -r "$REAL_DEFAULT" "$SEL_DEFAULT"
echo "  → コピー完了"

echo "Starting Chrome with remote debugging on port ${PORT}"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "$URL" > /dev/null 2>&1 &

echo "Chrome を起動しました。アルバムページに移動して「uv run python main.py」を実行してください。"
