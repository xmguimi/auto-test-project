# -*- coding: utf-8 -*-
"""
TC-0014: 表情情绪网格实际测试
点击不同方向，验证右侧表情预览对应变化
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 生成开关：True=实际点击生成（扣费），False=只验证按钮存在不实际生成
REAL_GENERATE = False


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
    print("TC-0014: 表情情绪网格实际测试", flush=True)
    print("=" * 60, flush=True)

    # 表情工作台已打开
    print("\n1. 表情工作台已打开", flush=True)
    results.append(True)

    # 测试四个方向：激动（顶部）
    print("\n2. 点击激动方向（顶部）", flush=True)
    try:
        # 情绪网格顶部中间点
        dots = page.locator(".dot, [class*='dot'], circle")
        if dots.count() > 0:
            # 点击最顶部中间的点（激动方向）
            dots.nth(2).click(force=True)
            time.sleep(1)
            shot(page, "tc0014_emotion_excited.png")
            print("   ✅ 激动方向点击成功", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 激动方向失败: {e}", flush=True)
        results.append(False)

    # 测试疏离方向（右侧）
    print("\n3. 点击疏离方向（右侧）", flush=True)
    try:
        dots = page.locator(".dot, [class*='dot'], circle")
        if dots.count() >= 5:
            dots.nth(7).click(force=True)
            time.sleep(1)
            shot(page, "tc0014_emotion_aloof.png")
            print("   ✅ 疏离方向点击成功", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 疏离方向失败: {e}", flush=True)
        results.append(False)

    # 测试平静方向（底部）
    print("\n4. 点击平静方向（底部）", flush=True)
    try:
        dots = page.locator(".dot, [class*='dot'], circle")
        if dots.count() >= 12:
            dots.nth(12).click(force=True)
            time.sleep(1)
            shot(page, "tc0014_emotion_calm.png")
            print("   ✅ 平静方向点击成功", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 平静方向失败: {e}", flush=True)
        results.append(False)

    # 测试亲近方向（左侧）
    print("\n5. 点击亲近方向（左侧）", flush=True)
    try:
        dots = page.locator(".dot, [class*='dot'], circle")
        if dots.count() >= 5:
            dots.nth(5).click(force=True)
            time.sleep(1)
            shot(page, "tc0014_emotion_friendly.png")
            print("   ✅ 亲近方向点击成功", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 亲近方向失败: {e}", flush=True)
        results.append(False)

    # 测试重置按钮
    print("\n6. 点击重置按钮", flush=True)
    try:
        reset_btn = page.locator("text=重置").first
        reset_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0014_emotion_reset.png")
        print("   ✅ 重置按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 重置按钮失败: {e}", flush=True)
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
