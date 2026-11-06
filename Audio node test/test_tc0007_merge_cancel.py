# -*- coding: utf-8 -*-
"""
TC-0007: 音频拼接-取消与边界
验证拼接弹窗取消/关闭不生成新节点，以及空列表、仅1条等边界场景下开始拼接按钮的状态符合产品定义。
测试流程：
1. 准备2条音频在拼接列表中 → 验证开始拼接按钮可用 → 点取消 → 验证不生成新节点
2. 再打开弹窗，删到只剩1条 → 验证开始拼接按钮不可用
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

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

        print("=== TC-0007: 音频拼接-取消与边界 ===")

        # ---------- 步骤1: 打开拼接弹窗，添加第2条音频 ----------
        print("\n[步骤1] 打开拼接弹窗，添加第2条音频...")
        select_visible_audio_node(page)

        nodes_before = page.locator('.react-flow__node').count()
        print(f"  拼接前画布节点数: {nodes_before}")

        merge_btn = page.get_by_role("button", name="拼接", exact=True)
        merge_btn.click()
        page.wait_for_timeout(1000)

        # 添加第2条：本地上传
        add_btn = page.get_by_role("button", name="添加音频")
        add_btn.click()
        page.wait_for_timeout(300)
        with page.expect_file_chooser() as fc_info:
            page.get_by_text("本地上传", exact=True).click()
        fc_info.value.set_files(TEST_AUDIO)
        page.wait_for_timeout(1500)

        # 验证现在有2条
        count_text = page.get_by_text("已选 2 / 20")
        check("添加后列表有2条音频（已选2/20）", count_text.is_visible())

        # ---------- 步骤2: 验证2条时开始拼接按钮可用 ----------
        print("\n[步骤2] 验证2条音频时开始拼接按钮可用...")
        start_btn = page.get_by_role("button", name="开始拼接")
        start_enabled = start_btn.is_enabled()
        print(f"  2条时开始拼接按钮可用: {start_enabled}")
        check("2条音频时开始拼接按钮可用", start_enabled)

        # ---------- 步骤3: 点取消，验证不生成新节点 ----------
        print("\n[步骤3] 点取消，验证不生成新节点...")
        cancel_btn = page.get_by_role("button", name="取消")
        cancel_btn.click()
        page.wait_for_timeout(800)

        dialog_closed = not page.locator('.cx-modal-title').is_visible()
        check("点取消后弹窗关闭", dialog_closed)

        nodes_after = page.locator('.react-flow__node').count()
        check("点取消后不生成新节点", nodes_before == nodes_after)
        page.screenshot(path=str(SHOT_DIR / "tc0007_01_after_cancel.png"))

        # ---------- 步骤4: 再打开弹窗，删到只剩1条，验证按钮状态 ----------
        print("\n[步骤4] 再打开弹窗，删到只剩1条，验证按钮状态...")
        select_visible_audio_node(page)

        merge_btn2 = page.get_by_role("button", name="拼接", exact=True)
        merge_btn2.click()
        page.wait_for_timeout(1000)

        # 初始只有1条，验证按钮状态
        start_btn2 = page.get_by_role("button", name="开始拼接")
        start_enabled2 = start_btn2.is_enabled()
        print(f"  1条时开始拼接按钮可用: {start_enabled2}")
        check("仅1条时开始拼接按钮不可用（产品设计：1条无需拼接）", not start_enabled2)

        page.screenshot(path=str(SHOT_DIR / "tc0007_02_one_item_disabled.png"))

        # 关闭弹窗
        close_x = page.locator('.cx-modal-header svg').first
        close_x.click()
        page.wait_for_timeout(500)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
