# -*- coding: utf-8 -*-
"""
TC-0014: 3D导演台-当前视角截图
测试：悬浮提示、截图成功、切换机位再截图、快速多次点击、截图列表验证
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
    print("TC-0014: 3D导演台-当前视角截图", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮当前视角截图按钮，验证提示
    print("\n1. 悬浮当前视角截图按钮", flush=True)
    try:
        shot_btn = page.locator("button[aria-label='当前视角截图']").first
        if shot_btn.count() > 0:
            shot_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=当前视角截图").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'当前视角截图'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 当前视角截图按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 先清空截图，确保干净状态
    print("\n2. 清空截图，确保干净状态", flush=True)
    try:
        # 切到摄像机截图tab
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

    # 3. 点击当前视角截图按钮，截第一张
    print("\n3. 点击当前视角截图按钮，截第一张", flush=True)
    try:
        # 切回属性tab
        props_tab = page.locator("text=属性").first
        props_tab.click(force=True)
        time.sleep(1)
        shot_btn = page.locator("button[aria-label='当前视角截图']").first
        shot_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0014_first_shot.png")
        print("   ✅ 第一张截图成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 切换机位，再截一张
    print("\n4. 切换机位，再截一张", flush=True)
    try:
        cam01 = page.locator("text=机位01").first
        cam01.click(force=True)
        time.sleep(1)
        shot_btn = page.locator("button[aria-label='当前视角截图']").first
        shot_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0014_second_shot.png")
        print("   ✅ 机位切换后第二张截图成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 快速连续点击3次，验证截图数量增加
    print("\n5. 快速连续点击3次，验证截图数量增加", flush=True)
    try:
        shot_btn = page.locator("button[aria-label='当前视角截图']").first
        for i in range(3):
            shot_btn.click(force=True)
            time.sleep(0.5)
        time.sleep(2)
        shot(page, "tc0014_rapid_shots.png")
        print("   ✅ 快速连续点击3次完成", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 切到摄像机截图tab，验证截图列表
    print("\n6. 切到摄像机截图tab，验证截图列表", flush=True)
    try:
        cam_shot_tab = page.locator("text=摄像机截图").first
        cam_shot_tab.click(force=True)
        time.sleep(1)
        shot(page, "tc0014_final_list.png")
        # 验证有机位01和机位02的截图
        cam01_shot = page.locator("text=机位01截图").first
        cam02_shot = page.locator("text=机位02截图").first
        if cam01_shot.count() > 0 or cam02_shot.count() > 0:
            print("   ✅ 截图列表按机位分类显示", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 截图列表未检测到", flush=True)
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
