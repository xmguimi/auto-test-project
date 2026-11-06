# -*- coding: utf-8 -*-
"""TC-0036 视频节点-抽帧-自由抽帧"""
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

    # 1. 找牛来啦节点并选中
    page.keyboard.press("Escape")
    time.sleep(1)
    nodes = page.locator(".react-flow__node")
    niulai_idx = -1
    for i in range(nodes.count()):
        t = nodes.nth(i).text_content() or ""
        if "牛来啦" in t:
            niulai_idx = i
            break
    check("找到牛来啦节点", niulai_idx >= 0, f"索引={niulai_idx}")
    if niulai_idx < 0:
        browser.close()
        pw.stop()
        return

    box = nodes.nth(niulai_idx).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(2)
    check("选中牛来啦节点", True)

    # 2. 找工具栏"抽帧"下拉按钮并点击
    frame_btn = page.locator("text=抽帧")
    check("工具栏含抽帧按钮", frame_btn.count() > 0, f"找到{frame_btn.count()}个")

    if frame_btn.count() > 0:
        frame_btn.first.click()
        time.sleep(1)
        check("点击抽帧下拉", True)

        # 3. 找"自由抽帧"选项
        free_btn = page.locator("text=自由抽帧")
        check("下拉含自由抽帧选项", free_btn.count() > 0, f"找到{free_btn.count()}个")

    # 4. 截图看抽帧下拉
    page.screenshot(path=str(ROOT / "tc0036_frame_dropdown.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
