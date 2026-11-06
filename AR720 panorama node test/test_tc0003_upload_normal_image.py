# -*- coding: utf-8 -*-
"""
TC-0003: AR720全景节点-上传普通比例图片
三种场景：不选类型/选AR720/选长图，上传草原.jpg后验证标签和状态。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

TEST_IMAGE = r"D:\Desktop\自动化测试\auto-test-project\testdata\草原.jpg"

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

def new_ar720_node(page, offset_x=0, offset_y=0):
    """双击画布新建AR720节点"""
    canvas = page.locator('.react-flow').first
    box = canvas.bounding_box()
    dbl_x = box['x'] + box['width'] / 2 + offset_x
    dbl_y = box['y'] + box['height'] / 2 - 100 + offset_y
    page.mouse.dblclick(dbl_x, dbl_y)
    page.wait_for_timeout(1000)
    menu_item = page.get_by_text("720 全景节点", exact=False)
    menu_item.click()
    page.wait_for_timeout(1500)
    nodes = page.locator('.react-flow__node')
    new_node = nodes.last
    new_node.click()
    page.wait_for_timeout(800)
    return new_node

def upload_image(page):
    """点上传按钮上传草原.jpg"""
    toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
    upload_btn = toolbar.locator('button[aria-label*="导入"], button[aria-label*="上传"]').first
    try:
        with page.expect_file_chooser(timeout=5000) as fc_info:
            upload_btn.click()
        file_chooser = fc_info.value
        file_chooser.set_files(TEST_IMAGE)
        page.wait_for_timeout(3000)
        return True
    except:
        return False

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0003: AR720全景节点-上传普通比例图片 ===")

        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # ---------- 场景A: 不选类型直接上传 ----------
        print("\n[场景A] 新建节点不选类型，直接上传草原.jpg...")
        node_a = new_ar720_node(page, offset_x=400, offset_y=0)
        upload_ok_a = upload_image(page)
        check("不选类型上传成功", upload_ok_a)

        # 看节点标签和状态
        nodes = page.locator('.react-flow__node')
        node_a_text = nodes.last.text_content()
        print(f"  节点内容: {node_a_text[:80]}")
        has_ar720_a = "AR720" in node_a_text or "720" in node_a_text
        has_pending_a = "待确认" in node_a_text
        check("不选类型默认标签为AR720", has_ar720_a)
        check("不选类型状态为待确认", has_pending_a)

        # ---------- 场景B: 选AR720后上传 ----------
        print("\n[场景B] 新建节点选AR720后上传...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        node_b = new_ar720_node(page, offset_x=400, offset_y=-200)
        ar720_card = node_b.locator('text=AR720').first
        ar720_card.click()
        page.wait_for_timeout(800)
        node_b.click()
        page.wait_for_timeout(500)

        upload_ok_b = upload_image(page)
        check("选AR720后上传成功", upload_ok_b)

        nodes = page.locator('.react-flow__node')
        node_b_text = nodes.last.text_content()
        print(f"  节点内容: {node_b_text[:80]}")
        has_ar720_b = "AR720" in node_b_text or "720" in node_b_text
        has_pending_b = "待确认" in node_b_text
        check("选AR720后标签为AR720", has_ar720_b)
        check("选AR720后状态为待确认", has_pending_b)

        # ---------- 场景C: 选长图后上传 ----------
        print("\n[场景C] 新建节点选长图后上传...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        node_c = new_ar720_node(page, offset_x=-300, offset_y=-200)
        longstrip_card = node_c.locator('text=长图').first
        longstrip_card.click()
        page.wait_for_timeout(800)
        node_c.click()
        page.wait_for_timeout(500)

        upload_ok_c = upload_image(page)
        check("选长图后上传成功", upload_ok_c)

        nodes = page.locator('.react-flow__node')
        node_c_text = nodes.last.text_content()
        print(f"  节点内容: {node_c_text[:80]}")
        has_longstrip_c = "长图" in node_c_text
        has_pending_c = "待确认" in node_c_text
        check("选长图后标签为长图", has_longstrip_c)
        check("选长图后状态为待确认", has_pending_c)

        page.screenshot(path=str(SHOT_DIR / "tc0003_03_all_nodes.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
