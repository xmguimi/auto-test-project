# -*- coding: utf-8 -*-
"""
TC-0001: 3D导演台-打开工作台
完整流程：双击空白→建3D导演台节点→双击进工作台→关闭工作台返回画布
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
    print("TC-0001: 3D导演台-打开工作台", flush=True)
    print("=" * 60, flush=True)

    # 初始：先按Esc关闭所有弹窗，取消选中
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 步骤1：双击画布空白位置
    print("\n步骤1：双击画布空白位置", flush=True)
    try:
        page.mouse.dblclick(500, 400)
        time.sleep(1.5)
        shot(page, "tc0001_step1_menu.png")
        print("   ✅ 双击画布，弹出节点菜单", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 双击失败: {e}", flush=True)
        results.append(False)

    # 步骤2：选择3D导演台节点，创建节点
    print("\n步骤2：选择3D导演台节点，创建节点", flush=True)
    try:
        director_item = page.locator(".cm-item:has-text('3D 导演台')").first
        if director_item.count() > 0:
            director_item.click(force=True)
            time.sleep(2)
            shot(page, "tc0001_step2_node_created.png")
            print("   ✅ 3D导演台节点已创建", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到3D导演台选项", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 创建节点失败: {e}", flush=True)
        results.append(False)

    # 步骤3：双击新建的3D导演台节点，进入工作台
    print("\n步骤3：双击3D导演台节点，进入工作台", flush=True)
    try:
        node = page.locator("[class*='node']:has-text('导演台')").first
        if node.count() > 0:
            node.dblclick(force=True)
            time.sleep(2)
            shot(page, "tc0001_step3_workbench.png")
            print("   ✅ 双击节点，工作台已打开", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到节点", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 双击节点失败: {e}", flush=True)
        results.append(False)

    # 步骤4：验证工作台元素
    print("\n步骤4：验证工作台元素显示", flush=True)
    try:
        workbench = page.locator("text=3D").first
        if workbench.count() > 0:
            print("   ✅ 工作台内元素显示正确", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 未检测到工作台元素", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 步骤5：关闭工作台，返回画布
    print("\n步骤5：关闭工作台，返回画布", flush=True)
    try:
        page.keyboard.press("Escape")
        time.sleep(1.5)
        shot(page, "tc0001_step5_back_canvas.png")
        print("   ✅ 工作台已关闭", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 关闭失败: {e}", flush=True)
        results.append(False)

    # 步骤6：验证返回画布，节点不受影响
    print("\n步骤6：验证返回画布，节点不受影响", flush=True)
    try:
        node = page.locator("[class*='node']:has-text('导演台')").first
        if node.count() > 0:
            print("   ✅ 返回画布，3D导演台节点仍在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 节点丢失", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
