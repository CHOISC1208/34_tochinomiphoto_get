# 34_tochinomiphoto_get
とちのみの写真をGETするためのプログラム（Tkinter GUI版）

## セットアップ（macOS・初回のみ）

1. リポジトリへ移動:
   ```bash
   cd /Users/choiseoncheol/git/34_tochinomiphoto_get
   ```
2. 仮想環境を作成:
   ```bash
   python3 -m venv .venv
   ```
3. 依存をインストール:
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```
4. Tkinter 用の Tcl/Tk をインストール（Homebrew が必要）:
   ```bash
   brew install python-tk@3.14
   ```

## 起動方法

Finder で **`run.command`** をダブルクリックするだけで GUI が起動します。

> 初回はセキュリティダイアログが出る場合があります。右クリック →「開く」で許可してください。

## 使い方

1. `run.command` をダブルクリックして GUI を開く
2. 必要に応じて設定欄（URL・枚数など）を編集
3. **「Open Chrome」** ボタンを押す → デバッグ用 Chrome が起動
4. 起動した Chrome でログインし、保存を開始したい画像を表示する
5. **「RUN」** ボタンを押す → ログエリアに進捗が流れ、画像が保存される
6. 途中で止めたい場合は **「STOP」** ボタンを押す（次の枚で停止）

## 設定項目

| 項目 | 説明 | デフォルト |
|------|------|-----------|
| URL | Chrome が最初に開く URL | `https://ephoto.jp/` |
| 枚数 (N_TIMES) | 保存する枚数 | 181 |
| 待機秒 (WAIT_SEC) | Selenium の明示待機秒数 | 3 |
| 切替タイムアウト | 次へ後の画像切り替わり最大待機秒 | 3 |
| 出力フォルダ | 画像の保存先フォルダ名 | `downloaded_images` |
| 連番間隔 (SLEEP_BETWEEN) | 次へクリック後のクールダウン秒 | 0.05 |
| リトライ数 (RETRY) | 画像取得の最大リトライ回数 | 2 |
| 上書き (OVERWRITE) | 既存ファイルを上書きするか | OFF |
| 詳細ログ (VERBOSE) | 詳細なログを表示するか | ON |
| ファイル名プレフィックス | ファイル名の先頭に付ける文字列（空欄で自動命名） | 空欄 |

設定は **「設定を保存」** ボタンで `config.json` に保存され、次回起動時に引き継がれます。

## ファイル構成

```
.
├── run.command       # 起動用スクリプト（ダブルクリックで起動）
├── gui.py            # Tkinter GUI
├── main.py           # ダウンロードロジック
├── config.json       # 設定の保存ファイル
├── start_chrome.sh   # デバッグ用 Chrome 起動スクリプト
└── requirements.txt  # 依存ライブラリ
```

## CLI での実行（上級者向け）

GUI を使わずターミナルから直接実行することも可能です。

```bash
# Chrome をリモートデバッグで起動（別ターミナル）
./start_chrome.sh [URL]

# メインスクリプトを実行
.venv/bin/python main.py
```

`PORT` / `PROFILE_DIR` 環境変数でポート・プロファイル保存先を変更できます。
