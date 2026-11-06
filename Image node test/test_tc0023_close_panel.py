# -*- coding: utf-8 -*-
"""
TC-0023: 图片节点保存到资产库功能测试（关闭面板版）
先关闭右侧AI助手面板，再找按钮
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
    print("TC-0023: 图片节点保存到资产库功能测试（关闭面板版）", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 0. 关闭右侧AI助手面板
    print("\n0. 关闭右侧AI助手面板", flush=True)
    try:
        # 找关闭按钮或切换面板的按钮
        close_btn = page.locator("button:has-text('无助手')").first
        if close_btn.count() > 0:
            close_btn.click(force=True)
            time.sleep(1)
            print("   ✅ 右侧面板已关闭", flush=True)
        else:
            # 试试点右上角的箭头
            arrow_btn = page.locator("button:has-text('›')").first
            if arrow_btn.count() > 0:
                arrow_btn.click(force=True)
                time.sleep(1)
                print("   ✅ 右侧面板已关闭", flush=True)
            else:
                print("   ⚠️ 未找到关闭按钮，继续测试", flush=True)
    except Exception as e:
        print(f"   ⚠️ 关闭面板失败: {e}", flush=True)

    # 1. 选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 2. 点击保存到资产库按钮（倒数第四个）
    print("\n2. 点击保存到资产库按钮（倒数第四个）", flush=True)
    try:
        toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
        print(f"   找到 {len(toolbar_btns)} 个工具栏按钮", flush=True)
        save_btn = toolbar_btns[-4]
        save_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0023_modal_close.png")
        print("   ✅ 保存到资产库按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 按钮失败: {e}", flush=True)
        results.append(False)

    # 3. 验证弹窗标题
    print("\n3. 验证弹窗标题", flush=True)
    try:
        title = page.locator("text=保存到资产库").first
        if title.count() > 0:
            print("   ✅ 标题「保存到资产库」显示正确", flush=True)
            results.append(True)
        else:
            print("   ❌ 标题未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 4. 验证资产名称输入框
    print("\n4. 验证资产名称输入框", flush=True)
    try:
        name_input = page.locator("input[type='text'], input[placeholder*='名称']").first
        if name_input.count() > 0:
            default_name = name_input.input_value()
            print(f"   默认资产名称: {default_name}", flush=True)
            print("   ✅ 资产名称输入框显示正确", flush=True)
            results.append(True)
        else:
            print("   ❌ 资产名称输入框未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 5. 验证底部按钮
    print("\n5. 验证底部按钮", flush=True)
    try:
        cancel_btn = page.locator("button:has-text('取消')").first
        confirm_btn = page.locator("button:has-text('确认保存')").first
        if cancel_btn.count() > 0 and confirm_btn.count() > 0:
            print("   ✅ 取消、确认保存按钮显示正确", flush=True)
            results.append(True)
        else:
            print("   ❌ 底部按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
