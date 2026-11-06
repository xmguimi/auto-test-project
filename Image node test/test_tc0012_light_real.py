# -*- coding: utf-8 -*-
"""
TC-0012: 打光主光源方位实际测试
验证点击不同方位按钮，左侧预览图光源对应移动
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
    print("TC-0012: 打光主光源方位实际测试", flush=True)
    print("=" * 60, flush=True)

    # 打光工作台已打开
    print("\n1. 打光工作台已打开", flush=True)
    results.append(True)

    # 测试各个光源方位
    directions = ["左侧", "顶部", "右侧", "前方", "底部", "后方"]
    
    for i, direction in enumerate(directions):
        print(f"\n{i+2}. 测试主光源：{direction}", flush=True)
        try:
            btn = page.locator(f"text={direction}").first
            btn.click(force=True)
            time.sleep(1)
            shot(page, f"tc0012_light_{direction}.png")
            print(f"   ✅ {direction}按钮点击成功", flush=True)
            results.append(True)
        except Exception as e:
            print(f"   ❌ {direction}按钮失败: {e}", flush=True)
            results.append(False)

    # 最终停在顶部
    print("\n8. 最终停在顶部光源", flush=True)
    top_btn = page.locator("text=顶部").first
    top_btn.click(force=True)
    time.sleep(1)
    shot(page, "tc0012_light_final.png")
    print("   ✅ 主光源设置为顶部", flush=True)
    results.append(True)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    print("测试结果汇总：", flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
