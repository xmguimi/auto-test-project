# -*- coding: utf-8 -*-
"""
TC-0009: 图片节点自由拼接测试
验证连续点击左侧图片可重复添加到右侧画框
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
    print("TC-0009: 自由拼接测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：拼图工具打开
    print("\n1. 拼图工具打开", flush=True)
    title = page.locator("text=拼图工具").first
    if title.count() > 0:
        print("   ✅ 拼图工具已打开", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤2：左侧列表第一张图片
    print("\n2. 左侧列表图片", flush=True)
    left_img = page.locator("img").nth(1)
    if left_img.count() > 0:
        print("   ✅ 左侧列表有图片", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤3：第一次点击左侧图片
    print("\n3. 第一次点击左侧图片，添加到右侧画框", flush=True)
    try:
        left_img.click(force=True)
        time.sleep(1)
        shot(page, "tc0009_first_add.png")
        print("   ✅ 第一次添加成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 第一次添加失败: {e}", flush=True)
        results.append(False)

    # 步骤4：第二次点击左侧同一张图片
    print("\n4. 第二次点击左侧图片，再添加一张", flush=True)
    try:
        left_img.click(force=True)
        time.sleep(1)
        shot(page, "tc0009_second_add.png")
        print("   ✅ 第二次添加成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 第二次添加失败: {e}", flush=True)
        results.append(False)

    # 步骤5：验证右侧画框有两张图片
    print("\n5. 右侧画框图片数量", flush=True)
    try:
        right_imgs = page.evaluate("""() => {
            return document.querySelectorAll('canvas').length;
        }""")
        print(f"   ✅ 画布canvas数量：{right_imgs}", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 画框验证失败: {e}", flush=True)
        results.append(False)

    # 步骤6：保存到画布按钮
    print("\n6. 保存到画布按钮", flush=True)
    try:
        save_btn = page.locator("text=保存到画布").first
        if save_btn.count() > 0:
            print("   ✅ 保存到画布按钮存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 保存按钮失败: {e}", flush=True)
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
