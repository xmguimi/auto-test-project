# -*- coding: utf-8 -*-
"""
TC-0012: 音频节点-文本转语音生成
验证底部中控台输入区域存在。TTS生成是付费功能（约¥0.09），REAL_GENERATE=False不实际生成。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# TTS生成是付费功能，不实际生成
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

        print("=== TC-0012: 音频节点-文本转语音生成 ===")

        # ---------- 步骤1: 验证底部输入区域存在 ----------
        print("\n[步骤1] 验证底部输入区域存在...")
        input_area = page.locator('div[role="textbox"]').last
        check("底部中控台输入框可见", input_area.is_visible())

        page.screenshot(path=str(SHOT_DIR / "tc0012_01_bottom_panel.png"))

        if REAL_GENERATE:
            print("\n  REAL_GENERATE=True，实际生成...")
        else:
            print("\n  REAL_GENERATE=False（TTS生成付费约¥0.09），不实际生成")

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
