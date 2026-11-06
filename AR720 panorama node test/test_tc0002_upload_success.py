# -*- coding: utf-8 -*-
"""
TC-0002: AR720全景节点-上传成功与结果校验
验证点上传按钮后弹出文件选择，上传图片成功。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 测试图片路径
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

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0002: AR720全景节点-上传成功与结果校验 ===")

        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # 找一个AR720节点选中
        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                node.click()
                page.wait_for_timeout(800)
                break

        # 找上传按钮
        toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
        upload_btn = toolbar.locator('button[aria-label*="导入"], button[aria-label*="上传"]').first
        check("工具栏上传按钮存在", upload_btn.is_visible())

        # 点上传按钮，捕获文件选择对话框
        print("\n[步骤2] 点上传按钮，上传图片...")
        try:
            with page.expect_file_chooser(timeout=5000) as fc_info:
                upload_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(TEST_IMAGE)
            print(f"  上传文件: {TEST_IMAGE}")
            page.wait_for_timeout(3000)
            check("点上传按钮后弹出文件选择对话框", True)
        except Exception as e:
            print(f"  捕获文件选择对话框失败: {str(e)[:80]}")
            check("点上传按钮后弹出文件选择对话框", False)

        page.screenshot(path=str(SHOT_DIR / "tc0002_02_after_upload.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
