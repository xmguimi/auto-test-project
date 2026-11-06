# -*- coding: utf-8 -*-
"""
TC-0004: 3D场景-添加全景图与参数设置
默认3D工作台已打开，测试场景参数设置
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
    print("TC-0004: 3D场景-添加全景图与参数设置", flush=True)
    print("=" * 60, flush=True)

    # 1. 验证工作台已打开
    print("\n1. 验证工作台已打开", flush=True)
    try:
        workbench = page.locator("text=3D").first
        if workbench.count() > 0:
            print("   ✅ 3D工作台已打开", flush=True)
            results.append(True)
        else:
            print("   ❌ 工作台未打开", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 2. 设置场景位置参数
    print("\n2. 设置场景位置参数 X=5, Y=-5, Z=5", flush=True)
    try:
        inputs = page.locator("input[type='number']").all()
        if len(inputs) >= 3:
            inputs[0].fill("5")  # X
            inputs[1].fill("-5")  # Y
            inputs[2].fill("5")  # Z
            time.sleep(0.5)
            print("   ✅ 场景位置参数输入成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 输入框不足", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 3. 设置场景旋转参数
    print("\n3. 设置场景旋转参数 X=1, Y=-1, Z=3", flush=True)
    try:
        inputs = page.locator("input[type='number']").all()
        if len(inputs) >= 6:
            inputs[3].fill("1")  # X
            inputs[4].fill("-1")  # Y
            inputs[5].fill("3")  # Z
            time.sleep(0.5)
            print("   ✅ 场景旋转参数输入成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 输入框不足", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 4. 打开网格吸附开关
    print("\n4. 打开网格吸附开关", flush=True)
    try:
        grid_switch = page.locator("text=网格吸附").first
        if grid_switch.count() > 0:
            grid_switch.click(force=True)
            time.sleep(0.5)
            shot(page, "tc0004_params_set.png")
            print("   ✅ 网格吸附开关已打开", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到网格吸附开关", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 操作失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
