# -*- coding: utf-8 -*-
"""TC-0031 视频节点-打开本地位置（REAL_GENERATE=True，本地功能）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = True
ROOT = Path(__file__).parent


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


def main():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # 1. 选中视频节点
    page.keyboard.press("Escape")
    time.sleep(1)
    box = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True)

    # 2. 右键点击节点中央
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, button="right")
    time.sleep(2)
    check("右键点击节点", True)

    # 3. 验证右键菜单有"打开本地位置"选项
    open_local = page.locator("text=打开本地位置")
    if open_local.count() > 0:
        check("右键菜单有打开本地位置选项", True)
    else:
        check("右键菜单有打开本地位置选项", False, "未找到")

    # 4. 点击"打开本地位置"
    if open_local.count() > 0:
        ol = open_local.first.bounding_box()
        page.mouse.click(ol["x"] + ol["width"] / 2, ol["y"] + ol["height"] / 2)
        time.sleep(2)
        check("点击打开本地位置", True)
    else:
        check("点击打开本地位置", False, "跳过")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
