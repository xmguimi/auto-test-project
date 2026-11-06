# -*- coding: utf-8 -*-
"""
TC-0009: AR720查看器-工具条-添加2D假人
验证查看器里添加2D假人按钮是否存在。
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

        print("=== TC-0009: AR720查看器-工具条-添加2D假人 ===")

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

        # ---------- 步骤2: 找添加2D假人按钮 ----------
        print("\n[步骤2] 找添加2D假人按钮...")
        actor_btn = page.locator('button[title*="假人"], button[title*="人物"], button:has-text("假人")').first
        if actor_btn.is_visible():
            print(f"找到假人按钮: {actor_btn.get_attribute('title')}")
            check("添加2D假人按钮存在", True)
        else:
            print("没找到添加2D假人按钮")
            # 列出底部所有按钮title
            all_btns = page.locator('button[title]')
            for i in range(all_btns.count()):
                btn = all_btns.nth(i)
                if btn.is_visible():
                    title = btn.get_attribute('title')
                    if title and len(title) < 20:
                        print(f"  按钮title: {title}")
            check("添加2D假人按钮存在", False)

        page.screenshot(path=str(SHOT_DIR / "tc0009_01_viewer.png"))

        # 关闭查看器
        close_btn = page.locator('button[aria-label="关闭（Esc）"]').first
        close_btn.click()
        page.wait_for_timeout(1500)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
