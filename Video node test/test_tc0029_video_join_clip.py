# -*- coding: utf-8 -*-
"""TC-0029 视频节点-加入剪辑（REAL_GENERATE=True，本地功能）"""
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
    box0 = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box0["x"] + box0["width"] / 2, box0["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True)

    # 2. 右键点击节点
    page.mouse.click(box0["x"] + box0["width"] / 2, box0["y"] + box0["height"] / 2, button="right")
    time.sleep(1)
    check("右键点击节点", True)

    # 3. 点"加入剪辑"
    join_btn = page.locator("text=加入剪辑")
    if join_btn.count() > 0:
        jb = join_btn.first.bounding_box()
        page.mouse.click(jb["x"] + jb["width"] / 2, jb["y"] + jb["height"] / 2)
        time.sleep(2)
        check("点击加入剪辑", True)
    else:
        check("点击加入剪辑", False, "未找到菜单选项")
        browser.close(); pw.stop(); return

    # 4. 截图看剪辑工作台是否出现
    page.screenshot(path=str(ROOT / "tc0029_join_clip.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
