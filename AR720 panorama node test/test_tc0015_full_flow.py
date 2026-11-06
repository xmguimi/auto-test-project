# -*- coding: utf-8 -*-
"""
完整流程：新建720节点→选长图→上传图片→点生成长图全景→验证参数弹窗
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
TEST_IMG = r"D:\Desktop\自动化测试\auto-test-project\testdata\风景全景图.jpg"

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

        print("=== 完整流程：新建长图节点→上传→生成长图全景 ===")

        # ---------- 步骤1: 双击画布新建节点 ----------
        print("\n[步骤1] 双击画布新建AR720节点...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        canvas = page.locator('.react-flow__pane').first
        box = canvas.bounding_box()
        # 双击右侧空白处
        page.mouse.click(box['x'] + box['width'] * 0.7, box['y'] + box['height'] * 0.5, click_count=2)
        page.wait_for_timeout(1000)

        # 点720全景节点
        menu_item = page.locator('div:has-text("720 全景节点")').first
        if menu_item.is_visible():
            menu_item.click()
            page.wait_for_timeout(1000)
            check("新建720全景节点成功", True)
        else:
            check("新建720全景节点", False)
            browser.close()
            return

        # ---------- 步骤2: 选长图 ----------
        print("\n[步骤2] 选择长图类型...")
        long_tab = page.locator('button:has-text("长图"), div:has-text("长图")').first
        if long_tab.is_visible():
            long_tab.click()
            page.wait_for_timeout(500)
            check("选长图类型", True)
        else:
            check("选长图类型", False)

        # ---------- 步骤3: 上传图片 ----------
        print("\n[步骤3] 上传图片...")
        with page.expect_file_chooser() as fc_info:
            upload_btn = page.locator('button[aria-label*="导入图片"], button[aria-label*="上传"]').first
            upload_btn.click()
        file_chooser = fc_info.value
        file_chooser.set_files(TEST_IMG)
        page.wait_for_timeout(3000)
        check("上传图片成功", True)

        # ---------- 步骤4: 选中节点 ----------
        print("\n[步骤4] 选中节点...")
        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                text = node.text_content()
                if "长图" in text:
                    node.click()
                    page.wait_for_timeout(1500)
                    print(f"选中长图节点[{i}]")
                    break

        # ---------- 步骤5: 找生成长图全景按钮 ----------
        print("\n[步骤5] 找生成长图全景按钮...")
        btns = page.locator('button[aria-label]')
        gen_btn = None
        for i in range(btns.count()):
            btn = btns.nth(i)
            label = btn.get_attribute('aria-label')
            if btn.is_visible() and "生成长图" in label:
                gen_btn = btn
                print(f"找到生成长图按钮: {label}")
                break

        check("找到生成长图全景按钮", gen_btn is not None)

        if gen_btn:
            gen_btn.click()
            page.wait_for_timeout(2000)

            # ---------- 步骤6: 验证参数弹窗 ----------
            print("\n[步骤6] 验证参数弹窗...")
            dialog = page.locator('[role="dialog"]').first
            check("弹窗打开", dialog.is_visible())

            if dialog.is_visible():
                text = dialog.text_content()
                check("有比例选项", "4:1" in text and "21:9" in text and "8:1" in text)
                check("有场景类型", "自动" in text and "室内" in text and "室外" in text)

                # 测试点比例选项
                ratio_btn = dialog.locator('button:has-text("21:9")').first
                ratio_btn.click()
                check("点21:9比例", True)

                # 测试点场景类型
                scene_btn = dialog.locator('button:has-text("室外")').first
                scene_btn.click()
                check("点室外场景", True)

                # 关闭弹窗
                page.keyboard.press('Escape')
                page.wait_for_timeout(1000)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
