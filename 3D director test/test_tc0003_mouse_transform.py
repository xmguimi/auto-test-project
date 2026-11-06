# -*- coding: utf-8 -*-
"""
TC-0003: 3D导演台-鼠标操作移动/旋转/缩放变换模式
默认3D工作台已打开，测试变换模式切换
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

REAL_GENERATE = True


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
    print("TC-0003: 3D导演台-鼠标操作变换模式", flush=True)
    print("=" * 60, flush=True)

    # 1. 选中角色01
    print("\n1. 选中角色01", flush=True)
    try:
        role_btn = page.locator("text=角色01").first
        if role_btn.count() > 0:
            role_btn.click(force=True)
            time.sleep(1)
            print("   ✅ 已选中角色01", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到角色01", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 选中失败: {e}", flush=True)
        results.append(False)

    # 2. 点击移动变换模式
    print("\n2. 点击移动变换模式", flush=True)
    try:
        move_btn = page.locator("[class*='move'], [title*='移动']").first
        if move_btn.count() > 0:
            move_btn.click(force=True)
            time.sleep(0.5)
            print("   ✅ 移动模式已切换", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到移动模式按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 3. 点击旋转变换模式
    print("\n3. 点击旋转变换模式", flush=True)
    try:
        rotate_btn = page.locator("[class*='rotate'], [title*='旋转']").first
        if rotate_btn.count() > 0:
            rotate_btn.click(force=True)
            time.sleep(0.5)
            print("   ✅ 旋转模式已切换", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到旋转模式按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 4. 点击缩放变换模式
    print("\n4. 点击缩放变换模式", flush=True)
    try:
        scale_btn = page.locator("[class*='scale'], [title*='缩放']").first
        if scale_btn.count() > 0:
            scale_btn.click(force=True)
            time.sleep(0.5)
            shot(page, "tc0003_mouse_modes.png")
            print("   ✅ 缩放模式已切换", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到缩放模式按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
