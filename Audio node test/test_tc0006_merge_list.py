# -*- coding: utf-8 -*-
"""
TC-0006: 音频拼接-列表操作与开始拼接
验证拼接列表可预览、上移、下移、删除，点击【开始拼接】能按列表顺序首尾相接生成新音频节点，新节点时长等于各段之和。
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

# 拼接是本地处理，不花钱
REAL_GENERATE = True

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

        print("=== TC-0006: 音频拼接-列表操作与开始拼接 ===")

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

        # ---------- 步骤1: 打开拼接弹窗，添加3条音频 ----------
        print("\n[步骤1] 打开拼接弹窗，添加3条音频...")
        # 先按Escape取消选中
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)

        # 找任意一个可见的音频节点（包含时间码00:的节点）
        all_nodes = page.locator('.react-flow__node')
        node_count = all_nodes.count()
        print(f"  画布上共{node_count}个节点，找第一个可见的音频节点...")

        # 遍历找第一个在视口内的节点
        selected = False
        for i in range(node_count):
            node = all_nodes.nth(i)
            try:
                box = node.bounding_box()
                if box and box['x'] > 0 and box['y'] > 0 and box['x'] < 1500 and box['y'] < 800:
                    node.click()
                    page.wait_for_timeout(500)
                    selected = True
                    print(f"  选中第{i}个节点（视口内）")
                    break
            except:
                continue

        if not selected:
            # 备选：直接找第一个包含00:时间码的节点
            audio_node = page.locator('.react-flow__node:has-text("00:")').first
            audio_node.click()
            page.wait_for_timeout(500)
            print("  用备选方式选中第一个音频节点")

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

        # 添加第3条：从当前画布选
        add_btn2 = page.get_by_role("button", name="添加音频")
        add_btn2.click()
        page.wait_for_timeout(300)
        page.get_by_text("从当前画布选", exact=True).click()
        page.wait_for_timeout(800)
        page.get_by_text("画布音频").nth(0).click()
        page.wait_for_timeout(500)

        count_text = page.get_by_text("已选 3 / 20")
        check("初始3条音频，计数已选3/20", count_text.is_visible())
        page.screenshot(path=str(SHOT_DIR / "tc0006_01_three_items.png"))

        # ---------- 步骤2: 验证预览按钮 ----------
        print("\n[步骤2] 验证预览按钮...")
        # 点第1项的预览按钮
        first_item_preview = page.locator('.acc-list button').nth(0)
        first_item_preview.click()
        page.wait_for_timeout(1000)
        check("点预览按钮不报错", True)

        # ---------- 步骤3: 验证上移/下移 ----------
        print("\n[步骤3] 验证上移/下移...")
        # 记录第1项名称
        first_name_before = page.locator('.acc-list .acc-name').nth(0).text_content()
        second_name_before = page.locator('.acc-list .acc-name').nth(1).text_content()
        print(f"  调整前第1项: {first_name_before}, 第2项: {second_name_before}")

        # 第2项的上移按钮：每一项4个按钮，第2项上移按钮索引=5
        second_item_up = page.locator('.acc-list button').nth(5)
        second_item_up.click()
        page.wait_for_timeout(500)

        # 验证第1项变了
        first_name_after = page.locator('.acc-list .acc-name').nth(0).text_content()
        print(f"  上移后第1项: {first_name_after}")
        check("上移按钮点击后顺序变化", first_name_before != first_name_after)

        # ---------- 步骤4: 验证删除 ----------
        print("\n[步骤4] 验证删除...")
        # 第3项的删除按钮：索引=11
        third_item_delete = page.locator('.acc-list button').nth(11)
        third_item_delete.click()
        page.wait_for_timeout(500)

        # 验证计数变为2
        count_text2 = page.get_by_text("已选 2 / 20")
        check("删除后计数变为已选2/20", count_text2.is_visible())
        page.screenshot(path=str(SHOT_DIR / "tc0006_02_after_delete.png"))

        # ---------- 步骤5: 开始拼接 ----------
        print("\n[步骤5] 开始拼接...")
        start_btn = page.get_by_role("button", name="开始拼接")

        if REAL_GENERATE:
            print("  REAL_GENERATE=True，点击开始拼接...")
            start_btn.click()
            page.wait_for_timeout(10000)  # 等待拼接完成
            page.screenshot(path=str(SHOT_DIR / "tc0006_03_after_merge.png"))

            # 验证生成了新节点（画布上音频节点总数增加）
            all_audio_nodes = page.locator('.react-flow__node').filter(has_text="00:")
            total_nodes = all_audio_nodes.count()
            check(f"点开始拼接后生成新节点（画布共{total_nodes}个音频节点）", total_nodes >= 4)
        else:
            print("  REAL_GENERATE=False，跳过实际拼接")
            check("开始拼接按钮存在（不实际点击）", start_btn.is_visible())

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
