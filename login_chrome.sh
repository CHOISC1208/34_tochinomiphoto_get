#!/usr/bin/env bash
# ログイン専用Chrome（本物のプロファイル使用、リモートデバッグなし）
set -euo pipefail

URL="${1:-https://ephoto.jp/}"
REAL_CHROME_DIR="$HOME/Library/Application Support/Google/Chrome"

if pgrep -x "Google Chrome" >/dev/null 2>&1; then
  echo "⚠️  Chromeが起動中です。Cmd+Q で完全終了してから再度実行してください。"
  exit 1
fi

echo "========================================"
echo "ログイン用Chromeを起動します"
echo "【重要】ログイン後は Cmd+Q でChromeを完全に終了してください"
echo "終了後に「bash start_chrome.sh」を実行してください"
echo "========================================"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir="$REAL_CHROME_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "$URL" > /dev/null 2>&1 &
