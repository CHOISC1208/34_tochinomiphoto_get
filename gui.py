# gui.py
# -*- coding: utf-8 -*-
"""Tkinter GUI for tochinomiphoto image downloader."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, ttk

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DEFAULT_CONFIG = {
    "url": "https://ephoto.jp/",
    "n_times": 181,
    "wait_sec": 3,
    "change_timeout": 3,
    "out_dir": "downloaded_images",
    "overwrite": False,
    "sleep_between": 0.05,
    "verbose": True,
    "retry": 2,
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            # マージ（新キーがあってもデフォルトで補完）
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class TextRedirector(io.TextIOBase):
    """sys.stdout をScrolledTextに流すラッパー"""

    def __init__(self, widget: scrolledtext.ScrolledText):
        self._widget = widget

    def write(self, s: str) -> int:
        self._widget.after(0, self._append, s)
        return len(s)

    def _append(self, s: str) -> None:
        self._widget.configure(state="normal")
        self._widget.insert(tk.END, s)
        self._widget.see(tk.END)
        self._widget.configure(state="disabled")

    def flush(self) -> None:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tochinomiphoto Downloader")
        self.resizable(True, True)
        self._cfg = load_config()
        self._running = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # ===== 設定フレーム =====
        frame = ttk.LabelFrame(self, text="設定", padding=8)
        frame.grid(row=0, column=0, sticky="ew", **pad)
        self.columnconfigure(0, weight=1)

        self._vars: dict[str, tk.Variable] = {}

        def row_entry(label: str, key: str, r: int, width: int = 30):
            ttk.Label(frame, text=label).grid(row=r, column=0, sticky="w")
            var = tk.StringVar(value=str(self._cfg[key]))
            self._vars[key] = var
            ttk.Entry(frame, textvariable=var, width=width).grid(row=r, column=1, sticky="ew", padx=4)

        def row_check(label: str, key: str, r: int):
            ttk.Label(frame, text=label).grid(row=r, column=0, sticky="w")
            var = tk.BooleanVar(value=bool(self._cfg[key]))
            self._vars[key] = var
            ttk.Checkbutton(frame, variable=var).grid(row=r, column=1, sticky="w", padx=4)

        frame.columnconfigure(1, weight=1)

        row_entry("URL",            "url",            0, width=40)
        row_entry("枚数 (N_TIMES)", "n_times",        1)
        row_entry("待機秒 (WAIT_SEC)", "wait_sec",    2)
        row_entry("切替タイムアウト", "change_timeout", 3)
        row_entry("出力フォルダ",   "out_dir",        4)
        row_entry("連番間隔 (SLEEP_BETWEEN)", "sleep_between", 5)
        row_entry("リトライ数 (RETRY)", "retry",      6)
        row_check("上書き (OVERWRITE)", "overwrite",  7)
        row_check("詳細ログ (VERBOSE)", "verbose",    8)

        # ファイル名プレフィックス（config非保存・セッション限り）
        ttk.Label(frame, text="ファイル名プレフィックス").grid(row=9, column=0, sticky="w")
        self._prefix_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self._prefix_var, width=30).grid(row=9, column=1, sticky="ew", padx=4)

        # ===== ボタンフレーム =====
        btn_frame = ttk.Frame(self, padding=4)
        btn_frame.grid(row=1, column=0, sticky="ew", **pad)

        self._login_btn = ttk.Button(btn_frame, text="① Login", command=self._open_login_chrome)
        self._login_btn.pack(side="left", padx=4)

        self._chrome_btn = ttk.Button(btn_frame, text="② Open Chrome", command=self._open_chrome)
        self._chrome_btn.pack(side="left", padx=4)

        self._run_btn = ttk.Button(btn_frame, text="RUN", command=self._start_run)
        self._run_btn.pack(side="left", padx=4)

        self._stop_btn = ttk.Button(btn_frame, text="STOP (次枚で停止)", command=self._request_stop, state="disabled")
        self._stop_btn.pack(side="left", padx=4)

        self._save_btn = ttk.Button(btn_frame, text="設定を保存", command=self._save_config_ui)
        self._save_btn.pack(side="right", padx=4)

        # ===== ログエリア =====
        log_frame = ttk.LabelFrame(self, text="ログ", padding=4)
        log_frame.grid(row=2, column=0, sticky="nsew", **pad)
        self.rowconfigure(2, weight=1)

        self._log = scrolledtext.ScrolledText(log_frame, state="disabled", wrap="word", height=20)
        self._log.pack(fill="both", expand=True)

        # stdout リダイレクト
        self._redirector = TextRedirector(self._log)
        sys.stdout = self._redirector

        # ===== ステータスバー =====
        self._status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status_var, relief="sunken", anchor="w").grid(
            row=3, column=0, sticky="ew"
        )

        self.geometry("680x700")

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------
    def _collect_config(self) -> dict:
        cfg = {}
        for key, var in self._vars.items():
            raw = var.get()
            if key in ("overwrite", "verbose"):
                cfg[key] = bool(raw)
            elif key in ("n_times", "wait_sec", "change_timeout", "retry"):
                try:
                    cfg[key] = int(raw)
                except ValueError:
                    cfg[key] = self._cfg[key]
            elif key == "sleep_between":
                try:
                    cfg[key] = float(raw)
                except ValueError:
                    cfg[key] = self._cfg[key]
            else:
                cfg[key] = str(raw)
        return cfg

    def _save_config_ui(self):
        cfg = self._collect_config()
        save_config(cfg)
        self._status_var.set("設定を保存しました")

    # ------------------------------------------------------------------
    # Open Chrome
    # ------------------------------------------------------------------
    def _open_login_chrome(self):
        url = self._vars["url"].get().strip() or "https://ephoto.jp/"
        script = Path(__file__).resolve().parent / "login_chrome.sh"
        try:
            subprocess.Popen(["bash", str(script), url])
            self._status_var.set("ログイン用Chrome起動 - ログイン後に閉じて「② Open Chrome」を押してください")
            print("[GUI] ログイン用Chrome起動（リモートデバッグなし）")
            print("[GUI] ログイン完了後、そのChromeを閉じてから「② Open Chrome」を押してください。")
        except Exception as e:
            self._status_var.set(f"Chrome起動エラー: {e}")

    def _open_chrome(self):
        url = self._vars["url"].get().strip() or "https://ephoto.jp/"
        script = Path(__file__).resolve().parent / "start_chrome.sh"
        try:
            subprocess.Popen(["bash", str(script), url])
            self._status_var.set(f"Chrome を起動しました: {url}")
            print(f"[GUI] Chrome 起動: {url}")
        except Exception as e:
            self._status_var.set(f"Chrome 起動エラー: {e}")
            print(f"[GUI] Chrome 起動エラー: {e}")

    # ------------------------------------------------------------------
    # RUN / STOP
    # ------------------------------------------------------------------
    def _start_run(self):
        if self._running:
            return
        self._running = True
        self._stop_requested = False
        self._run_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_var.set("実行中...")

        cfg = self._collect_config()
        prefix = self._prefix_var.get().strip()

        thread = threading.Thread(target=self._run_worker, args=(cfg, prefix), daemon=True)
        thread.start()

    def _request_stop(self):
        self._stop_requested = True
        self._status_var.set("停止リクエスト済み（次枚で停止します）")
        print("[GUI] 停止リクエストを受け付けました。")

    def _run_worker(self, cfg: dict, prefix: str):
        try:
            import main as main_mod
            # stop_requested フラグを main モジュールに渡すためにモンキーパッチ
            original_wait_changed = main_mod.wait_changed_fast

            app_ref = self

            def patched_wait_changed(driver, prev_src, timeout=3):
                if app_ref._stop_requested:
                    return False
                return original_wait_changed(driver, prev_src, timeout)

            main_mod.wait_changed_fast = patched_wait_changed
            try:
                main_mod.run(cfg, prefix=prefix)
            finally:
                main_mod.wait_changed_fast = original_wait_changed
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self.after(0, self._on_run_finished)

    def _on_run_finished(self):
        self._running = False
        self._run_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._status_var.set("完了")

    # ------------------------------------------------------------------
    # 終了時にstdoutを戻す
    # ------------------------------------------------------------------
    def destroy(self):
        sys.stdout = sys.__stdout__
        super().destroy()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
