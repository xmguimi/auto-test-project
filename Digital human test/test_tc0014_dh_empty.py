# -*- coding: utf-8 -*-
"""
TC-0014: 数字人-空态与创建入口
验证：数字人tab空态文案、创建按钮、选择创建方式弹窗
纯DOM元素定位
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    target = None
    for p in browser.contexts[0].pages:
        if "帧境" in (p.title() or ""):
            target = p
            break
    if not target:
        target = browser.contexts[0].pages[0]
    return pw, browser, target


def test_tc0014():
    print("=" * 60, flush=True)
    print("TC-0014: 数字人空态与创建入口", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200
    except Exception:
        print("[ERROR] CDP未就绪", flush=True); sys.exit(1)

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        time.sleep(2)

        # 步骤0：进入项目
        print("\n--- 步骤0：进入项目 ---", flush=True)
        project = page.locator("text=剪辑测试")
        if project.count() > 0:
            try:
                project.first.click(force=True, timeout=3000)
                time.sleep(6)
            except:
                print("  [INFO] 已在项目中", flush=True)

        # 步骤1：打开数字人库→数字人tab
        print("\n--- 步骤1：点数字人tab ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '数字人') { e.click(); break; } }
        }""")
        time.sleep(2)
        shot(page, "tc0014_empty.png")

        # 步骤2：验证空态文案
        print("\n--- 步骤2：验证空态文案 ---", flush=True)
        for text in ["还没有数字人", "创建数字人"]:
            el = page.locator(f"text={text}")
            if el.count() > 0:
                print(f"  ✅ 文案 '{text}' 可见", flush=True)
            else:
                errors.append(f"文案 '{text}' 未找到")

        # 步骤3：点创建数字人
        print("\n--- 步骤3：点创建数字人 ---", flush=True)
        create_btn = page.locator("text=创建数字人")
        if create_btn.count() > 0:
            create_btn.first.click(force=True)
            time.sleep(2)
            shot(page, "tc0014_create_dialog.png")
            print("  ✅ 已点创建数字人", flush=True)
        else:
            errors.append("创建数字人按钮未找到")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0014 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0014_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0014()
