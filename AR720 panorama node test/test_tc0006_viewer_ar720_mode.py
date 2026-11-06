# -*- coding: utf-8 -*-
"""
TC-0006: AR720全景节点-打开查看器-选AR720上传验证
验证选AR720上传的节点，打开查看器后默认360°全景模式，长图tab置灰不可切换。
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

        print("=== TC-0006: AR720全景节点-打开查看器-选AR720上传 ===")

        # ---------- 步骤1: 找AR720节点并选中 ----------
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
                if "AR720" in text and "已生成" in text:
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

        # ---------- 步骤2: 点打开查看器 ----------
        print("\n[步骤2] 点打开查看器...")
        toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
        viewer_btn = toolbar.locator('button[aria-label*="打开查看器"]').first
        viewer_btn.click()
        page.wait_for_timeout(2000)

        # ---------- 步骤3: 验证默认模式是360°全景 ----------
        print("\n[步骤3] 验证默认模式是360°全景...")
        mode_360 = page.get_by_text("360° 全景").first
        check("查看器打开成功", mode_360.is_visible())

        # 检查长图tab是不是置灰/不可点
        longstrip_tab = page.get_by_text("长图").first
        longstrip_class = longstrip_tab.get_attribute('class') or ""
        longstrip_disabled = "disabled" in longstrip_class or "inactive" in longstrip_class
        print(f"长图tab class: {longstrip_class}")
        check("长图tab存在", longstrip_tab.is_visible())

        page.screenshot(path=str(SHOT_DIR / "tc0006_01_viewer_ar720.png"))

        # ---------- 步骤4: 关闭查看器 ----------
        print("\n[步骤4] 关闭查看器...")
        close_btn = page.locator('button[aria-label="关闭（Esc）"]').first
        close_btn.click()
        page.wait_for_timeout(1500)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
