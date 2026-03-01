# main.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qsl

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


IMG_LOCATORS = [
    (By.CSS_SELECTOR, "#imgv-z"),  # 新
    (By.CSS_SELECTOR, "#imgv"),    # 旧
]

NEXT_LOCATORS = [
    (By.CSS_SELECTOR, "span.ui-icon.ui-icon-arrow-r"),
    (By.XPATH, "//span[contains(@class,'ui-icon-arrow-r')]"),
    (By.CSS_SELECTOR, 'img[alt="次画面"]'),
    (By.CSS_SELECTOR, 'img[src*="btnScrNext"]'),
    (By.XPATH, "//*[text()='次画面']"),
    (By.CSS_SELECTOR, 'button[aria-label="次画面"]'),
    (By.CSS_SELECTOR, 'input[alt="次画面"]'),
]


def build_driver(wait_sec: int = 3):
    opts = Options()
    opts.debugger_address = "127.0.0.1:9222"  # start_chrome.sh で起動済み前提
    drv = webdriver.Chrome(options=opts)
    wait = WebDriverWait(drv, wait_sec)
    return drv, wait


def find_img(driver):
    """ターゲット画像をメイン→浅い iframe で探索して返す"""
    driver.switch_to.default_content()
    for by, sel in IMG_LOCATORS:
        els = driver.find_elements(by, sel)
        if els:
            return els[0]

    frames = driver.find_elements(By.XPATH, "//iframe|//frame")
    for i in range(len(frames)):
        try:
            driver.switch_to.default_content()
            frames2 = driver.find_elements(By.XPATH, "//iframe|//frame")
            if i >= len(frames2):
                continue
            driver.switch_to.frame(frames2[i])
            for by, sel in IMG_LOCATORS:
                els = driver.find_elements(by, sel)
                if els:
                    return els[0]
        except Exception:
            continue

    driver.switch_to.default_content()
    raise RuntimeError("画像が見つかりません (#imgv-z / #imgv)")


def get_current_src(driver, wait, verbose: bool = True) -> str:
    img = find_img(driver)
    wait.until(EC.visibility_of(img))
    cur = driver.execute_script(
        "return arguments[0].currentSrc || arguments[0].src || '';",
        img
    )
    if verbose:
        print("currentSrc:", cur)
    return cur


def fetch_image_via_canvas(driver, url: str, verbose: bool = True) -> bytes:
    """
    <img> として読み込ませて canvas で JPEG 化して回収。
    fetch が HTML を返すサイトでも通ることが多い。
    """
    script = """
    const url = arguments[0];
    const callback = arguments[arguments.length - 1];

    (async () => {
      try {
        const img = new Image();
        img.decoding = "async";

        await new Promise((resolve, reject) => {
          img.onload = resolve;
          img.onerror = reject;
          img.src = url;
        });

        const w = img.naturalWidth || img.width;
        const h = img.naturalHeight || img.height;
        if (!w || !h) throw new Error("image has no size");

        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);

        const dataUrl = canvas.toDataURL("image/jpeg", 0.95);
        const b64 = dataUrl.split(",")[1] || "";
        callback({ ok: true, base64: b64, w, h, b64len: b64.length });
      } catch (e) {
        callback({ ok: false, error: String(e) });
      }
    })();
    """
    result = driver.execute_async_script(script, url)
    if not result or not result.get("ok"):
        raise RuntimeError(f"canvas fetch failed: {result!r}")

    if verbose:
        print("canvas:", result.get("w"), "x", result.get("h"), "b64len:", result.get("b64len"))

    return base64.b64decode(result["base64"])


def parse_idx_from_url(url: str) -> int | None:
    q = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    try:
        return int(q.get("idx")) if "idx" in q else None
    except Exception:
        return None


def filename_from_url(url: str, seq: int, prefix: str, pad: int) -> str:
    if prefix:
        return f"{prefix}-{seq:0{pad}d}.jpg"
    q = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    base = "image"
    if q.get("id"):
        base += f"_{q['id']}"
    if q.get("sub"):
        base += f"_{q['sub']}"
    num = parse_idx_from_url(url) or seq
    return f"{base}_{num:0{pad}d}.jpg"


def save_bytes(out_dir: Path, filename: str, data: bytes, overwrite: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    if path.exists() and not overwrite:
        return path
    with open(path, "wb") as f:
        f.write(data)
    return path


def click_next(driver, wait):
    def try_click():
        for by, sel in NEXT_LOCATORS:
            try:
                el = wait.until(EC.element_to_be_clickable((by, sel)))
                for anc in ["./ancestor::a[1]", "./ancestor::button[1]"]:
                    try:
                        p = el.find_element(By.XPATH, anc)
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", p)
                        p.click()
                        return True
                    except Exception:
                        pass
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                el.click()
                return True
            except Exception:
                continue
        return False

    if try_click():
        return
    driver.switch_to.default_content()
    if try_click():
        return
    raise RuntimeError("次へボタンが見つかりません")


def wait_changed_fast(driver, prev_src: str, timeout: int = 3) -> bool:
    """
    URL比較のポーリングより速い版。
    img.complete && currentSrcが変わったらOK。
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            ok = driver.execute_script(
                """
                const prev = arguments[0];
                const img = document.querySelector('#imgv-z, #imgv');
                if (!img) return false;
                const cur = img.currentSrc || img.src || '';
                return !!cur && (cur !== prev) && img.complete;
                """,
                prev_src,
            )
            if ok:
                return True
        except Exception:
            pass
        time.sleep(0.08)
    return False


def find_resume_seq(out_root: Path, prefix: str) -> int:
    """
    途中再開：prefix-001.jpg のような連番がある場合、次のseqを返す。
    prefixが空なら resume しない（安全側）
    """
    if not prefix:
        return 1
    files = sorted(out_root.glob(f"{prefix}-*.jpg"))
    if not files:
        return 1
    last = files[-1].stem
    try:
        num = int(last.split("-")[-1])
        return num + 1
    except Exception:
        return 1


def run(config: dict, prefix: str = ""):
    """GUIまたはCLIから呼び出すメインロジック。

    config keys:
        n_times, wait_sec, change_timeout, out_dir,
        overwrite, sleep_between, verbose, retry
    """
    n_times = int(config.get("n_times", 181))
    wait_sec = int(config.get("wait_sec", 3))
    change_timeout = int(config.get("change_timeout", 3))
    out_dir = config.get("out_dir", "downloaded_images")
    overwrite = bool(config.get("overwrite", False))
    sleep_between = float(config.get("sleep_between", 0.05))
    verbose = bool(config.get("verbose", True))
    retry = int(config.get("retry", 2))

    pad = max(3, len(str(n_times)))

    driver, wait = build_driver(wait_sec)
    print("Connected:", driver.title, driver.current_url)

    out_root = Path(__file__).resolve().parent / out_dir

    start_seq = find_resume_seq(out_root, prefix)
    if start_seq > 1:
        print(f"[RESUME] {start_seq} から再開します（prefix={prefix}）")

    for i in range(start_seq, n_times + 1):
        img_url = get_current_src(driver, wait, verbose)

        last_err = None
        for r in range(retry + 1):
            try:
                data = fetch_image_via_canvas(driver, img_url, verbose)
                last_err = None
                break
            except Exception as e:
                last_err = e
                if verbose:
                    print(f"  retry {r+1}/{retry}: {e}")
                time.sleep(0.2)

        if last_err is not None:
            print(f"[{i}/{n_times}] fetch failed (canvas): {last_err}")
            break

        fname = filename_from_url(img_url, i, prefix, pad)
        path = save_bytes(out_root, fname, data, overwrite)
        print(f"[{i}/{n_times}] saved -> {path.name}")

        if i >= n_times:
            break

        click_next(driver, wait)

        if not wait_changed_fast(driver, img_url, timeout=change_timeout):
            print("画像が切り替わらないため終了します。")
            break

        if sleep_between:
            time.sleep(sleep_between)

    print(f"Done. Output dir: {out_root}")


def main():
    # CLIからの後方互換エントリポイント
    N_TIMES = 181
    n_times = N_TIMES
    try:
        ans = input(f"何枚保存しますか？ [Enter で {N_TIMES}]: ").strip()
        if ans:
            v = int(ans)
            if v > 0:
                n_times = v
            else:
                print("1 以上の数値を指定してください。デフォルトを使用します。")
    except Exception:
        print("数値の解釈に失敗したため、デフォルトを使用します。")

    prefix = input("ファイル名の頭につける文字列は？（空のまま Enter で通常名）: ").strip()

    config = {
        "n_times": n_times,
        "wait_sec": 3,
        "change_timeout": 3,
        "out_dir": "downloaded_images",
        "overwrite": False,
        "sleep_between": 0.05,
        "verbose": True,
        "retry": 2,
    }
    run(config, prefix=prefix)


if __name__ == "__main__":
    main()
