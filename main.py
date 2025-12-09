# save_via_browser_fetch.py
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


# ===== 設定 =====
N_TIMES = 181                       # 何枚保存するか
WAIT_SEC = 15                      # Selenium の待機秒
OUT_DIR = "downloaded_images"      # 保存フォルダ
OVERWRITE = False                  # 同名があっても上書きする？
SLEEP_BETWEEN = 0.2                # 次へ間のクールダウン
VERBOSE = True                     # ログ多め
# =================

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


def build_driver():
    opts = Options()
    # すでに --remote-debugging-port=9222 で起動中の Chrome にアタッチ
    opts.debugger_address = "127.0.0.1:9222"
    drv = webdriver.Chrome(options=opts)
    wait = WebDriverWait(drv, WAIT_SEC)
    return drv, wait


def find_img(driver):
    """ターゲット画像をメイン→浅い iframe で探索して返す"""
    driver.switch_to.default_content()
    for by, sel in IMG_LOCATORS:
        els = driver.find_elements(by, sel)
        if els:
            return els[0]

    # 簡易 iframe 探索
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


def get_current_src(driver, wait) -> str:
    """DevTools の Current source（= HTMLImageElement.currentSrc）を取得"""
    img = find_img(driver)
    wait.until(EC.visibility_of(img))
    cur = driver.execute_script(
        "return arguments[0].currentSrc || arguments[0].src || '';",
        img
    )
    if VERBOSE:
        print("currentSrc:", cur)
    return cur


def fetch_image_via_browser(driver, url: str) -> bytes:
    """
    ブラウザの fetch で同一セッションのまま画像を取得して、
    Base64 にして Python 側に返す（credentials: 'include' & Referer 付与）
    """
    script = """
    const url = arguments[0];
    const referer = document.location.href;
    const callback = arguments[arguments.length - 1];

    (async () => {
      try {
        const res = await fetch(url, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Referer': referer,
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
          },
          cache: 'no-store',
        });
        const ct = res.headers.get('Content-Type') || '';
        const ab = await res.arrayBuffer();
        const bytes = new Uint8Array(ab);

        // Base64 へ
        let binary = '';
        const chunk = 0x8000;
        for (let i = 0; i < bytes.length; i += chunk) {
          binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
        }
        const b64 = btoa(binary);
        callback({ ok: true, contentType: ct, base64: b64, length: bytes.length });
      } catch (e) {
        callback({ ok: false, error: String(e) });
      }
    })();
    """
    result = driver.execute_async_script(script, url)
    if not result or not result.get("ok"):
        raise RuntimeError(f"browser fetch failed: {result!r}")
    if VERBOSE:
        print("ctype:", result.get("contentType"), "bytes:", result.get("length"))
    # 画像以外を弾く（最低限）
    ctype = (result.get("contentType") or "").lower()
    if not ctype.startswith("image/") or int(result.get("length") or 0) < 256:
        raise RuntimeError(f"not image or too small: ctype={ctype}, len={result.get('length')}")
    return base64.b64decode(result["base64"])


def parse_idx_from_url(url: str) -> int | None:
    q = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    try:
        return int(q.get("idx")) if "idx" in q else None
    except Exception:
        return None


def filename_from_url(url: str, seq: int) -> str:
    """id, sub, idx を使ってファイル名に。拡張子は常に .jpg"""
    q = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    base = "image"
    if q.get("id"):
        base += f"_{q['id']}"
    if q.get("sub"):
        base += f"_{q['sub']}"
    num = parse_idx_from_url(url)
    if num is None:
        num = seq
    return f"{base}_{num:04d}.jpg"


def save_bytes(out_dir: Path, filename: str, data: bytes) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    if path.exists() and not OVERWRITE:
        return path
    with open(path, "wb") as f:
        f.write(data)
    return path


def click_next(driver, wait):
    def try_click():
        for by, sel in NEXT_LOCATORS:
            try:
                el = wait.until(EC.element_to_be_clickable((by, sel)))
                # 親 a / button を優先クリック
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


def wait_changed(driver, wait, prev_url: str, timeout: int = WAIT_SEC) -> str:
    end = time.time() + timeout
    last = prev_url
    while time.time() < end:
        try:
            cur = get_current_src(driver, wait)
            if cur and cur != prev_url:
                return cur
            last = cur
        except Exception:
            pass
        time.sleep(0.3)
    return last


def main():
    driver, wait = build_driver()
    print("Connected:", driver.title, driver.current_url)

    out_root = Path(__file__).resolve().parent / OUT_DIR

    for i in range(1, N_TIMES + 1):
        # 1) currentSrc を取得
        img_url = get_current_src(driver, wait)

        # 2) ブラウザに fetch させてバイト列を取得
        try:
            data = fetch_image_via_browser(driver, img_url)
        except Exception as e:
            print(f"[{i}/{N_TIMES}] fetch failed: {e}")
            break

        # 3) 保存（.jpg 固定のファイル名）
        fname = filename_from_url(img_url, i)
        path = save_bytes(out_root, fname, data)
        print(f"[{i}/{N_TIMES}] saved -> {path.name}")

        if i >= N_TIMES:
            break

        # 4) 次へ
        click_next(driver, wait)

        # 5) 画像が切り替わるまで待つ
        new_url = wait_changed(driver, wait, img_url, WAIT_SEC)
        if new_url == img_url:
            print("画像が切り替わらないため終了します。")
            break

        if SLEEP_BETWEEN:
            time.sleep(SLEEP_BETWEEN)

    print(f"Done. Output dir: { (Path(__file__).resolve().parent / OUT_DIR) }")


if __name__ == "__main__":
    main()
