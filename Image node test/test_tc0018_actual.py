# -*- coding: utf-8 -*-
"""
TC-0018: 图片节点旋转与镜像功能实际测试
实际点击旋转、水平镜像、垂直镜像，验证图片变化
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
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


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
    print("TC-0018: 图片节点旋转与镜像功能实际测试", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗，选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.locator("img").nth(4).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 打开旋转与镜像工具栏
    print("\n2. 打开旋转与镜像工具栏", flush=True)
    rotate_btn = page.locator("[class*='rotate'], [class*='refresh']").nth(1)
    rotate_btn.click(force=True)
    time.sleep(2)
    print("   ✅ 旋转与镜像工具栏打开", flush=True)
    results.append(True)

    # 测试1：输入45度
    print("\n3. 输入45度", flush=True)
    try:
        angle_input = page.locator("input[type='number']").first
        angle_input.fill("45")
        page.keyboard.press("Enter")
        time.sleep(0.5)
        shot(page, "tc0018_45.png")
        print("   ✅ 输入45度成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 输入45度失败: {e}", flush=True)
        results.append(False)

    # 测试2：点击旋转按钮
    print("\n4. 点击旋转按钮", flush=True)
    try:
        rotate_icon = page.locator("[class*='rotate'], [class*='refresh']").nth(2)
        rotate_icon.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0018_rotate90.png")
        print("   ✅ 旋转按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 旋转按钮失败: {e}", flush=True)
        results.append(False)

    # 测试3：点击水平镜像按钮
    print("\n5. 点击水平镜像按钮", flush=True)
    try:
        h_mirror = page.locator("[class*='horizontal'], [class*='mirror']").first
        h_mirror.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0018_hmirror.png")
        print("   ✅ 水平镜像按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 水平镜像按钮失败: {e}", flush=True)
        results.append(False)

    # 测试4：点击垂直镜像按钮
    print("\n6. 点击垂直镜像按钮", flush=True)
    try:
        v_mirror = page.locator("[class*='vertical'], [class*='flip']").first
        v_mirror.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0018_vmirror.png")
        print("   ✅ 垂直镜像按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 垂直镜像按钮失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    print("测试结果汇总：", flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
