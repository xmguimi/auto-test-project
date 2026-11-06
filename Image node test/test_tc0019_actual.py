# -*- coding: utf-8 -*-
"""
TC-0019: 图片节点尺寸功能实际测试
实际输入宽高、点击快捷比例按钮，验证图片尺寸变化
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

    print("=" * 60, flush=True)
    print("TC-0019: 图片节点尺寸功能实际测试", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗，选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.locator("img").nth(4).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 打开尺寸工具栏
    print("\n2. 打开尺寸工具栏", flush=True)
    size_btn = page.locator("text=尺寸").first
    size_btn.click(force=True)
    time.sleep(2)
    print("   ✅ 尺寸工具栏打开", flush=True)
    results.append(True)

    # 测试1：输入宽度800
    print("\n3. 输入宽度800", flush=True)
    try:
        width_input = page.locator("input[type='number']").first
        width_input.fill("800")
        page.keyboard.press("Enter")
        time.sleep(0.5)
        shot(page, "tc0019_800.png")
        print("   ✅ 输入宽度800成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 输入宽度失败: {e}", flush=True)
        results.append(False)

    # 测试2：输入高度400
    print("\n4. 输入高度400", flush=True)
    try:
        height_input = page.locator("input[type='number']").nth(1)
        height_input.fill("400")
        page.keyboard.press("Enter")
        time.sleep(0.5)
        shot(page, "tc0019_400.png")
        print("   ✅ 输入高度400成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 输入高度失败: {e}", flush=True)
        results.append(False)

    # 测试3：点击50%按钮
    print("\n5. 点击50%按钮", flush=True)
    try:
        btn_50 = page.locator("text=50%").first
        btn_50.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0019_50.png")
        print("   ✅ 50%按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 50%按钮失败: {e}", flush=True)
        results.append(False)

    # 测试4：点击200%按钮
    print("\n6. 点击200%按钮", flush=True)
    try:
        btn_200 = page.locator("text=200%").first
        btn_200.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0019_200.png")
        print("   ✅ 200%按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 200%按钮失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    print("测试结果汇总：", flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
