# -*- coding: utf-8 -*-
"""
TC-0006: 3D导演台-下载
默认3D工作台已打开，点击下载按钮验证功能
实际：下载按钮点击后无任何反应，功能无效
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

REAL_GENERATE = True


def shot(page, name):
    page.screenshot(path=str(SHOT_DIR / name))
    print(f"  [SHOT] {name}", flush=True)


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


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0006: 3D导演台-下载", flush=True)
    print("=" * 60, flush=True)

    # 1. 点击下载按钮
    print("\n1. 点击下载按钮", flush=True)
    try:
        download_btn = page.locator("button[aria-label*='下载'], button[aria-label*='下载媒体']").first
        if download_btn.count() > 0:
            download_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0006_after_click.png")
            print("   ✅ 下载按钮点击成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到下载按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 2. 验证是否有下载提示（实际：无任何反应）
    print("\n2. 验证是否有下载提示", flush=True)
    try:
        tip = page.locator("text=下载, text=保存, text=导出").first
        if tip.count() > 0 and tip.is_visible():
            print("   ✅ 有下载相关提示", flush=True)
            results.append(True)
        else:
            print("   ❌ 下载按钮点击后无任何反应，功能无效", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
