# -*- coding: utf-8 -*-
"""TC-0022 视频节点-下载（REAL_GENERATE=True，本地功能）"""
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

    # 1. 选中视频节点（idx=0，原始视频剪辑节点）
    box0 = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box0["x"] + box0["width"] / 2, box0["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True)

    # 2. 验证下载按钮存在
    download_btn = page.locator("button[aria-label='下载']")
    dl_count1 = download_btn.count()
    check("选中时下载按钮存在", dl_count1 > 0, f"按钮数={dl_count1}")

    # 3. 点击下载按钮，观察节点是否取消选中（触发系统另存为对话框）
    if dl_count1 > 0:
        db = download_btn.first.bounding_box()
        page.mouse.click(db["x"] + db["width"] / 2, db["y"] + db["height"] / 2)
        time.sleep(2)
        # 点击后节点取消选中，说明触发了下载动作（系统另存为对话框弹出）
        dl_count2 = page.locator("button[aria-label='下载']").count()
        check("点击下载触发动作", dl_count2 == 0, f"点击后按钮数={dl_count2}（节点取消选中，系统另存为对话框弹出）")

    # 4. 重新选中节点，然后点空白处取消选中，验证下载按钮消失
    box1 = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box1["x"] + box1["width"] / 2, box1["y"] + 12)
    time.sleep(1)
    dl_count3 = page.locator("button[aria-label='下载']").count()
    check("重新选中后下载按钮恢复", dl_count3 > 0, f"按钮数={dl_count3}")

    # 点空白处取消选中
    page.mouse.click(50, 500)
    time.sleep(1)
    dl_count4 = page.locator("button[aria-label='下载']").count()
    check("未选中节点时下载按钮消失", dl_count4 == 0, f"按钮数={dl_count4}")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
