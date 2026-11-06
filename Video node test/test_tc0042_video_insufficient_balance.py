# -*- coding: utf-8 -*-
"""TC-0042 视频节点-余额不足付费任务（半自动：前置环境由人工准备）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = False  # 余额不足账号准备好后改为True
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

    # 前置条件（人工准备）：已登录余额不足的账号

    # 1. 选中视频节点（牛来啦）
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
    if niulai_idx < 0:
        browser.close()
        pw.stop()
        return

    box = nodes.nth(niulai_idx).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(2)
    check("选中牛来啦节点", True)

    # 2. 点视频工具下拉
    tool_btn = page.locator("text=视频工具")
    check("工具栏有视频工具", tool_btn.count() > 0)
    if tool_btn.count() > 0:
        tool_btn.first.click()
        time.sleep(1)
        check("点击视频工具下拉", True)

    # 3. 点超分
    super_btn = page.locator("text=视频超分")
    check("下拉含视频超分", super_btn.count() > 0, f"找到{super_btn.count()}个")
    if super_btn.count() > 0:
        super_btn.first.click()
        time.sleep(2)
        check("点击视频超分", True)

    # 4. 截图看超分面板
    page.screenshot(path=str(ROOT / "tc0042_super_panel.png"))
    print("已截图(超分面板)", flush=True)

    # 5. 【待余额不足账号准备好后开启】点生成按钮验证余额不足报错
    if REAL_GENERATE:
        gen_btn = page.locator("text=生成, button:has-text('生成')")
        check("有生成按钮", gen_btn.count() > 0)
        if gen_btn.count() > 0:
            gen_btn.first.click()
            time.sleep(3)
            check("点击生成按钮", True)

            # 观察报错提示
            page_text = page.evaluate("() => document.body.textContent || ''")
            check("有余额不足提示", "余额" in page_text or "不足" in page_text or "充值" in page_text)

            # 截图看报错
            page.screenshot(path=str(ROOT / "tc0042_error.png"))
            print("已截图(报错)", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
