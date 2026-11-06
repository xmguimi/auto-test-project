# -*- coding: utf-8 -*-
"""
TC-0016: AR720节点-生成AR720全景-弹窗与参数编辑
重新测试：确保输入框为空时按钮禁用状态
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

        print("=== TC-0016重新测试：空输入框时按钮状态 ===")

        # ---------- 步骤1: 先关闭所有弹窗，重新打开 ----------
        print("\n[步骤1] 重新打开弹窗...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)

        # 选中AR720节点
        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 100 and box['y'] > 100:
                text = node.text_content()
                if "AR720" in text and "已生成" in text:
                    node.click()
                    page.wait_for_timeout(1000)
                    break

        # 点生成按钮
        gen_btn = page.locator('button[aria-label*="生成 AR720"]').first
        gen_btn.click()
        page.wait_for_timeout(2000)

        dialog = page.locator('[role="dialog"]').first
        check("弹窗打开", dialog.is_visible())

        # ---------- 步骤2: 先清空输入框，测试按钮状态 ----------
        print("\n[步骤2] 清空输入框后测试按钮状态...")
        desc_input = dialog.locator('textarea, [contenteditable="true"]').first

        # 先清空输入框
        if desc_input.is_visible():
            desc_input.fill("")
            page.wait_for_timeout(500)
            print("已清空输入框")

        submit_btn = dialog.locator('button:has-text("生成 AR720 全景")').last
        print(f"空输入框时按钮enabled状态: {submit_btn.is_enabled()}")
        check("空输入框时生成按钮禁用", not submit_btn.is_enabled())

        # ---------- 步骤3: 输入文本后测试 ----------
        print("\n[步骤3] 输入文本后测试按钮状态...")
        desc_input.fill("一个开阔的城市广场，四周有高楼和街道")
        page.wait_for_timeout(500)
        print(f"输入文本后按钮enabled状态: {submit_btn.is_enabled()}")
        check("输入文本后生成按钮可用", submit_btn.is_enabled())

        page.screenshot(path=str(SHOT_DIR / "tc0016_02_after_input.png"))

        # 关闭弹窗
        page.keyboard.press('Escape')
        page.wait_for_timeout(1000)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
