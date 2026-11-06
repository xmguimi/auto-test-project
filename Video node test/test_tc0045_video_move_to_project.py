# -*- coding: utf-8 -*-
"""TC-0047 视频节点-移动到项目（REAL_GENERATE=True，本地功能）"""
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

    # 1. 记录移动前节点数
    count_before = get_node_count(page)
    print(f"移动前节点数: {count_before}", flush=True)

    # 2. 选中视频节点
    page.keyboard.press("Escape")
    time.sleep(1)
    box = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True)

    # 3. 右键点击节点中央
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, button="right")
    time.sleep(2)
    check("右键点击节点", True)

    # 4. 点"移动到项目…"
    move_item = page.locator("text=移动到项目…")
    if move_item.count() > 0:
        mi = move_item.first.bounding_box()
        page.mouse.click(mi["x"] + mi["width"] / 2, mi["y"] + mi["height"] / 2)
        time.sleep(2)
        check("点击移动到项目…", True)
    else:
        check("点击移动到项目…", False, "未找到")
        browser.close(); pw.stop(); return

    # 5. 选择第一个项目
    first_proj = page.locator("text=test2").first
    if first_proj.count() > 0:
        fp = first_proj.bounding_box()
        page.mouse.click(fp["x"] + fp["width"] / 2, fp["y"] + fp["height"] / 2)
        time.sleep(2)
        check("选择目标项目", True)
    else:
        check("选择目标项目", False, "未找到项目")

    # 6. 点"移动"按钮（确认对话框）
    confirm_move = page.locator("button:has-text('移动')")
    if confirm_move.count() > 0:
        cm = confirm_move.first.bounding_box()
        page.mouse.click(cm["x"] + cm["width"] / 2, cm["y"] + cm["height"] / 2)
        time.sleep(3)
        check("点确认移动", True)
    else:
        check("点确认移动", False, "未找到移动按钮")

    # 7. 点"留在当前"
    stay = page.locator("text=留在当前")
    if stay.count() > 0:
        st = stay.first.bounding_box()
        page.mouse.click(st["x"] + st["width"] / 2, st["y"] + st["height"] / 2)
        time.sleep(2)
        check("点留在当前", True)
    else:
        check("点留在当前", False, "未找到")

    # 8. 验证原项目节点被删除（节点数减少）
    count_after = get_node_count(page)
    check("原项目节点被删除", count_after < count_before, f"移动前={count_before} 移动后={count_after} 减少了{count_before-count_after}个")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
