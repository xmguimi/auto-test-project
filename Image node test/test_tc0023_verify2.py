# -*- coding: utf-8 -*-
"""
TC-0023: 验证保存到资产库按钮（面板关闭后）
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

    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 选中图片节点
    print("1. 选中图片节点", flush=True)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)

    # 2. 关闭右侧面板
    print("2. 关闭右侧面板", flush=True)
    close_btn = page.locator("button:has-text('无助手')").first
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1)

    # 3. 点击倒数第四个按钮（文件夹+加号图标）
    print("3. 点击倒数第四个按钮", flush=True)
    toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
    print(f"   共 {len(toolbar_btns)} 个按钮", flush=True)
    # 倒数第四个
    btn = toolbar_btns[-4]
    btn.click(force=True)
    time.sleep(2)
    shot(page, "tc0023_final_check.png")
    print("   已点击", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
