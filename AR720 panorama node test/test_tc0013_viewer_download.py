# -*- coding: utf-8 -*-
"""
TC-0013: AR720全景节点-下载
验证节点悬浮工具栏下载按钮存在，点击后弹出系统另存为对话框。
用Windows标准对话框固定class名匹配，跨电脑通用。
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

def count_save_dialogs():
    """用Windows标准对话框class名统计另存为对话框数量（跨电脑通用）"""
    desktop = Desktop(backend="win32")
    count = 0
    for w in desktop.windows():
        try:
            if w.is_visible():
                cls = w.class_name()
                # Windows标准对话框class是#32770，所有系统的另存为/打开对话框都是这个class
                if cls == "#32770":
                    count += 1
        except:
            pass
    return count

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0013: AR720全景节点-下载 ===")

        # ---------- 步骤1: 找AR720节点并选中 ----------
        print("\n[步骤1] 选中AR720节点...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                text = node.text_content()
                if "AR720" in text and "已生成" in text:
                    node.click()
                    page.wait_for_timeout(1000)
                    print(f"找到AR720节点（第{i}个）")
                    break

        # ---------- 步骤2: 验证节点工具栏下载按钮存在 ----------
        print("\n[步骤2] 验证节点悬浮工具栏下载按钮...")
        toolbar = page.locator('[class*="toolbar"], [class*="float-bar"]').first
        download_btn = toolbar.locator('button[aria-label*="下载"]').first
        download_label = download_btn.get_attribute('aria-label')
        print(f"下载按钮aria-label: {download_label}")
        check("节点工具栏下载按钮存在", "下载" in download_label)

        # ---------- 步骤3: 点下载按钮，检测另存为对话框 ----------
        print("\n[步骤3] 点下载按钮，检测系统对话框...")
        dialogs_before = count_save_dialogs()
        print(f"点之前另存为对话框数量: {dialogs_before}")

        download_btn.click()
        print("等待4秒...")
        time.sleep(4)

        dialogs_after = count_save_dialogs()
        print(f"点之后另存为对话框数量: {dialogs_after}")
        check("点下载后弹出系统另存为对话框", dialogs_after > dialogs_before)

        # 按Esc取消
        print("按Esc取消对话框...")
        page.keyboard.press('Escape')
        time.sleep(1)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
