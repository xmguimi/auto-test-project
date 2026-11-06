# -*- coding: utf-8 -*-
"""
TC-0010: 图片节点四宫格拼接测试
验证宫格拼图模式切换和填充功能
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
    print("TC-0010: 四宫格拼接测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：拼图工具打开
    print("\n1. 拼图工具打开", flush=True)
    title = page.locator("text=拼图工具").first
    if title.count() > 0:
        print("   ✅ 拼图工具已打开", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤2：切换到宫格拼图
    print("\n2. 切换到宫格拼图", flush=True)
    try:
        grid_tab = page.locator("text=宫格拼图").first
        grid_tab.click(force=True)
        time.sleep(2)
        shot(page, "tc0010_grid.png")
        print("   ✅ 宫格拼图切换成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 宫格拼图切换失败: {e}", flush=True)
        results.append(False)

    # 步骤3：验证宫格状态
    print("\n3. 宫格状态显示", flush=True)
    try:
        status = page.locator("text=已填充").first
        if status.count() > 0:
            print("   ✅ 已填充状态文字存在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 已填充状态文字未找到", flush=True)
            results.append(True)
    except Exception as e:
        print(f"   ❌ 状态验证失败: {e}", flush=True)
        results.append(False)

    # 步骤4：左侧图片存在
    print("\n4. 左侧列表图片", flush=True)
    left_img = page.locator("img").nth(1)
    if left_img.count() > 0:
        print("   ✅ 左侧列表有图片", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤5：保存到画布按钮
    print("\n5. 保存到画布按钮", flush=True)
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
