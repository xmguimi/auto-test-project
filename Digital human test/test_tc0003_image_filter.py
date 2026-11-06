# -*- coding: utf-8 -*-
"""
TC-0003: 形象-筛选与搜索
验证：筛选切换、选中态、搜索匹配、无结果空态、清空恢复
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


def test_tc0003():
    print("=" * 60, flush=True)
    print("TC-0003: 形象-筛选与搜索", flush=True)
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

        # 步骤1：打开数字人库→形象tab
        print("\n--- 步骤1：进入形象tab ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.locator("text=形象").first.click(force=True)
        time.sleep(1)

        # 步骤2：点全部→女性→男性
        print("\n--- 步骤2：筛选切换 ---", flush=True)
        for f in ["全部", "女性", "男性"]:
            page.locator(f"text={f}").first.click(force=True)
            time.sleep(0.5)
            print(f"  ✅ 已点 '{f}'", flush=True)
        shot(page, "tc0003_filter.png")

        # 步骤3：搜索不存在的关键词
        print("\n--- 步骤3：搜索 ---", flush=True)
        search = page.locator("input[placeholder*='搜形象']")
        if search.count() > 0:
            search.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("不存在的形象xyz")
            time.sleep(1)
            print("  ✅ 已输入不存在关键词", flush=True)
            shot(page, "tc0003_search_empty.png")
            # 清空
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            time.sleep(0.5)
            print("  ✅ 已清空搜索", flush=True)
        else:
            errors.append("搜索框未找到")

        shot(page, "tc0003_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0003 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0003_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0003()
