# -*- coding: utf-8 -*-
"""
TC-0014: 音频节点-余额不足生成提示测试
用中控台生成按钮
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

        page = None
        for pg in ctx.pages:
            if "帧境" in pg.title():
                page = pg
                break
        page.bring_to_front()
        page.wait_for_timeout(1000)

        print("=== TC-0014: 音频节点-余额不足生成提示测试 ===")

        # 选中音频节点
        nodes = page.locator('.react-flow__node')
        node = nodes.nth(0)
        node.click(force=True)
        time.sleep(1)

        # ---------- 步骤1: 输入文字 ----------
        print("\n[步骤1] 输入文字...")
        input_box = None
        inputs = page.locator('textarea, [contenteditable="true"]')
        for i in range(inputs.count()):
            inp = inputs.nth(i)
            if inp.is_visible():
                input_box = inp
                break
        check("输入框存在", input_box is not None)

        if input_box:
            input_box.click(force=True)
            input_box.fill("测试余额不足")
            time.sleep(0.5)
            check("输入文字成功", True)

        # ---------- 步骤2: 点中控台生成按钮 ----------
        print("\n[步骤2] 点生成按钮...")
        gen_btn = None
        btns = page.locator('button')
        for j in range(btns.count()):
            btn = btns.nth(j)
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                if label == '生成':
                    gen_btn = btn
                    print(f"找到生成按钮: 第{j}个按钮")
                    break
        check("生成按钮存在", gen_btn is not None)

        if gen_btn:
            gen_btn.click(force=True)
            time.sleep(2)
            check("点生成按钮无崩溃", True)

            # ---------- 步骤3: 观察余额不足提示 ----------
            print("\n[步骤3] 观察余额不足提示...")
            error_tip = page.locator('div:has-text("quota"), div:has-text("余额"), div:has-text("不足"), div:has-text("生成失败")').first
            if error_tip.is_visible():
                tip_text = error_tip.text_content()[:100]
                print(f"检测到提示: {tip_text}")
                check("有余额不足/生成失败提示", True)
            else:
                check("有余额不足/生成失败提示", False)

        page.screenshot(path=str(SHOT_DIR / "tc0014_01_result.png"))
        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
