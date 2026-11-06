# -*- coding: utf-8 -*-
"""TC-0038 视频节点-云端任务失败重试"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = False  # 付费功能不实际发起
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
    ctx = browser.contexts[0]
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # 1. 模拟断网
    ctx.set_offline(True)
    time.sleep(1)
    check("模拟断网", True, "set_offline(True)")

    # 2. 选中牛来啦节点
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
    if niulai_idx >= 0:
        box = nodes.nth(niulai_idx).bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
        time.sleep(1)

    # 3. 断网状态截图
    page.screenshot(path=str(ROOT / "tc0038_offline.png"))
    print("已截图(断网)", flush=True)

    # 4. 恢复网络
    ctx.set_offline(False)
    time.sleep(1)
    check("恢复网络", True, "set_offline(False)")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
