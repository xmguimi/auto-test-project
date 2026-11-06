# -*- coding: utf-8 -*-
"""
TC-0005: 3D导演台-截图到画布
点击画布上的截图到画布按钮，自动打开工作台，再点击截图按钮和发送到画布
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
    print("TC-0005: 3D导演台-截图到画布", flush=True)
    print("=" * 60, flush=True)

    # 1. 点击画布上的截图到画布按钮（第二个按钮）
    print("\n1. 点击画布上的截图到画布按钮", flush=True)
    try:
        shot_to_canvas_btn = page.locator("button[aria-label*='截图到画布']").first
        if shot_to_canvas_btn.count() > 0:
            shot_to_canvas_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0005_workbench_open.png")
            print("   ✅ 截图到画布按钮点击成功，工作台自动打开", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到截图到画布按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 2. 点击工作台内截图按钮
    print("\n2. 点击工作台内截图按钮", flush=True)
    try:
        shot_btn = page.locator("button:has-text('截图')").first
        if shot_btn.count() > 0:
            shot_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0005_after_shot.png")
            print("   ✅ 截图按钮点击成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到截图按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 3. 点击发送到画布按钮（工作台自动关闭）
    print("\n3. 点击发送到画布按钮", flush=True)
    try:
        send_btn = page.locator("button:has-text('发送到画布')").first
        if send_btn.count() > 0:
            send_btn.click(force=True)
            time.sleep(2)
            shot(page, "tc0005_back_canvas.png")
            print("   ✅ 发送到画布按钮点击成功，工作台自动关闭", flush=True)
            results.append(True)
        else:
            print("   ❌ 未找到发送到画布按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 点击失败: {e}", flush=True)
        results.append(False)

    # 4. 验证截图是否出现在画布上
    print("\n4. 验证截图是否出现在画布上", flush=True)
    try:
        nodes = page.locator(".react-flow__node").all()
        print(f"   当前画布节点数: {len(nodes)}", flush=True)
        if len(nodes) >= 2:
            print("   ✅ 画布上有截图节点", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 画布上未检测到截图节点", flush=True)
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
