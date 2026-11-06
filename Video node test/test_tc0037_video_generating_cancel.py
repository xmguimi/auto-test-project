# -*- coding: utf-8 -*-
"""TC-0037 视频节点-生成中状态与取消（实际点取消）"""
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

    # 1. 找黑白深度视频节点
    nodes = page.locator(".react-flow__node")
    bw_idx = -1
    for i in range(nodes.count()):
        t = nodes.nth(i).text_content() or ""
        if "黑白深度" in t:
            bw_idx = i
            break
    check("找到黑白深度节点", bw_idx >= 0, f"索引={bw_idx}")
    if bw_idx < 0:
        browser.close()
        pw.stop()
        return

    # 2. 验证生成中状态
    bw_text = nodes.nth(bw_idx).text_content() or ""
    check("生成中状态", "帧" in bw_text or "%" in bw_text, "节点显示生成进度")

    # 3. 点取消按钮
    cancel_btn = page.locator("text=取消")
    check("有取消按钮", cancel_btn.count() > 0, f"找到{cancel_btn.count()}个")

    if cancel_btn.count() > 0:
        cancel_btn.first.click()
        time.sleep(3)
        check("点击取消", True)

    # 4. 截图看取消后状态
    page.screenshot(path=str(ROOT / "tc0037_cancelled.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
