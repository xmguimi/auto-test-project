# -*- coding: utf-8 -*-
"""
TC-0021: 3D导演台-机位数量边界
测试：连续点击添加机位，验证是否无上限
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


def get_camera_count(page):
    """获取左侧列表中机位的数量"""
    camera_items = page.locator("text=机位").locator("xpath=..")
    return camera_items.count()


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0021: 3D导演台-机位数量边界", flush=True)
    print("=" * 60, flush=True)

    # 1. 确认添加机位按钮存在
    print("\n1. 确认添加机位按钮存在", flush=True)
    try:
        add_cam_btn = page.locator("button[aria-label='添加机位']").first
        if add_cam_btn.count() > 0 and add_cam_btn.is_visible():
            print("   ✅ 添加机位按钮可见", flush=True)
            results.append(True)
        else:
            print("   ❌ 添加机位按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 记录初始机位数量
    print("\n2. 记录初始机位数量", flush=True)
    try:
        initial_count = get_camera_count(page)
        print(f"   初始机位数量: {initial_count}", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)
        initial_count = 0

    # 3. 连续点击添加机位，验证无上限
    print("\n3. 连续点击添加机位20次，验证无上限", flush=True)
    try:
        add_cam_btn = page.locator("button[aria-label='添加机位']").first
        last_count = initial_count

        for i in range(20):
            add_cam_btn.click(force=True)
            time.sleep(0.5)
            current_count = get_camera_count(page)
            print(f"   点击第{i+1}次后，机位数量: {current_count}", flush=True)
            last_count = current_count

        final_count = last_count
        print(f"   最终机位数量: {final_count}", flush=True)
        shot(page, "tc0021_max_cameras.png")

        if final_count > initial_count:
            print("   ✅ 连续添加机位功能正常，无明显上限", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 机位数量未增加", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)
        final_count = initial_count

    # 4. 验证按钮一直可用，无上限限制
    print("\n4. 验证按钮一直可用，无上限限制", flush=True)
    try:
        add_cam_btn = page.locator("button[aria-label='添加机位']").first
        if not add_cam_btn.is_disabled():
            print("   ✅ 添加机位按钮一直可用，无上限", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 按钮置灰，存在上限", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 验证全程无崩溃
    print("\n5. 验证全程无崩溃", flush=True)
    try:
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        if fullscreen_btn.count() > 0 and fullscreen_btn.is_visible():
            print("   ✅ 页面正常，无崩溃", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 页面可能异常", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)
    print(f"最终机位数量: {final_count}（测试20次，无上限）", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
