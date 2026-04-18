#!/usr/bin/env bash
# ログイン専用Chrome（本物のプロファイル使用、リモートデバッグなし）
set -euo pipefail

URL="${1:-https://ephoto.jp/}"
REAL_CHROME_DIR="$HOME/Library/Application Support/Google/Chrome"

echo "========================================"
echo "ログイン用Chromeを起動します"
echo "【重要】ログイン後は Cmd+Q でChromeを完全に終了してください"
echo "（ウィンドウを閉じるだけではNGです）"
echo "終了後に「② Open Chrome」を押してください"
echo "========================================"

open -na "Google Chrome" --args \
  --user-data-dir="$REAL_CHROME_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "$URL"
