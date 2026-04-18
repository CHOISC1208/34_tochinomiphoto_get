# 34_tochinomiphoto_get

とちのみの写真をダウンロードするツール

## セットアップ（初回のみ）

[uv](https://docs.astral.sh/uv/) が必要です。インストールされていない場合:
```bash
brew install uv
```

## 毎回の起動手順

### 1. ログイン（初回 or セッションが切れたとき）

Chromeが起動している場合は **Cmd+Q** で完全終了してから：

```bash
cd /Users/choiseoncheol/git/34_tochinomiphoto_get
bash login_chrome.sh
```

→ 開いたChromeで ephoto.jp にログイン  
→ ログイン完了後 **Cmd+Q** でChromeを完全終了

### 2. ダウンロード用Chrome起動

```bash
bash start_chrome.sh
```

→ ログイン状態のChromeが開く  
→ アルバムの **1枚目** のページに移動

### 3. ダウンロード開始

```bash
uv run python main.py
```

→ 保存枚数を入力（Enterでデフォルト181枚）  
→ ファイル名プレフィックスを入力（例: `08`、空のままEnterで自動命名）  
→ 自動でダウンロード開始

画像は `downloaded_images/` フォルダに保存されます。

## 2回目以降（ログイン済みの場合）

手順1は不要です。手順2から始めてください。

## ファイル構成

```
.
├── main.py             # ダウンロードロジック
├── login_chrome.sh     # ログイン用Chrome起動スクリプト
├── start_chrome.sh     # ダウンロード用Chrome起動スクリプト
├── main.command        # ダブルクリックで main.py を起動
├── gui.py              # GUI版（現在署名問題により非推奨）
└── downloaded_images/  # 保存先フォルダ（自動生成）
```
