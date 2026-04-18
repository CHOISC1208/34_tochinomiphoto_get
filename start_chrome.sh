#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-9222}"
URL="${1:-https://ephoto.jp/}"
PROFILE_DIR="${PROFILE_DIR:-$HOME/.chrome-selenium}"
REAL_CHROME_DIR="$HOME/Library/Application Support/Google/Chrome"
REAL_DEFAULT="$REAL_CHROME_DIR/Default"
SEL_DEFAULT="$PROFILE_DIR/Default"

mkdir -p "$SEL_DEFAULT"

# Chromeが起動中の場合は警告
if pgrep -x "Google Chrome" >/dev/null 2>&1; then
  echo "⚠️  Chromeが起動中です。"
  echo "「① Login」でログイン後、Cmd+Q でChromeを完全終了してからこのボタンを押してください。"
  osascript -e 'display alert "Chromeが起動中です" message "Cmd+Q でChromeを完全終了してから「② Open Chrome」を押してください。" as warning'
  exit 1
fi

echo "本物のChromeプロファイルからセッションをコピー中..."

# Cookies（WAL/journalも含む）
for f in Cookies "Cookies-journal" "Cookies-wal"; do
  [[ -f "$REAL_DEFAULT/$f" ]] && cp "$REAL_DEFAULT/$f" "$SEL_DEFAULT/$f"
done
echo "  → Cookie コピー完了"

# LocalStorage
if [[ -d "$REAL_DEFAULT/Local Storage" ]]; then
  rm -rf "$SEL_DEFAULT/Local Storage"
  cp -r "$REAL_DEFAULT/Local Storage" "$SEL_DEFAULT/Local Storage"
  echo "  → LocalStorage コピー完了"
fi

# IndexedDB
if [[ -d "$REAL_DEFAULT/IndexedDB" ]]; then
  rm -rf "$SEL_DEFAULT/IndexedDB"
  cp -r "$REAL_DEFAULT/IndexedDB" "$SEL_DEFAULT/IndexedDB"
  echo "  → IndexedDB コピー完了"
fi

echo "Starting Chrome with remote debugging on port ${PORT}"

open -na "Google Chrome" --args \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  --disable-blink-features=AutomationControlled \
  --no-first-run \
  --no-default-browser-check \
  "$URL"

echo "Chrome を起動しました。アルバムページに移動して「RUN」を押してください。"
