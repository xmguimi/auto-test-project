# -*- coding: utf-8 -*-
"""
TC-0020: AR720全景节点-显示节点信息-开关状态
真正检测面板展开/收起状态，不只看按钮可点
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
    """模糊找信息按钮"""
    btns = page.locator('button')
    for i in range(btns.count()):
        btn = btns.nth(i)
        label = btn.get_attribute('aria-label') or ''
        title = btn.get_attribute('title') or ''
        if btn.is_visible() and ('节点信息' in label or '节点信息' in title):
            return btn
    return None

def is_panel_open(page):
    """检测信息面板是否展开（找面板内容）"""
    panel = page.locator('div:has-text("文件位置"):has-text("一键复用")').first
    return panel.is_visible()

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0020: AR720全景节点-显示节点信息-开关状态 ===")

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

        # 初始状态：面板应该是收起的
        print("\n初始状态：面板是否展开？")
        check("初始面板收起", not is_panel_open(page))

        # 第一次点：展开面板
        print("\n点第一次（展开面板）...")
        btn1 = find_info_btn(page)
        if btn1:
            btn1.click()
            time.sleep(1)
            check("第一次点后面板展开", is_panel_open(page))
        else:
            check("找到信息按钮", False)

        # 第二次点：收起面板
        print("\n点第二次（收起面板）...")
        btn2 = find_info_btn(page)
        if btn2:
            btn2.click()
            time.sleep(1)
            check("第二次点后面板收起", not is_panel_open(page))
        else:
            check("第二次找到信息按钮", False)

        # 第三次点：再展开
        print("\n点第三次（再展开）...")
        btn3 = find_info_btn(page)
        if btn3:
            btn3.click()
            time.sleep(1)
            check("第三次点后面板再次展开", is_panel_open(page))

        page.screenshot(path=str(SHOT_DIR / "tc0020_01_panel_state.png"))

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
