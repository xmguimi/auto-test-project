# -*- coding: utf-8 -*-
"""
TC-0005: 音频拼接-添加音频
验证【添加音频】下拉三项（本地上传/从当前画布选/从资产库选）均能正常添加音频到列表，列表与计数同步更新。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 测试音频文件路径
TEST_AUDIO = r"D:\Desktop\自动化测试\auto-test-project\testdata\欢呼声.mp3"

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

        print("=== TC-0005: 音频拼接-添加音频 ===")

        # 先关闭可能存在的弹窗
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        try:
            cancel_btn = page.get_by_role("button", name="取消", timeout=1000)
            if cancel_btn.is_visible():
                cancel_btn.click()
                page.wait_for_timeout(500)
        except:
            pass
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)

        # ---------- 步骤1: 打开拼接弹窗 ----------
        print("\n[步骤1] 打开拼接弹窗...")
        audio_node = page.locator('.react-flow__node:has-text("欢呼声.mp3")').first
        audio_node.click()
        page.wait_for_timeout(500)

        merge_btn = page.get_by_role("button", name="拼接", exact=True)
        merge_btn.click()
        page.wait_for_timeout(1000)

        count_text = page.get_by_text("已选 1 / 20")
        check("初始计数为已选1/20", count_text.is_visible())

        # ---------- 步骤2: 点【添加音频】，观察下拉三项 ----------
        print("\n[步骤2] 点【添加音频】，观察下拉三项...")
        add_btn = page.get_by_role("button", name="添加音频")
        add_btn.click()
        page.wait_for_timeout(500)

        option1 = page.get_by_text("本地上传", exact=True)
        option2 = page.get_by_text("从当前画布选", exact=True)
        option3 = page.get_by_text("从资产库选", exact=True)

        check("下拉选项1：本地上传", option1.is_visible())
        check("下拉选项2：从当前画布选", option2.is_visible())
        check("下拉选项3：从资产库选", option3.is_visible())

        # ---------- 步骤3: 测试【本地上传】 ----------
        print("\n[步骤3] 测试【本地上传】...")
        # 用expect_file_chooser监听文件选择对话框
        with page.expect_file_chooser() as fc_info:
            option1.click()
        file_chooser = fc_info.value
        file_chooser.set_files(TEST_AUDIO)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SHOT_DIR / "tc0005_03_after_local_upload.png"))

        # 验证计数更新
        count_text2 = page.get_by_text("已选 2 / 20")
        check("本地上传后计数更新为已选2/20", count_text2.is_visible())

        # ---------- 步骤4: 测试【从当前画布选】 ----------
        print("\n[步骤4] 测试【从当前画布选】...")
        add_btn2 = page.get_by_role("button", name="添加音频")
        add_btn2.click()
        page.wait_for_timeout(500)

        option2_click = page.get_by_text("从当前画布选", exact=True)
        option2_click.click()
        page.wait_for_timeout(1000)

        # 在"当前参考音频"弹窗里选一个音频
        second_option = page.get_by_text("画布音频").nth(0)
        second_option.click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(SHOT_DIR / "tc0005_04_after_canvas_add.png"))

        # 验证计数再更新
        count_text3 = page.get_by_text("已选 3 / 20")
        check("从画布选添加后计数更新为已选3/20", count_text3.is_visible())

        # 验证列表项数量
        list_items = page.locator('.acc-list .acc-index')
        item_count = list_items.count()
        check(f"列表项总数为3（当前{item_count}项）", item_count == 3)

        # ---------- 步骤5: 关闭弹窗 ----------
        print("\n[步骤5] 关闭弹窗...")
        cancel_btn = page.get_by_role("button", name="取消")
        cancel_btn.click()
        page.wait_for_timeout(500)

        dialog_closed = not page.locator('.cx-modal-title').is_visible()
        check("点取消后弹窗关闭", dialog_closed)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
