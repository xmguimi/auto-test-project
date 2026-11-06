# -*- coding: utf-8 -*-
"""
TC-0018: 3D导演台-全屏
测试：悬浮提示、点击全屏收起两侧、再次点击展开、快速连续点击
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


def is_panel_expanded(page):
    """检测右侧属性面板是否展开（用'名称'文本的可见性）"""
    name_text = page.locator("text=名称").first
    if name_text.count() > 0 and name_text.is_visible():
        return True
    return False


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0018: 3D导演台-全屏", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮全屏按钮，验证提示
    print("\n1. 悬浮全屏按钮，验证提示", flush=True)
    try:
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        if fullscreen_btn.count() > 0:
            fullscreen_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=全屏").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'全屏'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 全屏按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 记录初始状态（面板展开）
    print("\n2. 记录初始状态", flush=True)
    try:
        if is_panel_expanded(page):
            print("   ✅ 初始状态：右侧面板展开", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 初始状态：右侧面板未展开", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 点击全屏按钮，验证两侧面板收起
    print("\n3. 点击全屏按钮，验证两侧面板收起", flush=True)
    try:
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        fullscreen_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0018_fullscreen_on.png")
        if not is_panel_expanded(page):
            print("   ✅ 点击全屏后，两侧面板收起", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 点击全屏后，面板仍展开", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 再次点击全屏按钮，验证两侧面板展开
    print("\n4. 再次点击全屏按钮，验证两侧面板展开", flush=True)
    try:
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        fullscreen_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0018_fullscreen_off.png")
        if is_panel_expanded(page):
            print("   ✅ 再次点击后，两侧面板展开", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 再次点击后，面板仍收起", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 快速连续点击3次，验证状态正确交替
    print("\n5. 快速连续点击3次，验证状态正确交替", flush=True)
    try:
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        # 快速点击3次
        for i in range(3):
            fullscreen_btn.click(force=True)
            time.sleep(0.2)
        time.sleep(1)
        shot(page, "tc0018_quick_click.png")
        # 初始是展开，点1次收起，点2次展开，点3次收起
        if not is_panel_expanded(page):
            print("   ✅ 快速连续点击3次后，状态正确（收起）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 快速连续点击3次后，状态不正确", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 恢复初始状态（展开面板）
    print("\n6. 恢复初始状态（展开面板）", flush=True)
    try:
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        fullscreen_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0018_restored.png")
        if is_panel_expanded(page):
            print("   ✅ 已恢复初始状态，面板展开", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 未恢复初始状态", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
