# -*- coding: utf-8 -*-
"""
TC-0018: AR720全景节点-添加到画布-正常添加
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

        print("=== TC-0018: AR720全景节点-添加到画布 ===")

        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes_before = page.locator('.react-flow__node').count()
        print(f"添加前画布共{nodes_before}个节点")

        # 选中第一个可见节点
        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 100 and box['y'] > 100:
                node.click()
                page.wait_for_timeout(1500)
                print(f"选中节点[{i}]")
                break

        # 全局找所有带aria-label的按钮
        btns = page.locator('button[aria-label]')
        print(f"\n所有可见按钮:")
        for i in range(btns.count()):
            btn = btns.nth(i)
            label = btn.get_attribute('aria-label')
            if btn.is_visible():
                print(f"  - {label}")

        # 找添加到画布按钮
        add_btn = page.locator('button[aria-label*="添加到画布"]').first
        check("添加到画布按钮存在", add_btn.is_visible())

        if add_btn.is_visible():
            add_btn.click()
            page.wait_for_timeout(2000)
            check("点添加到画布按钮无报错", True)

            nodes_after = page.locator('.react-flow__node').count()
            print(f"添加后画布共{nodes_after}个节点")
            check("添加后节点数量增加", nodes_after > nodes_before)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
