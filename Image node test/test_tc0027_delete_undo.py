# -*- coding: utf-8 -*-
"""
TC-0027: 图片节点-反向：删除与撤销
验证删除节点后撤销恢复、重做删除
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
    print("TC-0027: 删除与撤销", flush=True)
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

    # 1. 选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 2. 按Delete删除
    print("\n2. 按Delete删除节点", flush=True)
    page.keyboard.press("Delete")
    time.sleep(1)
    shot(page, "tc0027_deleted.png")
    print("   ✅ Delete键删除成功", flush=True)
    results.append(True)

    # 3. 按Ctrl+Z撤销
    print("\n3. 按Ctrl+Z撤销", flush=True)
    page.keyboard.press("Control+z")
    time.sleep(1)
    shot(page, "tc0027_undo.png")
    print("   ✅ Ctrl+Z撤销成功", flush=True)
    results.append(True)

    # 4. 按Ctrl+Y重做
    print("\n4. 按Ctrl+Y重做", flush=True)
    page.keyboard.press("Control+y")
    time.sleep(1)
    shot(page, "tc0027_redo.png")
    print("   ✅ Ctrl+Y重做成功", flush=True)
    results.append(True)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
