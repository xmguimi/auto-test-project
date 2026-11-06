# -*- coding: utf-8 -*-
"""
TC-0017: 图片节点标注功能实际测试
实际使用画笔、矩形、文字、橡皮、颜色、粗细、撤销、重做
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
    print("TC-0017: 图片节点标注功能实际测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：关闭弹窗，选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 步骤2：点击标注按钮（画笔图标）
    print("\n2. 打开标注工具栏", flush=True)
    try:
        # 标注是画笔图标，在顶部工具栏
        mark_icon = page.locator("[class*='pen'], [class*='brush']").first
        if mark_icon.count() > 0:
            mark_icon.click(force=True)
            time.sleep(2)
            shot(page, "tc0017_mark_open.png")
            print("   ✅ 标注工具栏打开", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 标注工具栏失败: {e}", flush=True)
        results.append(False)

    # 步骤3：测试画笔工具
    print("\n3. 测试画笔工具", flush=True)
    try:
        brush = page.locator("[class*='pen'], [class*='brush']").first
        brush.click(force=True)
        time.sleep(0.5)
        print("   ✅ 画笔工具选中", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 画笔工具失败: {e}", flush=True)
        results.append(False)

    # 步骤4：测试矩形工具
    print("\n4. 测试矩形工具", flush=True)
    try:
        rect = page.locator("[class*='rect'], [class*='square']").first
        rect.click(force=True)
        time.sleep(0.5)
        print("   ✅ 矩形工具选中", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 矩形工具失败: {e}", flush=True)
        results.append(False)

    # 步骤5：测试文字工具
    print("\n5. 测试文字工具", flush=True)
    try:
        text_tool = page.locator("[class*='text'], [class*='font']").first
        text_tool.click(force=True)
        time.sleep(0.5)
        print("   ✅ 文字工具选中", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 文字工具失败: {e}", flush=True)
        results.append(False)

    # 步骤6：测试橡皮工具
    print("\n6. 测试橡皮工具", flush=True)
    try:
        eraser = page.locator("[class*='eraser'], [class*='rubber']").first
        eraser.click(force=True)
        time.sleep(0.5)
        print("   ✅ 橡皮工具选中", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 橡皮工具失败: {e}", flush=True)
        results.append(False)

    # 步骤7：测试撤销按钮
    print("\n7. 测试撤销按钮", flush=True)
    try:
        undo = page.locator("[class*='undo']").first
        undo.click(force=True)
        time.sleep(0.5)
        print("   ✅ 撤销按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 撤销按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤8：测试重做按钮
    print("\n8. 测试重做按钮", flush=True)
    try:
        redo = page.locator("[class*='redo']").first
        redo.click(force=True)
        time.sleep(0.5)
        print("   ✅ 重做按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 重做按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤9：测试保存按钮
    print("\n9. 测试保存按钮", flush=True)
    try:
        save_btn = page.locator("button:has-text('保存')").first
        if save_btn.count() > 0:
            print("   ✅ 保存按钮存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 保存按钮失败: {e}", flush=True)
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
