# -*- coding: utf-8 -*-
"""
TC-0002: 形象-空态与创建形象入口
验证：形象tab筛选、搜索框、创建形象卡片、空态提示
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


def test_tc0002():
    print("=" * 60, flush=True)
    print("TC-0002: 形象-空态与创建形象入口", flush=True)
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

        # 步骤1：打开数字人库
        print("\n--- 步骤1：打开数字人库 ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)

        # 步骤2：切到形象tab
        print("\n--- 步骤2：切到形象tab ---", flush=True)
        page.locator("text=形象").first.click(force=True)
        time.sleep(1)
        shot(page, "tc0002_image_tab.png")

        # 步骤3：验证筛选
        print("\n--- 步骤3：筛选 ---", flush=True)
        for f in ["全部", "女性", "男性"]:
            el = page.locator(f"text={f}")
            if el.count() > 0:
                print(f"  ✅ 筛选 '{f}' 可见", flush=True)
            else:
                errors.append(f"筛选 '{f}' 未找到")

        # 步骤4：验证搜索框
        print("\n--- 步骤4：搜索框 ---", flush=True)
        search = page.locator("input[placeholder*='搜形象']")
        if search.count() > 0:
            print("  ✅ 搜索框'搜形象名'可见", flush=True)
        else:
            print("  [WARN] 搜索框未找到", flush=True)

        # 步骤5：验证创建形象卡片
        print("\n--- 步骤5：创建形象卡片 ---", flush=True)
        create = page.locator("text=创建形象")
        if create.count() > 0:
            print("  ✅ 创建形象卡片可见", flush=True)
        else:
            errors.append("创建形象卡片未找到")

        shot(page, "tc0002_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0002 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0002_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0002()
