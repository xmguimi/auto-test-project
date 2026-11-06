# -*- coding: utf-8 -*-
"""
TC-0001: AR720全景节点-初始态与上传入口
完整流程：新建节点→验证默认按钮→选AR720→再新建选长图→验证按钮切换。
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

def get_first_toolbar_btn(page):
    """获取悬浮工具栏最左按钮的aria-label"""
    toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
    if toolbar.is_visible():
        btn = toolbar.locator('button').first
        return btn.get_attribute('aria-label') or ""
    return ""

def new_ar720_node(page, offset_x=0, offset_y=0):
    """双击画布新建AR720节点，offset_x/offset_y是相对于画布中心的偏移"""
    canvas = page.locator('.react-flow').first
    box = canvas.bounding_box()
    dbl_x = box['x'] + box['width'] / 2 + offset_x
    dbl_y = box['y'] + box['height'] / 2 - 100 + offset_y
    page.mouse.dblclick(dbl_x, dbl_y)
    page.wait_for_timeout(1000)
    # 点菜单里的"720 全景节点"
    menu_item = page.get_by_text("720 全景节点", exact=False)
    menu_item.click()
    page.wait_for_timeout(1500)
    # 选中新节点
    nodes = page.locator('.react-flow__node')
    new_node = nodes.last
    new_node.click()
    page.wait_for_timeout(800)
    return new_node

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0001: AR720全景节点-初始态与上传入口 ===")

        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # ---------- 步骤1: 新建第一个AR720节点，验证默认最左按钮 ----------
        print("\n[步骤1] 新建第一个AR720节点，验证默认最左按钮...")
        node1 = new_ar720_node(page)
        btn_label_default = get_first_toolbar_btn(page)
        print(f"  默认最左按钮: {btn_label_default}")
        check("初始态默认最左按钮为「生成 AR720 全景」", "AR720" in btn_label_default)

        # ---------- 步骤2: 点AR720卡片，验证按钮 ----------
        print("\n[步骤2] 点AR720卡片，验证最左按钮...")
        ar720_card = node1.locator('text=AR720').first
        ar720_card.click()
        page.wait_for_timeout(800)
        node1.click()
        page.wait_for_timeout(500)

        btn_label_ar720 = get_first_toolbar_btn(page)
        print(f"  选AR720后最左按钮: {btn_label_ar720}")
        check("选AR720后最左按钮仍为「生成 AR720 全景」", "AR720" in btn_label_ar720)

        # ---------- 步骤3: 新建第二个AR720节点，选长图 ----------
        print("\n[步骤3] 新建第二个AR720节点（往左上方偏移），选长图卡片...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        node2 = new_ar720_node(page, offset_x=-300, offset_y=-150)  # 往左上方挪，离第一个节点远
        longstrip_card = node2.locator('text=长图').first
        longstrip_card.click()
        page.wait_for_timeout(800)
        node2.click()
        page.wait_for_timeout(500)

        btn_label_longstrip = get_first_toolbar_btn(page)
        print(f"  选长图后最左按钮: {btn_label_longstrip}")
        check("选长图后最左按钮变为「生成长图全景」", "长图" in btn_label_longstrip)

        page.screenshot(path=str(SHOT_DIR / "tc0001_01_final.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
