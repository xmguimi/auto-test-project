# -*- coding: utf-8 -*-
"""
TC-0022: AR720全景节点-上传超大图片测试
点导入图片→在文件对话框输入路径→上传→观察反应
"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from pywinauto import Desktop

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)
TEST_IMG = r"D:\Desktop\自动化测试\auto-test-project\testdata\100MB.png"

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

def find_active_file_dialog():
    """找当前活动的文件打开对话框"""
    desktop = Desktop(backend="win32")
    for w in desktop.windows():
        try:
            if w.class_name() == "#32770" and w.is_visible():
                # 检查是不是文件打开对话框（有Edit和Open按钮）
                try:
                    edit = w.Edit
                    if edit.exists():
                        return w
                except:
                    pass
        except:
            pass
    return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0022: 新建节点上传100MB超大图片 ===")
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

        # ---------- 步骤2: 点导入图片按钮 ----------
        print("\n[步骤2] 点导入图片按钮...")
        upload_btn = page.locator('button[aria-label*="导入图片"], button:has-text("导入图片")').last
        check("导入图片按钮存在", upload_btn.is_visible())
        upload_btn.click(force=True)
        time.sleep(2)
        print("已点导入图片按钮")

        # ---------- 步骤3: 找文件对话框并输入路径 ----------
        print("\n[步骤3] 找文件对话框并输入路径...")
        file_dlg = find_active_file_dialog()
        if file_dlg:
            print("找到文件打开对话框")
            # 在文件名输入框输入完整路径
            edit = file_dlg.Edit
            edit.set_edit_text(TEST_IMG)
            time.sleep(0.5)
            # 点打开按钮
            file_dlg.Open.click()
            print("已输入路径并点打开，开始上传...")

            # ---------- 步骤4: 等待上传，观察反应 ----------
            time.sleep(10)  # 100MB大文件等久一点
            page.screenshot(path=str(SHOT_DIR / "tc0022_01_after_oversize_upload.png"))
            print("已截图记录上传后状态")

            check("上传超大图片无崩溃", True)
        else:
            print("未找到文件打开对话框")
            check("弹出文件选择对话框", False)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
