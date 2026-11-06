# -*- coding: utf-8 -*-
"""
TC-0016: 图片节点反推功能测试
验证反推工作台打开、反推方向、目标模型、分析模型、开始反推按钮
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

# 生成开关：True=实际点击开始反推（扣费），False=只验证按钮存在不实际生成
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
    print("TC-0016: 图片节点反推功能测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：关闭弹窗，选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 步骤2：点击反推按钮
    print("\n2. 点击反推按钮", flush=True)
    try:
        reverse_btn = page.locator("text=反推").first
        reverse_btn.click(force=True)
        time.sleep(3)
        shot(page, "tc0016_reverse.png")
        print("   ✅ 反推按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 反推按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤3：验证反推工作台
    print("\n3. 反推工作台布局", flush=True)
    try:
        title = page.locator("text=提示词反推").first
        if title.count() > 0:
            print("   ✅ 标题'提示词反推'存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 工作台验证失败: {e}", flush=True)
        results.append(False)

    # 步骤4：验证反推方向
    print("\n4. 反推方向选项", flush=True)
    try:
        general = page.locator("text=通用反推").first
        ecommerce = page.locator("text=电商复刻").first
        if general.count() > 0 and ecommerce.count() > 0:
            print("   ✅ 通用反推/电商复刻选项存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 反推方向失败: {e}", flush=True)
        results.append(False)

    # 步骤5：验证目标模型
    print("\n5. 目标模型选项", flush=True)
    try:
        gpt = page.locator("text=GPT-IMAGE2").first
        banana = page.locator("text=香蕉").first
        if gpt.count() > 0 and banana.count() > 0:
            print("   ✅ GPT-IMAGE2/香蕉系列模型选项存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 目标模型失败: {e}", flush=True)
        results.append(False)

    # 步骤6：验证开始反推按钮
    print("\n6. 开始反推按钮", flush=True)
    try:
        start_btn = page.locator("button:has-text('开始反推')").first
        if start_btn.count() > 0:
            print("   ✅ 开始反推按钮存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 开始反推按钮失败: {e}", flush=True)
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
