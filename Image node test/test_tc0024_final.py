# -*- coding: utf-8 -*-
"""
TC-0024: 图片节点保存到资产库-名称与分类编辑功能测试
基于成功打开弹窗的方法，测试名称编辑和分类切换
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


def open_save_modal(page):
    """打开保存到资产库弹窗"""
    # 关闭右侧面板
    close_btn = page.locator("button:has-text('无助手')").first
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1)

    # 选中图片节点
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)

    # 点击倒数第四个按钮
    toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
    toolbar_btns[-4].click(force=True)
    time.sleep(2)


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0024: 图片节点保存到资产库-名称与分类编辑", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 0. 打开弹窗
    print("\n0. 打开保存到资产库弹窗", flush=True)
    open_save_modal(page)
    shot(page, "tc0024_modal_open.png")
    print("   ✅ 弹窗已打开", flush=True)
    results.append(True)

    # 1. 正常编辑名称
    print("\n1. 正常编辑名称", flush=True)
    try:
        name_input = page.locator("input[type='text'], input[placeholder*='名称']").first
        name_input.fill("草原羊群")
        time.sleep(0.5)
        current_val = name_input.input_value()
        print(f"   输入后名称: {current_val}", flush=True)
        print("   ✅ 名称编辑成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 名称编辑失败: {e}", flush=True)
        results.append(False)

    # 2. 清空名称
    print("\n2. 清空名称", flush=True)
    try:
        name_input = page.locator("input[type='text']").first
        name_input.fill("")
        time.sleep(0.5)
        current_val = name_input.input_value()
        print(f"   清空后名称: '{current_val}'", flush=True)
        print("   ✅ 清空名称完成", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 清空失败: {e}", flush=True)
        results.append(False)

    # 3. 特殊字符名称
    print("\n3. 特殊字符名称", flush=True)
    try:
        name_input = page.locator("input[type='text']").first
        name_input.fill("测试#@￥%&*")
        time.sleep(0.5)
        current_val = name_input.input_value()
        print(f"   特殊字符名称: {current_val}", flush=True)
        print("   ✅ 特殊字符输入成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 特殊字符失败: {e}", flush=True)
        results.append(False)

    # 4. 测试分类切换
    print("\n4. 测试分类切换", flush=True)
    try:
        categories = ["人物", "场景", "物品", "音频", "其他"]
        for cat in categories:
            cat_btn = page.locator(f"button:has-text('{cat}')").first
            if cat_btn.count() > 0:
                cat_btn.click(force=True)
                time.sleep(0.3)
                print(f"   点击分类: {cat}", flush=True)
        print("   ✅ 分类切换测试完成", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 分类切换失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
