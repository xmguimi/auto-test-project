# -*- coding: utf-8 -*-
"""TC-0027 视频节点-创建副本关联节点（REAL_GENERATE=True，本地功能）"""
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


def get_node_count(page):
    return page.evaluate("() => document.querySelectorAll('.react-flow__node').length")


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
    box0 = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box0["x"] + box0["width"] / 2, box0["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True)

    # 2. 记录创建前节点数
    count_before = get_node_count(page)
    print(f"创建前节点数: {count_before}", flush=True)

    # 3. 右键点击节点
    page.mouse.click(box0["x"] + box0["width"] / 2, box0["y"] + box0["height"] / 2, button="right")
    time.sleep(1)
    check("右键点击节点", True)

    # 4. 点"创建副本关联节点"
    dup_link = page.locator("text=创建副本关联节点")
    if dup_link.count() > 0:
        dl = dup_link.first.bounding_box()
        page.mouse.click(dl["x"] + dl["width"] / 2, dl["y"] + dl["height"] / 2)
        time.sleep(1)
        check("点击创建副本关联节点", True)
    else:
        check("点击创建副本关联节点", False, "未找到")
        browser.close(); pw.stop(); return

    # 5. 点"直属节点"
    direct_btn = page.locator("text=直属节点")
    if direct_btn.count() > 0:
        db = direct_btn.first.bounding_box()
        page.mouse.click(db["x"] + db["width"] / 2, db["y"] + db["height"] / 2)
        time.sleep(2)
        check("选择直属节点模式", True)
    else:
        check("选择直属节点模式", False, "未找到")

    # 6. 验证节点数增加
    count_after = get_node_count(page)
    check("直属副本节点出现", count_after > count_before, f"创建前={count_before} 创建后={count_after} 增加了{count_after-count_before}个")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
