#!/usr/bin/env bash
# Finder からダブルクリックで gui.py を起動するスクリプト

# このスクリプトが置かれているディレクトリに移動
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 仮想環境の Python で GUI を起動
exec "$DIR/.venv/bin/python" "$DIR/gui.py"
