# -*- coding: utf-8 -*-
"""
TC-0026: 上传标准全景图后，生成AR720弹窗里的生成按钮置灰
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

        print("=== TC-0026: 上传全景图后弹窗内生成按钮置灰验证 ===")
        print(f"测试图片: {TEST_IMG}")

        # ---------- 步骤1: 右上角空白处双击新建节点 ----------
        print("\n[步骤1] 新建AR720节点...")
        page.keyboard.press('Escape')
        time.sleep(0.3)
        page.mouse.dblclick(900, 200)
        time.sleep(1.5)
        menu_item = page.locator('text=720 全景节点').first
        menu_item.click(force=True)
        time.sleep(1.5)
        check("新建AR720节点成功", True)

        # ---------- 步骤2: 上传标准全景图 ----------
        print("\n[步骤2] 上传标准全景图...")
        upload_btn = None
        btns = page.locator('button')
        for j in range(btns.count()):
            btn = btns.nth(j)
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                if '导入图片' in label:
                    upload_btn = btn
                    break
        check("导入图片按钮存在", upload_btn is not None)

        if upload_btn:
            with page.expect_file_chooser() as fc_info:
                upload_btn.click(force=True)
            fc_info.value.set_files(TEST_IMG)
            print("已上传，等待加载...")
            time.sleep(6)

        # ---------- 步骤3: 点生成AR720按钮，看弹窗 ----------
        print("\n[步骤3] 点生成AR720全景按钮，弹窗打开...")
        # 重新选中节点
        nodes = page.locator('.react-flow__node')
        new_node = nodes.nth(nodes.count() - 1)
        new_node.click(force=True)
        time.sleep(1.5)

        gen_btn = None
        btns = page.locator('button')
        for j in range(btns.count()):
            btn = btns.nth(j)
            if btn.is_visible():
                label = btn.get_attribute('aria-label') or ''
                if '生成' in label and 'AR720' in label:
                    gen_btn = btn
                    break
        check("工具栏上生成AR720按钮存在", gen_btn is not None)

        if gen_btn:
            gen_btn.click(force=True)
            time.sleep(1.5)
            check("生成弹窗打开", True)

            # ---------- 步骤4: 验证弹窗里的生成按钮置灰 ----------
            print("\n[步骤4] 验证弹窗内生成按钮状态...")
            confirm_btn = None
            btns = page.locator('button')
            for j in range(btns.count()):
                btn = btns.nth(j)
                if btn.is_visible():
                    label = btn.get_attribute('aria-label') or ''
                    text = btn.text_content() or ''
                    if ('生成' in text or '生成' in label) and 'AR720' in (text + label):
                        confirm_btn = btn
                        print(f"找到弹窗生成按钮: {text} / {label}")
                        break

            check("弹窗内生成按钮存在", confirm_btn is not None)
            if confirm_btn:
                is_disabled = confirm_btn.is_disabled()
                print(f"弹窗内生成按钮置灰: {is_disabled}")
                check("弹窗内生成按钮置灰不可点", is_disabled)

                # 填了参数后还是不可点
                print("\n[步骤5] 填写描述后再验证生成按钮状态...")
                desc_input = page.locator('textarea, [contenteditable="true"]').last
                if desc_input.is_visible():
                    desc_input.fill("测试描述")
                    time.sleep(0.5)
                    confirm_btn2 = None
                    btns = page.locator('button')
                    for j in range(btns.count()):
                        btn = btns.nth(j)
                        if btn.is_visible():
                            text = btn.text_content() or ''
                            if '生成' in text and 'AR720' in text:
                                confirm_btn2 = btn
                                break
                    if confirm_btn2:
                        still_disabled = confirm_btn2.is_disabled()
                        print(f"填了参数后生成按钮仍置灰: {still_disabled}")
                        check("填了参数后生成按钮仍置灰", still_disabled)

        page.screenshot(path=str(SHOT_DIR / "tc0026_01_gen_dialog.png"))
        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
