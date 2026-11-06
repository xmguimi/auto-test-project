# -*- coding: utf-8 -*-
"""
TC-0026: 图片节点-反向：未选中节点操作工具栏
验证未选中节点时工具栏不显示
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


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
    print("TC-0026: 未选中节点操作工具栏", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 0. 关闭右侧面板
    print("\n0. 关闭右侧面板", flush=True)
    close_btn = page.locator("button:has-text('无助手')").first
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1)

    # 1. 不选中任何节点，点击空白处
    print("\n1. 不选中任何节点，点击空白处", flush=True)
    page.mouse.click(500, 300)
    time.sleep(1)
    print("   ✅ 已点击空白处，取消选中", flush=True)
    results.append(True)

    # 2. 验证工具栏不显示
    print("\n2. 验证工具栏不显示", flush=True)
    try:
        edit_btn = page.locator("text=编辑").first
        if edit_btn.count() == 0:
            print("   ✅ 工具栏不显示（未选中节点时无工具栏）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 工具栏仍显示", flush=True)
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
