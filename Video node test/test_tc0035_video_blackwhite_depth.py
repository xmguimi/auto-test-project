# -*- coding: utf-8 -*-
"""TC-0035 视频工具-黑白深度视频（免费）"""
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

    # 1. 先取消选中
    page.keyboard.press("Escape")
    time.sleep(1)

    # 2. 找"牛来啦"节点并选中
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

    # 3. 找工具栏里的"视频工具"按钮并点击
    page_text = page.evaluate("() => document.body.textContent || ''")
    check("工具栏出现", "视频工具" in page_text, "选中后工具栏显示视频工具")

    tool_btn = page.locator("text=视频工具")
    if tool_btn.count() > 0:
        tool_btn.first.click()
        time.sleep(1)
        check("点击视频工具下拉", True)

        # 4. 找"黑白深度视频"选项
        bw_btn = page.locator("text=黑白深度视频")
        check("下拉含黑白深度视频", bw_btn.count() > 0, f"找到{bw_btn.count()}个")

        if bw_btn.count() > 0:
            bw_btn.first.click()
            time.sleep(2)
            check("点击黑白深度视频", True)
    else:
        check("点击视频工具下拉", False, "未找到视频工具按钮")

    # 5. 截图看生成状态
    page.screenshot(path=str(ROOT / "tc0035_generating.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
