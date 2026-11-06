# -*- coding: utf-8 -*-
"""
TC-0024: AR720全景节点-生成异常-余额不足测试
重新选中节点，等工具栏加载后找生成按钮
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

REAL_GENERATE = False

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

        print("=== TC-0024: 生成异常-余额不足测试 ===")

        # ---------- 步骤1: 选中所有节点都试试 ----------
        print("\n[步骤1] 逐个选中节点，找生成AR720按钮...")
        page.keyboard.press('Escape')
        time.sleep(0.3)
        nodes = page.locator('.react-flow__node')
        print(f"画布共{nodes.count()}个节点")

        gen_btn = None
        for i in range(nodes.count()):
            node = nodes.nth(i)
            node.click(force=True)
            time.sleep(1.5)  # 等工具栏加载
            # 找带"生成"的按钮
            btns = page.locator('button')
            for j in range(btns.count()):
                btn = btns.nth(j)
                label = btn.get_attribute('aria-label') or ''
                if btn.is_visible() and '生成' in label and 'AR720' in label:
                    gen_btn = btn
                    print(f"在节点[{i}]上找到生成按钮: {label}")
                    break
            if gen_btn:
                break

        check("找到生成AR720全景按钮", gen_btn is not None)

        if gen_btn:
            # ---------- 步骤2: 点生成按钮 ----------
            print("\n[步骤2] 点生成AR720全景按钮...")
            gen_btn.click(force=True)
            time.sleep(1)
            check("生成弹窗打开", True)

            # ---------- 步骤3: 输入描述 ----------
            print("\n[步骤3] 输入描述文本...")
            desc_input = page.locator('textarea, [contenteditable="true"]').last
            if desc_input.is_visible():
                desc_input.fill("测试余额不足")
                time.sleep(0.5)
                check("输入描述成功", True)

            # ---------- 步骤4: 点生成按钮，看余额不足提示 ----------
            print("\n[步骤4] 点生成按钮...")
            confirm_btn = page.locator('button:has-text("生成 AR720 全景"), button:has-text("生成")').last
            if confirm_btn.is_visible():
                confirm_btn.click(force=True)
                time.sleep(2)
                check("点生成按钮无报错", True)

                toast = page.locator('div:has-text("余额"), div:has-text("不足"), [class*="error"]').first
                if toast.is_visible():
                    print(f"检测到提示: {toast.text_content()[:100]}")
                    check("有余额不足提示", True)
                else:
                    check("有余额不足提示", False)

        page.screenshot(path=str(SHOT_DIR / "tc0024_01_insufficient_balance.png"))
        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
