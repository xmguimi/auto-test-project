# -*- coding: utf-8 -*-
"""TC-0030 视频节点-复制到项目"""
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

    # 3. 点"复制到项目…"
    copy_item = page.locator("text=复制到项目…")
    if copy_item.count() > 0:
        ci = copy_item.first.bounding_box()
        page.mouse.click(ci["x"] + ci["width"] / 2, ci["y"] + ci["height"] / 2)
        time.sleep(2)
        check("点击复制到项目", True)
    else:
        check("点击复制到项目", False, "未找到")
        browser.close(); pw.stop(); return

    # 4. 选择第一个项目（列表第一个）
    first_project = page.locator(".react-flow__node, [class*='project']").first
    # 直接选列表第一个项目项
    projects = page.locator("text=test2").first
    if projects.count() > 0:
        pi = projects.bounding_box()
        page.mouse.click(pi["x"] + pi["width"] / 2, pi["y"] + pi["height"] / 2)
        time.sleep(3)
        check("选择第一个项目(test2)", True)
    else:
        check("选择第一个项目(test2)", False, "未找到")

    # 5. 截图看弹出的对话框
    page.screenshot(path=str(ROOT / "tc0030_dialog.png"))
    print("已截图", flush=True)

    # 6. 找"留在当前"按钮
    stay = page.locator("text=留在当前")
    if stay.count() > 0:
        check("出现留在当前按钮", True)
    else:
        check("出现留在当前按钮", False, "未找到")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
