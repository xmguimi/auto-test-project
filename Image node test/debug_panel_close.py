# -*- coding: utf-8 -*-
"""
调试：先关闭右侧AI助手面板，再探查工具栏按钮
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    page.screenshot(path=str(SHOT_DIR / name))
    print(f"  [SHOT] {name}", flush=True)


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


def test():
    pw, browser, page = connect()
    time.sleep(2)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 选中图片节点
    print("1. 选中图片节点", flush=True)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    shot(page, "debug_1_selected.png")

    # 2. 关闭右侧面板 - 尝试多种方法
    print("\n2. 关闭右侧AI助手面板", flush=True)
    # 方法1：点"无助手"按钮
    close_btn = page.locator("button:has-text('无助手')").first
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1)
        print("   方法1：点击'无助手'按钮", flush=True)
    else:
        # 方法2：点右上角箭头
        arrow_btn = page.locator("button:has-text('›')").first
        if arrow_btn.count() > 0:
            arrow_btn.click(force=True)
            time.sleep(1)
            print("   方法2：点击箭头按钮", flush=True)
        else:
            # 方法3：按Esc
            page.keyboard.press("Escape")
            time.sleep(1)
            print("   方法3：按Esc", flush=True)

    shot(page, "debug_2_panel_closed.png")

    # 3. 列出所有工具栏按钮
    print("\n3. 所有工具栏按钮：", flush=True)
    toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
    print(f"   共 {len(toolbar_btns)} 个按钮", flush=True)
    for i, btn in enumerate(toolbar_btns):
        try:
            text = btn.inner_text()
            cls = btn.get_attribute("class") or ""
            print(f"   按钮{i}: text='{text}', class='{cls[:50]}'", flush=True)
        except:
            pass

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
