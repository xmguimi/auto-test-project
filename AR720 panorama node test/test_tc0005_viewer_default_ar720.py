# -*- coding: utf-8 -*-
"""
TC-0005: AR720全景节点-打开查看器-不选类型上传默认AR720
完整流程：选中节点→点打开查看器按钮→验证查看器打开→验证模式tab→关闭查看器。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0005: AR720全景节点-打开查看器 ===")

        # ---------- 步骤1: 找一个AR720节点并选中 ----------
        print("\n[步骤1] 选中AR720节点...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        target_node = None
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                text = node.text_content()
                if "AR720" in text:
                    target_node = node
                    print(f"找到AR720节点（第{i}个）")
                    break

        if not target_node:
            print("没找到AR720节点")
            check("找到AR720节点", False)
            browser.close()
            return

        target_node.click()
        page.wait_for_timeout(1000)

        # ---------- 步骤2: 点工具栏打开查看器按钮 ----------
        print("\n[步骤2] 点工具栏「打开查看器」按钮...")
        toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
        viewer_btn = toolbar.locator('button[aria-label*="打开查看器"]').first
        check("工具栏打开查看器按钮存在", viewer_btn.is_visible())

        viewer_btn.click()
        page.wait_for_timeout(2000)

        # ---------- 步骤3: 验证查看器打开了 ----------
        print("\n[步骤3] 验证查看器正常打开...")
        viewer_title = page.get_by_text("AR720 VIEWER")
        check("查看器打开，标题AR720 VIEWER显示", viewer_title.is_visible())

        # ---------- 步骤4: 验证模式tab ----------
        print("\n[步骤4] 验证查看器模式tab...")
        mode_360 = page.get_by_text("360° 全景").first
        mode_longstrip = page.get_by_text("长图").first
        check("360°全景tab存在", mode_360.is_visible())
        check("长图tab存在", mode_longstrip.is_visible())

        page.screenshot(path=str(SHOT_DIR / "tc0005_01_viewer_open.png"))

        # ---------- 步骤5: 关闭查看器 ----------
        print("\n[步骤5] 关闭查看器...")
        close_btn = page.locator('button[aria-label="关闭（Esc）"]').first
        close_btn.click()
        page.wait_for_timeout(1500)

        viewer_title_after = page.get_by_text("AR720 VIEWER")
        check("点关闭后查看器正常关闭", not viewer_title_after.is_visible())

        page.screenshot(path=str(SHOT_DIR / "tc0005_02_after_close.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
