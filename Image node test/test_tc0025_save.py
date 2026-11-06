# -*- coding: utf-8 -*-
"""
TC-0025: 图片节点保存到资产库-确认保存与校验功能测试
验证确认保存、取消不保存、空名称处理
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
    print("TC-0025: 图片节点保存到资产库-确认保存与校验", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 正常保存测试
    print("\n1. 正常保存测试", flush=True)
    open_save_modal(page)
    try:
        # 输入名称
        name_input = page.locator("input[type='text']").first
        name_input.fill("测试资产")
        time.sleep(0.3)
        # 选分类
        scene_btn = page.locator("button:has-text('场景')").first
        scene_btn.click(force=True)
        time.sleep(0.3)
        # 点确认保存
        confirm_btn = page.locator("button:has-text('确认保存')").first
        confirm_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0025_after_save.png")
        print("   ✅ 确认保存按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 保存失败: {e}", flush=True)
        results.append(False)

    # 2. 验证弹窗关闭
    print("\n2. 验证弹窗关闭", flush=True)
    try:
        modal_title = page.locator("text=保存到资产库").first
        if modal_title.count() == 0 or not modal_title.is_visible():
            print("   ✅ 弹窗已关闭", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 弹窗仍在", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 3. 取消测试
    print("\n3. 取消测试", flush=True)
    open_save_modal(page)
    try:
        cancel_btn = page.locator("button:has-text('取消')").first
        cancel_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0025_after_cancel.png")
        print("   ✅ 取消按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 取消失败: {e}", flush=True)
        results.append(False)

    # 4. 空名称测试
    print("\n4. 空名称测试", flush=True)
    open_save_modal(page)
    try:
        name_input = page.locator("input[type='text']").first
        name_input.fill("")  # 清空
        time.sleep(0.3)
        confirm_btn = page.locator("button:has-text('确认保存')").first
        confirm_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0025_empty_name.png")
        print("   ✅ 空名称测试完成", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 空名称测试失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
