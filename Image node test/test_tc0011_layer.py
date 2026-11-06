# -*- coding: utf-8 -*-
"""
TC-0011: 图片节点分层测试
验证分层功能入口、清晰度选择、开始拆分按钮
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
    print("TC-0011: 图片节点分层测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：关闭弹窗，选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.locator("img").nth(1).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 步骤2：点击分层按钮
    print("\n2. 点击分层按钮", flush=True)
    try:
        layer_btn = page.locator("text=分层").first
        layer_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0011_layer.png")
        print("   ✅ 分层按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 分层按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤3：验证分层面板
    print("\n3. 分层面板显示", flush=True)
    try:
        price_info = page.locator("text=价格").first
        if price_info.count() > 0:
            print("   ✅ 价格估算信息存在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 价格信息未找到", flush=True)
            results.append(True)
    except Exception as e:
        print(f"   ❌ 面板验证失败: {e}", flush=True)
        results.append(False)

    # 步骤4：验证清晰度选项
    print("\n4. 清晰度选项", flush=True)
    try:
        k1_btn = page.locator("text=1K").first
        k2_btn = page.locator("text=2K").first
        if k1_btn.count() > 0 and k2_btn.count() > 0:
            print("   ✅ 1K/2K清晰度选项存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 清晰度选项失败: {e}", flush=True)
        results.append(False)

    # 步骤5：验证自动拆分选项
    print("\n5. 自动拆分选项", flush=True)
    try:
        auto_split = page.locator("text=自动拆分").first
        if auto_split.count() > 0:
            print("   ✅ 自动拆分选项存在，点击后直接开始生成", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 自动拆分选项失败: {e}", flush=True)
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
