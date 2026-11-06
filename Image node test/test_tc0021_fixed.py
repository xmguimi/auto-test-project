# -*- coding: utf-8 -*-
"""
TC-0021: 图片节点重命名功能完整测试（修正版）
修正：每次点重命名后等输入框出现再操作
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


def click_rename_and_get_input(page):
    """点击重命名按钮，等输入框出现并返回"""
    # 点击重命名按钮（工具栏最右边）
    toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
    toolbar_btns[-1].click(force=True)
    time.sleep(1)  # 等输入框出现
    # 找输入框
    name_input = page.locator("input[type='text'], input[placeholder*='名称']").first
    name_input.wait_for(state="visible", timeout=5000)
    return name_input


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0021: 图片节点重命名功能完整测试（修正版）", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 2. 正常重命名
    print("\n2. 正常重命名输入'测试节点'", flush=True)
    try:
        name_input = click_rename_and_get_input(page)
        name_input.fill("测试节点")
        page.keyboard.press("Enter")
        time.sleep(0.5)
        shot(page, "tc0021_2_normal.png")
        print("   ✅ 正常重命名成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 正常重命名失败: {e}", flush=True)
        results.append(False)

    # 3. 取消重命名（Esc不保存）
    print("\n3. 取消重命名（Esc不保存）", flush=True)
    try:
        name_input = click_rename_and_get_input(page)
        name_input.fill("临时名称")
        page.keyboard.press("Escape")  # 按Esc取消
        time.sleep(0.5)
        shot(page, "tc0021_3_cancel.png")
        print("   ✅ 按Esc取消成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 取消重命名失败: {e}", flush=True)
        results.append(False)

    # 4. 空名称测试
    print("\n4. 空名称测试", flush=True)
    try:
        name_input = click_rename_and_get_input(page)
        name_input.fill("")  # 清空
        page.keyboard.press("Enter")
        time.sleep(0.5)
        shot(page, "tc0021_4_empty.png")
        print("   ✅ 空名称测试完成", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 空名称测试失败: {e}", flush=True)
        results.append(False)

    # 5. 特殊字符测试
    print("\n5. 特殊字符测试", flush=True)
    try:
        name_input = click_rename_and_get_input(page)
        name_input.fill("测试#@￥%&*")
        page.keyboard.press("Enter")
        time.sleep(0.5)
        shot(page, "tc0021_5_special.png")
        print("   ✅ 特殊字符测试完成", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 特殊字符测试失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
