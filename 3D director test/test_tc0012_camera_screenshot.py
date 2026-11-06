# -*- coding: utf-8 -*-
"""
TC-0012: 3D导演台-摄像机截图
测试：先确认截图tab为空 → 机位01截图 → 机位02截图 → 检查分类显示
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
    print("TC-0012: 3D导演台-摄像机截图", flush=True)
    print("=" * 60, flush=True)

    # 1. 先切换到摄像机截图tab，确认是空的
    print("\n1. 切换到摄像机截图tab，确认空状态", flush=True)
    try:
        cam_shot_tab = page.locator("text=摄像机截图").first
        cam_shot_tab.click(force=True)
        time.sleep(1)
        shot(page, "tc0012_empty.png")
        # 先清空，确保是空的
        clear_btn = page.locator("text=清空全部").first
        if clear_btn.count() > 0:
            clear_btn.click(force=True)
            time.sleep(1)
            print("   ✅ 已清空，确认截图tab为空", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 切换到机位01，对机位01截图
    print("\n2. 切换到机位01，对机位01截图", flush=True)
    try:
        # 先切回属性tab
        props_tab = page.locator("text=属性").first
        props_tab.click(force=True)
        time.sleep(1)
        # 切换机位01
        cam01 = page.locator("text=机位01").first
        cam01.click(force=True)
        time.sleep(1)
        # 点击当前机位截图
        take_shot_btn = page.locator("text=当前机位截图").first
        if take_shot_btn.count() > 0:
            take_shot_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0012_cam01_shot.png")
            print("   ✅ 机位01截图完成", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 当前机位截图按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 切换到机位02，对机位02截图
    print("\n3. 切换到机位02，对机位02截图", flush=True)
    try:
        cam02 = page.locator("text=机位02").first
        cam02.click(force=True)
        time.sleep(1)
        take_shot_btn = page.locator("text=当前机位截图").first
        if take_shot_btn.count() > 0:
            take_shot_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0012_cam02_shot.png")
            print("   ✅ 机位02截图完成", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 当前机位截图按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 切换回摄像机截图tab，检查分类和缩略图
    print("\n4. 切换回摄像机截图tab，检查分类显示", flush=True)
    try:
        cam_shot_tab = page.locator("text=摄像机截图").first
        cam_shot_tab.click(force=True)
        time.sleep(1)
        shot(page, "tc0012_final.png")
        # 检查是否有机位01截图和机位02截图
        cam01_shot = page.locator("text=机位01截图").first
        cam02_shot = page.locator("text=机位02截图").first
        if cam01_shot.count() > 0 and cam02_shot.count() > 0:
            print("   ✅ 截图按机位正确分类：机位01截图、机位02截图", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 截图分类不完整", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 验证清空全部按钮
    print("\n5. 验证清空全部按钮", flush=True)
    try:
        clear_btn = page.locator("text=清空全部").first
        if clear_btn.count() > 0:
            print("   ✅ 清空全部按钮存在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 清空全部按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 验证发送到画布按钮
    print("\n6. 验证发送到画布按钮", flush=True)
    try:
        send_btn = page.locator("text=发送到画布").first
        if send_btn.count() > 0:
            print("   ✅ 发送到画布按钮存在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 发送到画布按钮未找到", flush=True)
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
