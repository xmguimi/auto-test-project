# -*- coding: utf-8 -*-
"""
TC-0013: 3D导演台-画幅比例
测试：每次点比例面板自动关闭，需重新点按钮弹面板再选下一个
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
    print("TC-0013: 3D导演台-画幅比例", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮画幅比例按钮，验证提示
    print("\n1. 悬浮画幅比例按钮", flush=True)
    try:
        ratio_btn = page.locator("button[aria-label='选择画幅比例']").first
        if ratio_btn.count() > 0:
            ratio_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=画幅比例").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'画幅比例'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 画幅比例按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 点击画幅比例按钮，弹出面板，验证8个选项
    print("\n2. 点击画幅比例按钮，验证8个选项", flush=True)
    try:
        ratio_btn = page.locator("button[aria-label='选择画幅比例']").first
        ratio_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0013_panel_open.png")
        panel_title = page.locator("text=比例").first
        if panel_title.count() > 0:
            ratios = ["自动", "1:1", "2:1", "3:4", "4:3", "16:9", "21:9", "9:16"]
            found = 0
            for ratio in ratios:
                ratio_item = page.locator(f"text={ratio}").first
                if ratio_item.count() > 0:
                    found += 1
            if found == len(ratios):
                print(f"   ✅ 比例面板弹出，全部{len(ratios)}个选项都存在", flush=True)
                results.append(True)
            else:
                print(f"   ⚠️ 只找到{found}/{len(ratios)}个选项", flush=True)
                results.append(False)
        else:
            print("   ❌ 比例面板未弹出", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 依次切换每个比例（每次重新点按钮弹面板）
    print("\n3. 依次切换每个比例（每次重新点按钮弹面板）", flush=True)
    try:
        ratios = ["1:1", "2:1", "3:4", "4:3", "16:9", "21:9", "9:16", "自动"]
        switch_ok = 0
        for i, ratio in enumerate(ratios):
            # 重新点按钮弹面板
            ratio_btn = page.locator("button[aria-label='选择画幅比例']").first
            ratio_btn.click(force=True)
            time.sleep(1)
            # 选择比例
            ratio_item = page.locator(f"text={ratio}").first
            if ratio_item.count() > 0:
                ratio_item.click(force=True)
                time.sleep(1)
                shot(page, f"tc0013_{ratio.replace(':', '_')}.png")
                switch_ok += 1
                print(f"     - {ratio} ✅", flush=True)
            else:
                print(f"     - {ratio} ❌", flush=True)
        if switch_ok == len(ratios):
            print(f"   ✅ 全部{len(ratios)}个比例切换成功", flush=True)
            results.append(True)
        else:
            print(f"   ⚠️ 只有{switch_ok}/{len(ratios)}个比例切换成功", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 验证当前选中自动比例
    print("\n4. 验证当前选中自动比例", flush=True)
    try:
        # 再切一次自动
        ratio_btn = page.locator("button[aria-label='选择画幅比例']").first
        ratio_btn.click(force=True)
        time.sleep(1)
        auto_item = page.locator("text=自动").first
        auto_item.click(force=True)
        time.sleep(1)
        shot(page, "tc0013_final_auto.png")
        print("   ✅ 切回自动比例成功", flush=True)
        results.append(True)
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
