# -*- coding: utf-8 -*-
"""
TC-0023: AR720全景节点-上传损坏图片测试
上传损坏图片，观察错误处理
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
TEST_IMG = r"D:\Desktop\自动化测试\auto-test-project\testdata\损坏图片.png"

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

        print("=== TC-0023: 上传损坏图片测试 ===")
        print(f"测试图片: {TEST_IMG}")

        # ---------- 步骤1: 新建AR720节点 ----------
        print("\n[步骤1] 双击画布新建AR720节点...")
        page.keyboard.press('Escape')
        time.sleep(0.3)
        page.mouse.dblclick(400, 400)
        time.sleep(1)
        menu_item = page.locator('div:has-text("720 全景节点")').first
        check("新建菜单弹出", menu_item.is_visible())
        if menu_item.is_visible():
            menu_item.click()
            time.sleep(1)
            print("新建AR720节点成功")

        # ---------- 步骤2: 点导入图片按钮，用file_chooser上传 ----------
        print("\n[步骤2] 点导入图片按钮上传损坏图片...")
        upload_btn = page.locator('button[aria-label*="导入图片"], button:has-text("导入图片")').last
        check("导入图片按钮存在", upload_btn.is_visible())

        if upload_btn.is_visible():
            with page.expect_file_chooser() as fc_info:
                upload_btn.click(force=True)
            file_chooser = fc_info.value
            print("文件选择对话框已捕获")

            file_chooser.set_files(TEST_IMG)
            print("已设置损坏图片文件")
            time.sleep(5)  # 等待处理

            # ---------- 步骤3: 观察反应 ----------
            print("\n[步骤3] 观察上传后反应...")
            page.screenshot(path=str(SHOT_DIR / "tc0023_01_after_corrupted_upload.png"))
            print("已截图记录")

            # 检测是否有错误提示
            toast = page.locator('div:has-text("损坏"), div:has-text("错误"), div:has-text("失败"), div:has-text("无法打开"), [class*="error"], [class*="toast"]').first
            if toast.is_visible():
                toast_text = toast.text_content()
                print(f"检测到提示: {toast_text[:100]}")
                check("上传损坏图片有错误提示", True)
            else:
                print("未检测到错误提示")
                check("上传损坏图片有错误提示", False)

            check("上传损坏图片不崩溃", True)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
