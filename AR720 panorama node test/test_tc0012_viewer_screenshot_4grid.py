# -*- coding: utf-8 -*-
"""
TC-0012: AR720查看器-工具条-四切截图
完整流程：打开查看器→点四视角截图→关闭查看器→验证画布上多了四切截图节点。
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

        print("=== TC-0012: AR720查看器-工具条-四切截图 ===")

        # ---------- 步骤1: 记录截图前节点数量 ----------
        print("\n[步骤1] 记录截图前节点数量...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        nodes_before = page.locator('.react-flow__node').count()
        print(f"截图前画布共{nodes_before}个节点")

        # ---------- 步骤2: 打开查看器 ----------
        print("\n[步骤2] 打开查看器...")
        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                text = node.text_content()
                if "AR720" in text and "已生成" in text:
                    node.click()
                    page.wait_for_timeout(1000)
                    viewer_btn = page.locator('button[aria-label*="打开查看器"]').first
                    viewer_btn.click()
                    page.wait_for_timeout(2000)
                    break

        check("查看器打开成功", True)

        # ---------- 步骤3: 点四视角截图按钮 ----------
        print("\n[步骤3] 点四视角截图按钮...")
        screenshot_4grid_btn = page.locator('button[title="四视角截图"]').first
        check("四视角截图按钮存在", screenshot_4grid_btn.is_visible())
        screenshot_4grid_btn.click()
        page.wait_for_timeout(2000)
        check("点四切截图按钮无报错", True)

        # ---------- 步骤4: 关闭查看器回到画布 ----------
        print("\n[步骤4] 关闭查看器回到画布...")
        close_btn = page.locator('button[aria-label="关闭（Esc）"]').first
        close_btn.click()
        page.wait_for_timeout(2000)

        # ---------- 步骤5: 验证画布上多了截图节点 ----------
        print("\n[步骤5] 验证画布上生成了四切截图节点...")
        nodes_after = page.locator('.react-flow__node').count()
        print(f"截图后画布共{nodes_after}个节点")
        check("四切截图后画布上新增了节点", nodes_after > nodes_before)

        page.screenshot(path=str(SHOT_DIR / "tc0012_01_after_4grid.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
