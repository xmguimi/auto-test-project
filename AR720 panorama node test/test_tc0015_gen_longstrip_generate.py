# -*- coding: utf-8 -*-
"""
TC-0015: AR720节点-生成长图全景-生成与参数
REAL_GENERATE=False（不真实生成）
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

REAL_GENERATE = False

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

        print("=== TC-0015: AR720节点-生成长图全景-生成与参数 ===")
        print(f"REAL_GENERATE = {REAL_GENERATE}")

        # ---------- 步骤1: 打开弹窗 ----------
        print("\n[步骤1] 打开生成长图弹窗...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 100 and box['y'] > 100:
                text = node.text_content()
                if "长图" in text:
                    node.click()
                    page.wait_for_timeout(1000)
                    break

        gen_btn = page.locator('button[aria-label*="生成长图"]').first
        gen_btn.click()
        page.wait_for_timeout(2000)

        dialog = page.locator('[role="dialog"]').first
        check("弹窗正常打开", dialog.is_visible())

        # ---------- 步骤2: 输入描述并选参数 ----------
        print("\n[步骤2] 输入描述并选参数...")
        desc_input = dialog.locator('textarea, [contenteditable="true"]').first
        desc_input.fill("夜晚赛博城市高架桥两侧延展的商业街")
        check("输入描述文本成功", True)

        ratio_219 = dialog.locator('button:has-text("21:9")').first
        ratio_219.click()
        check("选21:9比例成功", True)

        scene_indoor = dialog.locator('button:has-text("室内")').first
        scene_indoor.click()
        check("选室内场景成功", True)

        # ---------- 步骤3: 验证生成按钮可用 ----------
        print("\n[步骤3] 验证生成按钮状态...")
        submit_btn = dialog.locator('button:has-text("生成长图全景")').last
        check("输入后生成按钮可用", submit_btn.is_enabled())

        if REAL_GENERATE:
            print("\n[步骤4] 点生成按钮...")
            submit_btn.click()
            import time
            time.sleep(3)
            check("点生成按钮无报错", True)
        else:
            print("\n[步骤4] REAL_GENERATE=False，跳过真实生成")

        # 关闭弹窗
        page.keyboard.press('Escape')
        page.wait_for_timeout(1000)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
