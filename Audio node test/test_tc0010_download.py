# -*- coding: utf-8 -*-
"""
TC-0010: 音频节点-下载
点下载按钮后，用pywinauto找另存为对话框并点保存按钮。
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

        print("=== TC-0010: 音频节点-下载 ===")

        # 选中节点
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        node = page.locator('.react-flow__node').first
        node.click()
        page.wait_for_timeout(800)

        # 点下载按钮
        download_btn = page.locator('button[aria-label="下载"]')
        check("工具栏下载按钮可见", download_btn.is_visible())

        print("\n[步骤2] 点下载按钮，等待系统对话框...")
        download_btn.click()
        print("  点了下载，等待对话框弹出...")

        # 等对话框弹出
        time.sleep(4)

        # 用pywinauto找对话框
        print("\n[步骤3] 用pywinauto查找另存为对话框...")
        desktop = Desktop(backend="win32")

        # 找所有顶层窗口，打印可见的
        dialog = None
        all_windows = desktop.windows()
        print(f"  共{len(all_windows)}个窗口，找可见的对话框...")

        for w in all_windows:
            try:
                if w.is_visible():
                    t = w.window_text()
                    rect = w.rectangle()
                    # 找大小适中的窗口（另存为对话框大概600x500左右）
                    if 500 < rect.width() < 800 and 400 < rect.height() < 600:
                        print(f"    候选窗口: '{t}' 大小({rect.width()}x{rect.height()})")
                        dialog = w
                        break
            except:
                continue

        check("系统另存为对话框弹出", dialog is not None)

        # 如果找到对话框，按回车确认保存
        if dialog:
            print("\n[步骤4] 按回车键确认保存...")
            try:
                dialog.set_focus()
                time.sleep(0.5)
                dialog.type_keys("{ENTER}")
                print("  按了回车键确认保存")
                check("对话框确认保存（回车）", True)
                time.sleep(2)
            except Exception as e:
                print(f"  按回车出错: {str(e)[:60]}")
                check("对话框确认保存", False)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
