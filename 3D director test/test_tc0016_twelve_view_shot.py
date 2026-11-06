# -*- coding: utf-8 -*-
"""
TC-0016: 3D导演台-十二方位截图
测试：悬浮提示、点击十二方位截图、验证生成12张截图
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
    print("TC-0016: 3D导演台-十二方位截图", flush=True)
    print("=" * 60, flush=True)

    # 0. 先选中机位01，确保右侧显示摄像机面板
    print("\n0. 选中机位01，切换到摄像机面板", flush=True)
    try:
        cam01 = page.locator("div:has-text('机位01')").first
        cam01.click(force=True)
        time.sleep(2)
        print("   ✅ 已选中机位01", flush=True)
    except Exception as e:
        print(f"   ⚠️ 选中机位失败: {e}", flush=True)

    # 1. 悬浮十二方位截图按钮，验证提示
    print("\n1. 悬浮十二方位截图按钮", flush=True)
    try:
        twelve_btn = page.locator("button[aria-label='十二方位截图']").first
        if twelve_btn.count() > 0:
            twelve_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=十二方位截图").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'十二方位截图'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 十二方位截图按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 先清空截图，确保干净状态
    print("\n2. 清空截图，确保干净状态", flush=True)
    try:
        cam_shot_tab = page.locator("text=摄像机截图").first
        cam_shot_tab.click(force=True)
        time.sleep(1)
        clear_btn = page.locator("text=清空全部").first
        if clear_btn.count() > 0:
            clear_btn.click(force=True)
            time.sleep(1)
            print("   ✅ 已清空截图", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 点击十二方位截图按钮
    print("\n3. 点击十二方位截图按钮", flush=True)
    try:
        props_tab = page.locator("text=属性").first
        props_tab.click(force=True)
        time.sleep(1)
        twelve_btn = page.locator("button[aria-label='十二方位截图']").first
        twelve_btn.click(force=True)
        time.sleep(5)  # 等待12张截图生成
        shot(page, "tc0016_twelve_shot.png")
        print("   ✅ 十二方位截图按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 切到摄像机截图tab，验证生成12张截图
    print("\n4. 验证生成12张截图", flush=True)
    try:
        cam_shot_tab = page.locator("text=摄像机截图").first
        cam_shot_tab.click(force=True)
        time.sleep(1)
        shot(page, "tc0016_final_list.png")
        # 数一下截图数量
        cam01_shots = page.locator("text=机位01-截图").count()
        if cam01_shots >= 12:
            print(f"   ✅ 十二方位截图生成成功，共{cam01_shots}张截图", flush=True)
            results.append(True)
        else:
            print(f"   ⚠️ 截图数量不足，只有{cam01_shots}张", flush=True)
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
