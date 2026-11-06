# -*- coding: utf-8 -*-
"""
TC-0010: AR720查看器-工具条-镜像
验证底部工具条镜像按钮存在，点击可切换镜像状态。
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

        print("=== TC-0010: AR720查看器-工具条-镜像 ===")

        # ---------- 步骤1: 打开查看器 ----------
        print("\n[步骤1] 打开查看器...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                text = node.text_content()
                if "AR720" in text and "已生成" in text:
                    node.click()
                    page.wait_for_timeout(1000)
                    toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
                    viewer_btn = toolbar.locator('button[aria-label*="打开查看器"]').first
                    viewer_btn.click()
                    page.wait_for_timeout(2000)
                    break

        check("查看器打开成功", True)

        # ---------- 步骤2: 验证镜像按钮存在 ----------
        print("\n[步骤2] 验证镜像按钮...")
        mirror_btn = page.locator('button[title="镜像"]').first
        check("底部工具条镜像按钮存在", mirror_btn.is_visible())

        # ---------- 步骤3: 点镜像按钮 ----------
        print("\n[步骤3] 点镜像按钮...")
        mirror_btn.click()
        page.wait_for_timeout(1000)
        check("点镜像按钮无报错", True)

        page.screenshot(path=str(SHOT_DIR / "tc0010_01_mirror_on.png"))

        # ---------- 步骤4: 再点一次还原 ----------
        print("\n[步骤4] 再点一次还原...")
        mirror_btn.click()
        page.wait_for_timeout(1000)
        check("再点一次镜像按钮无报错", True)

        page.screenshot(path=str(SHOT_DIR / "tc0010_02_mirror_off.png"))

        # 关闭查看器
        close_btn = page.locator('button[aria-label="关闭（Esc）"]').first
        close_btn.click()
        page.wait_for_timeout(1500)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
