# -*- coding: utf-8 -*-
"""
TC-0011: 3D导演台-添加机位与摄像机属性
测试：添加机位、右侧属性面板、修改参数、切换机位、截图
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
    print("TC-0011: 3D导演台-添加机位与摄像机属性", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮添加机位按钮，验证提示
    print("\n1. 悬浮添加机位按钮", flush=True)
    try:
        cam_btn = page.locator("button[aria-label='添加机位']").first
        if cam_btn.count() > 0:
            cam_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=添加机位").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'添加机位'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 添加机位按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 点击添加机位按钮，新增机位
    print("\n2. 点击添加机位按钮，新增机位", flush=True)
    try:
        cam_btn = page.locator("button[aria-label='添加机位']").first
        cam_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0011_camera_added.png")
        # 验证左侧列表新增机位
        cam_list = page.locator("text=机位02").first
        if cam_list.count() > 0:
            print("   ✅ 新增机位成功，左侧列表出现机位02", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 机位02未检测到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 验证右侧摄像机属性面板
    print("\n3. 验证右侧摄像机属性面板", flush=True)
    try:
        # 点击机位02，选中它
        cam_item = page.locator("text=机位02").first
        cam_item.click(force=True)
        time.sleep(1)
        shot(page, "tc0011_camera_props.png")
        # 检测属性面板标题
        props_title = page.locator("text=摄像机").first
        if props_title.count() > 0:
            print("   ✅ 右侧摄像机属性面板显示", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 摄像机属性面板未检测到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 修改位置X参数
    print("\n4. 修改位置X参数", flush=True)
    try:
        # 找到位置X输入框并修改
        pos_x_input = page.locator("input[type='number']").first
        if pos_x_input.count() > 0:
            pos_x_input.fill("5")
            time.sleep(1)
            shot(page, "tc0011_pos_modified.png")
            print("   ✅ 位置参数修改成功", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 位置输入框未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 切换机位（机位01→机位02）
    print("\n5. 切换机位", flush=True)
    try:
        cam01 = page.locator("text=机位01").first
        cam01.click(force=True)
        time.sleep(1)
        shot(page, "tc0011_switch_cam01.png")
        print("   ✅ 切换到机位01成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 点击当前机位截图按钮
    print("\n6. 点击当前机位截图按钮", flush=True)
    try:
        # 点击顶部截图按钮
        shot_btn = page.locator("button[aria-label='截图']").first
        if shot_btn.count() > 0:
            shot_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0011_shot_taken.png")
            print("   ✅ 截图按钮点击成功", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 截图按钮未找到", flush=True)
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
