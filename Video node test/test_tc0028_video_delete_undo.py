# -*- coding: utf-8 -*-
"""TC-0028 视频节点-删除与撤销（REAL_GENERATE=True，本地功能）"""
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

    # 2. 记录删除前节点数
    count_before = get_node_count(page)
    print(f"删除前节点数: {count_before}", flush=True)

    # 3. 按Delete键删除
    page.keyboard.press("Delete")
    time.sleep(2)
    check("按Delete删除", True)

    # 4. 验证节点数减少
    count_after_delete = get_node_count(page)
    check("删除后节点数减少", count_after_delete < count_before, f"删除前={count_before} 删除后={count_after_delete} 减少了{count_before-count_after_delete}个")

    # 5. 按Ctrl+Z撤销
    page.keyboard.press("Control+z")
    time.sleep(2)
    check("按Ctrl+Z撤销", True)

    # 6. 验证节点数恢复
    count_after_undo = get_node_count(page)
    check("撤销后节点数恢复", count_after_undo == count_before, f"删除前={count_before} 撤销后={count_after_undo}")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
