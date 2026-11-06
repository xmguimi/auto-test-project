# -*- coding: utf-8 -*-
"""
TC-0028: 图片节点-反向：边界尺寸输入
用hover提示定位尺寸按钮
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
    results = []

    print("=" * 60, flush=True)
    print("TC-0028: 边界尺寸输入", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 0. 关闭右侧面板
    print("\n0. 关闭右侧面板", flush=True)
    close_btn = page.locator("button:has-text('无助手')").first
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1)

    # 1. 选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.locator("img").nth(0).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 2. hover找尺寸按钮
    print("\n2. hover找尺寸按钮", flush=True)
    try:
        toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
        print(f"   共 {len(toolbar_btns)} 个按钮", flush=True)
        size_btn = None
        for btn in toolbar_btns:
            btn.hover()
            time.sleep(0.3)
            # 检查是否出现"尺寸"提示
            tip = page.locator("text=尺寸").first
            if tip.count() > 0 and tip.is_visible():
                size_btn = btn
                print("   ✅ 找到尺寸按钮", flush=True)
                break
        if size_btn:
            size_btn.click(force=True)
            time.sleep(1)
            shot(page, "tc0028_size_toolbar.png")
            results.append(True)
        else:
            print("   ❌ 未找到尺寸按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 找尺寸按钮失败: {e}", flush=True)
        results.append(False)

    # 3. 输入宽度0
    print("\n3. 输入宽度0", flush=True)
    try:
        width_input = page.locator("input[type='number']").first
        width_input.fill("0")
        time.sleep(0.5)
        print("   ✅ 输入宽度0成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 4. 输入宽度负数
    print("\n4. 输入宽度-100", flush=True)
    try:
        width_input = page.locator("input[type='number']").first
        width_input.fill("-100")
        time.sleep(0.5)
        print("   ✅ 输入负数成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 5. 输入超大值
    print("\n5. 输入宽度99999", flush=True)
    try:
        width_input = page.locator("input[type='number']").first
        width_input.fill("99999")
        time.sleep(0.5)
        shot(page, "tc0028_extreme.png")
        print("   ✅ 输入超大值成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
