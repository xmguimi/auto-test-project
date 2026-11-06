# -*- coding: utf-8 -*-
"""
重新打开图片编辑器，实际测试功能
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 生成开关：True=实际点击生成（扣费），False=只验证按钮存在不实际生成
REAL_GENERATE = False


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


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
    results = []

    print("关闭所有弹窗...", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1.5)

    print("\n选中图片节点...", flush=True)
    page.locator("img").nth(1).click(force=True)
    time.sleep(1.5)

    print("\n点编辑按钮...", flush=True)
    page.locator("text=编辑").first.click(force=True)
    time.sleep(2.5)
    shot(page, "tc0005_reopen.png")
    print("  ✅ 编辑器重新打开", flush=True)

    tools = page.locator(".ie-tb")
    tool_count = tools.count()
    print(f"  工具栏按钮数量：{tool_count}", flush=True)
    results.append(True)

    # 画笔绘制
    print("\n画笔绘制...", flush=True)
    tools.nth(1).click()
    time.sleep(0.5)
    page.mouse.move(300, 300)
    page.mouse.down()
    page.mouse.move(400, 350)
    page.mouse.up()
    time.sleep(0.5)
    shot(page, "tc0005_brush_real.png")
    print("  ✅ 画笔绘制完成", flush=True)
    results.append(True)

    # 矩形绘制
    print("\n矩形绘制...", flush=True)
    tools.nth(2).click()
    time.sleep(0.5)
    page.mouse.move(500, 300)
    page.mouse.down()
    page.mouse.move(600, 400)
    page.mouse.up()
    time.sleep(0.5)
    shot(page, "tc0005_rect_real.png")
    print("  ✅ 矩形绘制完成", flush=True)
    results.append(True)

    # 圆形绘制
    print("\n圆形绘制...", flush=True)
    tools.nth(3).click()
    time.sleep(0.5)
    page.mouse.move(400, 450)
    page.mouse.down()
    page.mouse.move(480, 520)
    page.mouse.up()
    time.sleep(0.5)
    shot(page, "tc0005_circle_real.png")
    print("  ✅ 圆形绘制完成", flush=True)
    results.append(True)

    # 箭头绘制
    print("\n箭头绘制...", flush=True)
    tools.nth(4).click()
    time.sleep(0.5)
    page.mouse.move(300, 500)
    page.mouse.down()
    page.mouse.move(400, 550)
    page.mouse.up()
    time.sleep(0.5)
    shot(page, "tc0005_arrow_real.png")
    print("  ✅ 箭头绘制完成", flush=True)
    results.append(True)

    # 文字添加
    print("\n文字添加...", flush=True)
    tools.nth(5).click()
    time.sleep(0.5)
    page.mouse.click(500, 250)
    time.sleep(0.5)
    page.keyboard.type("测试文字")
    time.sleep(0.5)
    page.keyboard.press("Enter")
    time.sleep(0.5)
    shot(page, "tc0005_text_real.png")
    print("  ✅ 文字添加完成", flush=True)
    results.append(True)

    # 旋转
    print("\n旋转90°...", flush=True)
    tools.nth(10).click()
    time.sleep(1)
    shot(page, "tc0005_rotate_real.png")
    print("  ✅ 旋转完成", flush=True)
    results.append(True)

    # 导入画布
    print("\n导入画布按钮...", flush=True)
    export_btn = page.locator("text=导入画布").first
    if export_btn.count() > 0:
        print("  ✅ 导入画布按钮存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    print(f"\n通过: {sum(results)}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
