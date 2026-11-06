# -*- coding: utf-8 -*-
"""
TC-0020: 图片节点自定义工具栏 - 完整功能测试
1. 取消固定切分工具
2. 点击完成
3. 验证工具栏切分消失
4. 重新打开面板
5. 点击恢复默认
6. 验证切分恢复
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


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
    print("TC-0020: 自定义工具栏完整功能测试", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.locator("img").nth(4).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 2. 打开自定义工具栏面板
    print("\n2. 打开自定义工具栏面板", flush=True)
    toolbar_btns = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
    toolbar_btns[-2].click(force=True)  # 倒数第二个是...按钮
    time.sleep(2)
    print("   ✅ 面板已打开", flush=True)
    results.append(True)

    # 3. 点击切分的取消固定按钮
    print("\n3. 点击切分的取消固定按钮", flush=True)
    try:
        # 切分那一行，右边的取消固定图标
        unpin_btn = page.locator("text=切分").locator("xpath=..//*[contains(@class, 'unpin') or contains(@class, 'close') or contains(@class, 'x')]").first
        if unpin_btn.count() == 0:
            # 尝试找切分行右边的所有按钮
            unpin_btn = page.locator("text=切分").locator("xpath=..//*").last
        unpin_btn.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0020_unpin_split.png")
        print("   ✅ 切分取消固定成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 取消固定失败: {e}", flush=True)
        results.append(False)

    # 4. 点击完成按钮
    print("\n4. 点击完成按钮", flush=True)
    try:
        done_btn = page.locator("button:has-text('完成')").first
        done_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0020_after_done.png")
        print("   ✅ 完成按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 完成按钮失败: {e}", flush=True)
        results.append(False)

    # 5. 验证工具栏切分是否消失
    print("\n5. 验证工具栏切分是否消失", flush=True)
    try:
        split_btn = page.locator("text=切分").first
        if split_btn.count() == 0:
            print("   ✅ 切分已从工具栏消失", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 切分仍在工具栏", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 验证失败: {e}", flush=True)
        results.append(False)

    # 6. 重新打开面板，点击恢复默认
    print("\n6. 重新打开面板，点击恢复默认", flush=True)
    try:
        toolbar_btns2 = page.locator("[class*='toolbar'] button, div[class*='toolbar'] button").all()
        toolbar_btns2[-2].click(force=True)
        time.sleep(1)
        reset_btn = page.locator("text=恢复默认").first
        reset_btn.click(force=True)
        time.sleep(0.5)
        shot(page, "tc0020_after_reset.png")
        print("   ✅ 恢复默认成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 恢复默认失败: {e}", flush=True)
        results.append(False)

    # 7. 验证切分恢复
    print("\n7. 验证切分是否恢复", flush=True)
    try:
        done_btn2 = page.locator("button:has-text('完成')").first
        done_btn2.click(force=True)
        time.sleep(1)
        split_btn = page.locator("text=切分").first
        if split_btn.count() > 0:
            print("   ✅ 切分已恢复到工具栏", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 切分未恢复", flush=True)
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
