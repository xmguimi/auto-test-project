# -*- coding: utf-8 -*-
"""
TC-0004: AR720全景节点-上传标准全景图
三种场景：不选类型/选AR720/选长图，上传风景全景图.jpg后验证标签和状态为「已生成」。
三个节点放不同位置，离远一点。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

TEST_IMAGE = r"D:\Desktop\自动化测试\auto-test-project\testdata\风景全景图.jpg"

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
    """点上传按钮上传全景图"""
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

        print("=== TC-0004: AR720全景节点-上传标准全景图 ===")

        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # ---------- 场景A: 不选类型直接上传全景图（画布中心） ----------
        print("\n[场景A] 新建节点（画布中心）不选类型，直接上传全景图...")
        node_a = new_ar720_node(page, offset_x=0, offset_y=0)
        upload_ok_a = upload_image(page)
        check("不选类型上传全景图成功", upload_ok_a)

        nodes = page.locator('.react-flow__node')
        node_a_text = nodes.last.text_content()
        print(f"  节点内容: {node_a_text[:80]}")
        has_ar720_a = "AR720" in node_a_text or "720" in node_a_text
        has_done_a = "已生成" in node_a_text
        check("不选类型默认标签为AR720", has_ar720_a)
        check("不选类型上传全景图后状态为已生成", has_done_a)

        # ---------- 场景B: 选AR720后上传全景图（右上方） ----------
        print("\n[场景B] 新建节点（右上方）选AR720后上传全景图...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        node_b = new_ar720_node(page, offset_x=500, offset_y=-200)  # 右上方，离第一个远
        ar720_card = node_b.locator('text=AR720').first
        ar720_card.click()
        page.wait_for_timeout(800)
        node_b.click()
        page.wait_for_timeout(500)

        upload_ok_b = upload_image(page)
        check("选AR720后上传全景图成功", upload_ok_b)

        nodes = page.locator('.react-flow__node')
        node_b_text = nodes.last.text_content()
        print(f"  节点内容: {node_b_text[:80]}")
        has_ar720_b = "AR720" in node_b_text or "720" in node_b_text
        has_done_b = "已生成" in node_b_text
        check("选AR720后标签为AR720", has_ar720_b)
        check("选AR720后状态为已生成", has_done_b)

        # ---------- 场景C: 选长图后上传全景图（左下方） ----------
        print("\n[场景C] 新建节点（左下方）选长图后上传全景图...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        node_c = new_ar720_node(page, offset_x=-500, offset_y=200)  # 左下方，离前两个都远
        longstrip_card = node_c.locator('text=长图').first
        longstrip_card.click()
        page.wait_for_timeout(800)
        node_c.click()
        page.wait_for_timeout(500)

        upload_ok_c = upload_image(page)
        check("选长图后上传全景图成功", upload_ok_c)

        nodes = page.locator('.react-flow__node')
        node_c_text = nodes.last.text_content()
        print(f"  节点内容: {node_c_text[:80]}")
        has_longstrip_c = "长图" in node_c_text
        has_done_c = "已生成" in node_c_text
        check("选长图后标签为长图", has_longstrip_c)
        check("选长图后状态为已生成", has_done_c)

        page.screenshot(path=str(SHOT_DIR / "tc0004_03_all_panorama.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
