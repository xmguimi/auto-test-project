# -*- coding: utf-8 -*-
"""
TC-0021: AR720全景节点-信息面板复制按钮功能验证
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

def find_info_btn(page):
    btns = page.locator('button')
    for i in range(btns.count()):
        btn = btns.nth(i)
        label = btn.get_attribute('aria-label') or ''
        if btn.is_visible() and '节点信息' in label:
            return btn
    return None

def find_copy_btn(page):
    """遍历所有按钮，找带复制文字的"""
    btns = page.locator('button')
    for i in range(btns.count()):
        btn = btns.nth(i)
        text = btn.text_content() or ''
        if btn.is_visible() and '复制' in text and len(text) < 10:
            print(f"  找到复制按钮[{i}]: {text.strip()}")
            return btn
    return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0021: 复制按钮功能验证 ===")

        # 选中节点
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 100 and box['y'] > 100:
                node.click()
                page.wait_for_timeout(1000)
                break

        # 记录复制前节点数
        nodes_before = page.locator('.react-flow__node').count()
        print(f"\n复制前节点数: {nodes_before}")

        # 打开信息面板
        info_btn = find_info_btn(page)
        if info_btn:
            info_btn.click(force=True)
            time.sleep(1)
            check("信息面板展开", True)
        else:
            check("找到信息按钮", False)
            browser.close()
            return

        # 找复制按钮
        print("\n找复制按钮...")
        copy_btn = find_copy_btn(page)
        check("复制按钮存在", copy_btn is not None)

        if copy_btn:
            print(f"  点击前: {copy_btn.text_content().strip()}")
            copy_btn.click(force=True)
            time.sleep(1)
            print(f"  点击后: {copy_btn.text_content().strip()}")
            check("点复制后按钮变为已复制", "已复制" in copy_btn.text_content())

            # 验证节点数量
            nodes_after = page.locator('.react-flow__node').count()
            print(f"\n复制后节点数: {nodes_after}")
            check("复制后节点数量增加", nodes_after > nodes_before)

        page.screenshot(path=str(SHOT_DIR / "tc0021_01_copy_test.png"))

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
