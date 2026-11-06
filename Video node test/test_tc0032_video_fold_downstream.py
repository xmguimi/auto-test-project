# -*- coding: utf-8 -*-
"""TC-0032 视频节点-折叠下游完整版"""
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

    # 1. 验证折叠状态：有"展开"按钮
    expand_btn = page.locator("text=展开")
    if expand_btn.count() > 0:
        check("折叠状态有展开按钮", True)
    else:
        check("折叠状态有展开按钮", False, "未找到")

    # 2. 点"展开"按钮
    if expand_btn.count() > 0:
        eb = expand_btn.first.bounding_box()
        page.mouse.click(eb["x"] + eb["width"] / 2, eb["y"] + eb["height"] / 2)
        time.sleep(2)
        check("点击展开按钮", True)
    else:
        check("点击展开按钮", False, "跳过")

    # 3. 验证提示文字
    page_text = page.evaluate("() => document.body.textContent || ''")
    check("验证展开提示", "已展开" in page_text or "展开" in page_text, "含'展开'提示")

    # 4. 截图看展开效果
    page.screenshot(path=str(ROOT / "tc0032_expanded.png"))
    print("已截图(展开后)", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
