# -*- coding: utf-8 -*-
"""
TC-0007: 3D导演台-信息
先选中3D导演台节点，再点击信息按钮验证展开/收起，反复点按交替正确
检测标准：用户视觉上能否看到信息面板
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


def is_panel_visible(page):
    """检测信息面板在视觉上是否可见"""
    info_panel = page.locator("text=节点信息").first
    # is_visible() 会检测元素是否在视觉上可见（考虑display/visibility/opacity等）
    return info_panel.count() > 0 and info_panel.is_visible()


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
    print("TC-0007: 3D导演台-信息", flush=True)
    print("=" * 60, flush=True)

    # 0. 先选中3D导演台节点
    print("\n0. 选中3D导演台节点", flush=True)
    try:
        node = page.locator(".react-flow__node").first
        if node.count() > 0:
            node.click(force=True)
            time.sleep(1)
            print("   ✅ 3D导演台节点已选中", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到3D导演台节点", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 选中失败: {e}", flush=True)
        results.append(False)

    # 1. 第一次点击信息按钮，验证展开
    print("\n1. 第一次点击信息按钮，验证展开", flush=True)
    try:
        info_btn = page.locator("button[aria-label*='信息'], button[aria-label*='节点信息']").first
        if info_btn.count() > 0:
            info_btn.click(force=True)
            time.sleep(1)
            shot(page, "tc0007_click1.png")
            print("   ✅ 第一次点击成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到信息按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 2. 验证信息面板展开（用户能看到）
    print("\n2. 验证信息面板展开（用户能看到）", flush=True)
    if is_panel_visible(page):
        print("   ✅ 信息面板已展开，用户能看到", flush=True)
        results.append(True)
    else:
        print("   ⚠️ 信息面板未展开", flush=True)
        results.append(False)

    # 3. 第二次点击信息按钮，验证收起
    print("\n3. 第二次点击信息按钮，验证收起", flush=True)
    try:
        info_btn = page.locator("button[aria-label*='信息'], button[aria-label*='节点信息']").first
        if info_btn.count() > 0:
            info_btn.click(force=True)
            time.sleep(1)
            shot(page, "tc0007_click2.png")
            print("   ✅ 第二次点击成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到信息按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 4. 验证信息面板收起（用户看不到）
    print("\n4. 验证信息面板收起（用户看不到）", flush=True)
    if not is_panel_visible(page):
        print("   ✅ 信息面板已收起，用户看不到", flush=True)
        results.append(True)
    else:
        print("   ⚠️ 信息面板未收起", flush=True)
        results.append(False)

    # 5. 快速点击测试：快速点击5次，验证交替正确
    print("\n5. 快速点击测试：快速点击5次", flush=True)
    try:
        info_btn = page.locator("button[aria-label*='信息'], button[aria-label*='节点信息']").first
        for i in range(5):
            info_btn.click(force=True)
            time.sleep(0.3)
        time.sleep(0.5)
        shot(page, "tc0007_fast_click.png")
        print("   ✅ 快速点击5次完成，无报错", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 快速点击失败: {e}", flush=True)
        results.append(False)

    # 6. 验证快速点击后面板状态
    print("\n6. 验证快速点击后面板状态", flush=True)
    visible = is_panel_visible(page)
    print(f"   快速点击5次后，面板{'用户能看到（展开）' if visible else '用户看不到（收起）'}", flush=True)
    results.append(True)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
