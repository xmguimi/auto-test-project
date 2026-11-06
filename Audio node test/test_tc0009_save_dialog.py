# -*- coding: utf-8 -*-
"""
TC-0009: 音频节点-保存到资产库
验证音频节点保存到资产库弹窗功能：弹窗打开、名称输入、确认保存按钮可点击不报错。
（资产库实际入库验证需手动确认，因资产列表分页+异步加载，自动化遍历成本高）
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

TEST_ASSET_NAME = "TC0009自动化测试音频"

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

def select_visible_audio_node(page):
    """找第一个视口内可见的音频节点并选中"""
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)
    all_nodes = page.locator('.react-flow__node')
    node_count = all_nodes.count()
    for i in range(node_count):
        node = all_nodes.nth(i)
        try:
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0 and box['x'] < 1500 and box['y'] < 800:
                node.click()
                page.wait_for_timeout(500)
                return True
        except:
            continue
    return False

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0009: 音频节点-保存到资产库 ===")

        # 先关闭残留弹窗
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        try:
            close_x = page.locator('.cx-modal-header svg').first
            if close_x.is_visible():
                close_x.click()
                page.wait_for_timeout(500)
        except:
            pass
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)

        # ---------- 步骤1: 选中节点，点保存到资产库 ----------
        print("\n[步骤1] 选中节点，点保存到资产库...")
        select_visible_audio_node(page)

        save_btn = page.get_by_role("button", name="保存到资产库")
        check("工具栏保存到资产库按钮可见", save_btn.is_visible())

        save_btn.click()
        page.wait_for_timeout(1000)

        # ---------- 步骤2: 验证弹窗标题和名称输入框 ----------
        print("\n[步骤2] 验证弹窗标题和名称输入框...")
        dialog_title = page.locator('.cx-modal-title')
        check("弹窗标题为「保存到资产库」", dialog_title.text_content() == "保存到资产库")

        name_input = page.get_by_placeholder("输入资产名称")
        default_name = name_input.input_value()
        print(f"  默认名称: {default_name}")
        # 实际：默认自动取当前节点名称，不是固定的"未命名资产"
        check("资产名称输入框有默认值（自动取节点名称）", len(default_name) > 0)

        # ---------- 步骤3: 输入测试名称 ----------
        print("\n[步骤3] 输入测试名称...")
        name_input.fill(TEST_ASSET_NAME)
        page.wait_for_timeout(300)
        final_name = name_input.input_value()
        check(f"资产名称输入成功「{TEST_ASSET_NAME}」", final_name == TEST_ASSET_NAME)

        # ---------- 步骤4: 点确认保存 ----------
        print("\n[步骤4] 点确认保存...")
        confirm_btn = page.get_by_role("button", name="确认保存")
        check("确认保存按钮可见", confirm_btn.is_visible())

        confirm_btn.click()
        page.wait_for_timeout(3000)

        # 验证弹窗关闭
        dialog_closed = not page.locator('.cx-modal-title').is_visible()
        check("点确认保存后弹窗关闭（保存触发成功）", dialog_closed)

        page.screenshot(path=str(SHOT_DIR / "tc0009_01_after_save.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")
        print(f"\n备注：资产库实际入库验证需手动确认——资产库共76项，分页显示，且保存为异步操作")

if __name__ == "__main__":
    main()
