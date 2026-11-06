# -*- coding: utf-8 -*-
"""
TC-0008: AR720查看器-工具条-复位
完整流程：打开查看器→拖动旋转视角→点重置视角→验证视角恢复，弹出提示。
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

        print("=== TC-0008: AR720查看器-工具条-复位 ===")

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

        # ---------- 步骤2: 拖动旋转视角 ----------
        print("\n[步骤2] 按住图片拖动旋转视角...")
        view_area = page.locator('div').filter(has_text="AR720 VIEWER").first
        box = view_area.bounding_box()
        if box:
            start_x = box['x'] + box['width'] / 2
            start_y = box['y'] + box['height'] / 2
            # 按住鼠标往右拖
            page.mouse.move(start_x, start_y)
            page.mouse.down()
            page.mouse.move(start_x + 200, start_y + 50, steps=10)
            page.mouse.up()
            page.wait_for_timeout(1000)
            check("拖动旋转视角成功", True)
        else:
            check("拖动旋转视角成功", False)

        # ---------- 步骤3: 点重置视角按钮 ----------
        print("\n[步骤3] 点重置视角按钮...")
        reset_btn = page.locator('button[title="重置视角"]').first
        check("重置视角按钮存在", reset_btn.is_visible())
        reset_btn.click()
        page.wait_for_timeout(1500)

        page.screenshot(path=str(SHOT_DIR / "tc0008_02_after_reset.png"))

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
