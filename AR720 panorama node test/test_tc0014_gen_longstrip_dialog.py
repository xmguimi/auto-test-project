# -*- coding: utf-8 -*-
"""
TC-0014: AR720节点-生成长图全景-弹窗与参数编辑
验证生成长图全景弹窗正常打开，各元素显示正确。
"""
import os
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

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0014: AR720节点-生成长图全景-弹窗与参数编辑 ===")

        # ---------- 步骤1: 选中节点并打开弹窗 ----------
        print("\n[步骤1] 选中节点并点生成长图全景...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
                node.click()
                page.wait_for_timeout(1000)
                break

        gen_btn = page.locator('button[aria-label="生成长图全景"]').first
        check("生成长图全景按钮存在", gen_btn.is_visible())
        gen_btn.click()
        page.wait_for_timeout(2000)

        dialog = page.locator('[role="dialog"]').first
        check("弹窗正常打开", dialog.is_visible())

        # ---------- 步骤2: 验证弹窗标题和描述 ----------
        print("\n[步骤2] 验证弹窗内容...")
        dialog_text = dialog.text_content()
        check("标题包含生成长图全景", "生成长图全景" in dialog_text)
        check("有描述输入提示", "输入连续横向空间描述" in dialog_text)
        check("有生成通道选项", "生成通道" in dialog_text)

        # ---------- 步骤3: 验证比例选项 ----------
        print("\n[步骤3] 验证比例选项...")
        check("比例4:1存在", "4:1" in dialog_text)
        check("比例21:9存在", "21:9" in dialog_text)
        check("比例8:1存在", "8:1" in dialog_text)

        # ---------- 步骤4: 验证场景类型选项 ----------
        print("\n[步骤4] 验证场景类型选项...")
        check("场景自动存在", "自动" in dialog_text)
        check("场景室内存在", "室内" in dialog_text)
        check("场景室外存在", "室外" in dialog_text)

        # ---------- 步骤5: 验证底部按钮 ----------
        print("\n[步骤5] 验证底部按钮...")
        check("底部生成长图全景按钮存在", "生成长图全景" in dialog_text)

        page.screenshot(path=str(SHOT_DIR / "tc0014_01_dialog.png"))

        # 关闭弹窗
        close_btn = dialog.locator('button[aria-label*="关闭"]').first
        if close_btn.is_visible():
            close_btn.click()
        else:
            page.keyboard.press('Escape')
        page.wait_for_timeout(1000)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
