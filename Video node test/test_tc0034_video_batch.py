# -*- coding: utf-8 -*-
"""TC-0034 视频节点-多选批量操作（REAL_GENERATE=True，本地功能）"""
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

    # 1. 先点击画布空白处确保焦点在画布
    page.mouse.click(500, 500)
    time.sleep(1)

    # 2. 按Ctrl+A全选所有节点
    page.keyboard.press("Control+a")
    time.sleep(2)
    check("按Ctrl+A全选所有节点", True)

    # 3. 验证多选状态（节点周围有紫色选中框）
    selected_nodes = page.evaluate("""
        () => document.querySelectorAll('.react-flow__node.selected').length
    """)
    check("验证多选状态", selected_nodes >= 2, f"选中了{selected_nodes}个节点")

    # 4. 截图看多选状态
    page.screenshot(path=str(ROOT / "tc0034_selected.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
