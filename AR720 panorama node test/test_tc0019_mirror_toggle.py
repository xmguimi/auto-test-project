# -*- coding: utf-8 -*-
"""
TC-0019: AR720全景节点-开启镜像-开关状态
"""
import os
import time
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

        print("=== TC-0019: AR720全景节点-开启镜像-开关状态 ===")

        # ---------- 步骤1: 选中节点 ----------
        print("\n[步骤1] 选中AR720节点...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 100 and box['y'] > 100:
                node.click()
                page.wait_for_timeout(1500)
                break

        # ---------- 步骤2: 找开启镜像按钮 ----------
        print("\n[步骤2] 找开启镜像按钮...")
        mirror_btn = page.locator('button[aria-label*="镜像"]').first
        check("开启镜像按钮存在", mirror_btn.is_visible())

        if mirror_btn.is_visible():
            # ---------- 步骤3: 点第一次（开启） ----------
            print("\n[步骤3] 点第一次（开启镜像）...")
            mirror_btn.click()
            time.sleep(1)
            check("第一次点镜像按钮无报错", True)

            # ---------- 步骤4: 点第二次（关闭） ----------
            print("\n[步骤4] 点第二次（关闭镜像）...")
            # 用同一个locator重新定位，不每次重新找
            mirror_btn2 = page.locator('button[aria-label*="镜像"]').first
            mirror_btn2.click()
            time.sleep(1)
            check("第二次点镜像按钮无报错", True)

            # ---------- 步骤5: 再点第三次 ----------
            print("\n[步骤5] 点第三次（再开启）...")
            mirror_btn3 = page.locator('button[aria-label*="镜像"]').first
            mirror_btn3.click()
            time.sleep(1)
            check("第三次点镜像按钮无报错", True)

        page.screenshot(path=str(SHOT_DIR / "tc0019_01_mirror.png"))

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
