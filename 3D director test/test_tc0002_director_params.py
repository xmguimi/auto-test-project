# -*- coding: utf-8 -*-
"""
TC-0002: 3D导演台-键盘输入修改角色参数
默认3D导演台节点已存在，双击进入工作台后测试参数输入
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
    print("TC-0002: 3D导演台-键盘输入修改角色参数", flush=True)
    print("=" * 60, flush=True)

    # 1. 双击3D导演台节点，进入工作台
    print("\n1. 双击3D导演台节点，进入工作台", flush=True)
    try:
        node = page.locator(".react-flow__node").first
        if node.count() > 0:
            node.dblclick(force=True)
            time.sleep(2)
            shot(page, "tc0002_workbench_open.png")
            print("   ✅ 已进入3D工作台", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到3D导演台节点", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 双击失败: {e}", flush=True)
        results.append(False)

    # 2. 点击角色01
    print("\n2. 点击角色01", flush=True)
    try:
        role_btn = page.locator("text=角色01").first
        if role_btn.count() > 0:
            role_btn.click(force=True)
            time.sleep(1)
            print("   ✅ 已选中角色01", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到角色01", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 3. 输入位置参数
    print("\n3. 输入位置参数 X=5, Y=-5", flush=True)
    try:
        inputs = page.locator("input[type='number']").all()
        if len(inputs) >= 6:
            inputs[0].fill("5")  # X
            inputs[1].fill("-5")  # Y
            time.sleep(0.5)
            print("   ✅ 位置参数输入成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 输入框不足", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 4. 输入旋转参数
    print("\n4. 输入旋转参数 X=0.5, Y=1.5, Z=-0.5", flush=True)
    try:
        inputs = page.locator("input[type='number']").all()
        if len(inputs) >= 9:
            inputs[3].fill("0.5")  # X
            inputs[4].fill("1.5")  # Y
            inputs[5].fill("-0.5")  # Z
            time.sleep(0.5)
            print("   ✅ 旋转参数输入成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 输入框不足", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 5. 输入缩放参数
    print("\n5. 输入缩放参数 X=0.8, Y=0.9, Z=1.1", flush=True)
    try:
        inputs = page.locator("input[type='number']").all()
        if len(inputs) >= 9:
            inputs[6].fill("0.8")  # X
            inputs[7].fill("0.9")  # Y
            inputs[8].fill("1.1")  # Z
            time.sleep(0.5)
            shot(page, "tc0002_params_entered.png")
            print("   ✅ 缩放参数输入成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 输入框不足", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 输入失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
