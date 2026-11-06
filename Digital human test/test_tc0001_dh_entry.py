# -*- coding: utf-8 -*-
"""
TC-0001: 数字人库-入口与布局
验证：打开数字人库弹窗、四个tab、搜索框、关闭按钮
纯DOM元素定位，环境变量 FJ_CDP_HOST/FJ_CDP_PORT
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


def test_tc0001():
    print("=" * 60, flush=True)
    print("TC-0001: 数字人库-入口与布局", flush=True)
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
            project.first.click(force=True)
            time.sleep(6)

        # 步骤1：点数字人库按钮
        print("\n--- 步骤1：打开数字人库 ---", flush=True)
        dh_btn = page.locator("button[aria-label='数字人库']")
        if dh_btn.count() > 0:
            dh_btn.first.click(force=True)
            time.sleep(2)
            print("  ✅ 已点击数字人库按钮", flush=True)
            shot(page, "tc0001_open.png")
        else:
            errors.append("数字人库按钮 button[aria-label='数字人库'] 未找到")

        # 步骤2：验证四个tab
        print("\n--- 步骤2：验证四个tab ---", flush=True)
        for tab in ["形象", "数字人", "配音", "成片"]:
            el = page.locator(f"text={tab}")
            if el.count() > 0:
                print(f"  ✅ tab '{tab}' 可见", flush=True)
            else:
                errors.append(f"tab '{tab}' 未找到")

        # 步骤3：验证搜索框
        print("\n--- 步骤3：搜索框 ---", flush=True)
        search = page.locator("input[placeholder='搜数字人名']")
        if search.count() > 0:
            print("  ✅ 搜索框'搜数字人名'可见", flush=True)
        else:
            errors.append("搜索框未找到")

        # 步骤4：点关闭
        print("\n--- 步骤4：关闭弹窗 ---", flush=True)
        close_btn = page.locator("button[aria-label='关闭'], .cx-modal__close, [class*='close']")
        if close_btn.count() > 0:
            close_btn.first.click(force=True)
            time.sleep(1)
            print("  ✅ 已关闭弹窗", flush=True)
            shot(page, "tc0001_closed.png")
        else:
            errors.append("关闭按钮未找到")

        shot(page, "tc0001_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0001 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0001_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0001()
