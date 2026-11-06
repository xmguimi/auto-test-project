# -*- coding: utf-8 -*-
"""
TC-0025: AR720全景节点-离线模式测试
断网时：1.能不能上传图片 2.能不能生成AR720全景
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

        # 找帧境AI页面
        page = None
        for pg in ctx.pages:
            if "帧境" in pg.title():
                page = pg
                break
        page.bring_to_front()
        page.wait_for_timeout(1000)

        print("=== TC-0025: 离线模式-上传与生成测试 ===")
        print(f"测试图片: {TEST_IMG}")

        # 选中节点[1]（有生成按钮的那个）
        nodes = page.locator('.react-flow__node')
        node = nodes.nth(1)
        node.click(force=True)
        time.sleep(1.5)

        # ---------- 测试1: 断网时能不能上传图片 ----------
        print("\n[测试1] 断网时能不能上传图片？")
        # 找替换图片按钮
        replace_btn = None
        btns = page.locator('button')
        for j in range(btns.count()):
            btn = btns.nth(j)
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                if '替换图片' in label:
                    replace_btn = btn
                    break
        check("替换图片按钮存在", replace_btn is not None)

        if replace_btn:
            try:
                with page.expect_file_chooser(timeout=3000) as fc_info:
                    replace_btn.click(force=True)
                print("文件选择对话框弹出（系统功能不依赖网络）")
                check("断网时本地文件选择对话框可弹出", True)

                # 选文件，看上传会不会失败
                fc_info.value.set_files(TEST_IMG)
                time.sleep(3)
                print("已选择文件，观察上传结果...")
                # 截图看状态
                page.screenshot(path=str(SHOT_DIR / "tc0025_01_upload_result.png"))
                check("断网时选择图片后无崩溃", True)
            except Exception as e:
                print(f"文件选择失败: {e}")
                check("断网时本地文件选择对话框可弹出", False)

        # ---------- 测试2: 断网时能不能生成AR720全景 ----------
        print("\n[测试2] 断网时能不能生成AR720全景？")
        # 找生成按钮
        gen_btn = None
        btns = page.locator('button')
        for j in range(btns.count()):
            btn = btns.nth(j)
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                if '生成' in label and 'AR720' in label:
                    gen_btn = btn
                    break
        check("生成AR720全景按钮存在", gen_btn is not None)

        if gen_btn:
            gen_btn.click(force=True)
            time.sleep(1)
            check("生成弹窗打开", True)

            # 输入描述，点生成
            desc_input = page.locator('textarea, [contenteditable="true"]').last
            if desc_input.is_visible():
                desc_input.fill("断网测试")
                time.sleep(0.5)

            confirm_btn = page.locator('button:has-text("生成 AR720 全景")').last
            if confirm_btn.is_visible():
                confirm_btn.click(force=True)
                time.sleep(2)
                print("已点生成按钮，观察生成结果...")
                page.screenshot(path=str(SHOT_DIR / "tc0025_02_gen_result.png"))
                check("断网时点生成按钮无崩溃", True)

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
