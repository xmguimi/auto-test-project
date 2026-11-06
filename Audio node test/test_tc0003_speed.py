# -*- coding: utf-8 -*-
"""
TC-0003: 音频节点-变速
验证音频节点工具栏【变速】功能正常：点击后出现变速工作台，可通过滑块或数值输入调整倍速（0.25x~4.0x），倍速与数值双向同步，点击【生成】能按所选倍速生成新音频节点；同时验证默认值、取消等处理。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 变速是本地处理，生成按钮旁无价格标注，不花钱
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

        print("=== TC-0003: 音频节点-变速 ===")

        # ---------- 步骤1: 选中原始音频节点，观察工具栏【变速】入口 ----------
        print("\n[步骤1] 选中音频节点，观察工具栏【变速】入口...")
        audio_node = page.locator('.react-flow__node:has-text("欢呼声.mp3")').first
        audio_node.click()
        page.wait_for_timeout(800)

        speed_btn = page.get_by_role("button", name="变速", exact=True)
        speed_visible = speed_btn.is_visible()
        check("选中音频节点后，工具栏【变速】入口正常显示", speed_visible)

        # ---------- 步骤2: 点击【变速】，观察工作台 ----------
        print("\n[步骤2] 点击【变速】，观察工作台出现...")
        speed_btn.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SHOT_DIR / "tc0003_03_workbench.png"))

        # 验证工作台元素：0.25x标签、4.0x标签、数值输入框、生成按钮
        min_label = page.get_by_text("0.25x")
        max_label = page.get_by_text("4.0x")
        # 数值输入框：class=iae-num
        speed_input = page.locator('input.iae-num')
        # 生成按钮：class=iae-generate-btn
        generate_btn = page.locator('.iae-generate-btn')

        check("变速工作台出现，可见最小值0.25x标签", min_label.is_visible())
        check("变速工作台出现，可见最大值4.0x标签", max_label.is_visible())
        check("变速工作台数值输入框可见", speed_input.is_visible())

        # ---------- 步骤3: 验证默认倍速 ----------
        print("\n[步骤3] 验证默认倍速值...")
        current_value = speed_input.input_value()
        print(f"  当前倍速值: {current_value}")
        # 注意：工作台会记住上次设置的倍速，所以默认值不一定是1.00
        check("倍速输入框有数值（默认或上次设置）", current_value.strip() != "")

        # 先重置为1.00，确保测试从干净状态开始
        speed_input.fill("")
        speed_input.fill("1.00")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)

        # ---------- 步骤4: 输入倍速2.00，观察生成按钮激活 ----------
        print("\n[步骤4] 输入倍速2.00，观察生成按钮状态...")
        speed_input.fill("")
        speed_input.fill("2.00")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)
        page.screenshot(path=str(SHOT_DIR / "tc0003_04_speed_2x.png"))

        # 验证生成按钮变为可用（不再是灰色disabled）
        generate_enabled = generate_btn.is_enabled()
        check("调整倍速后【生成】按钮变为可用", generate_enabled)

        # ---------- 步骤5: 取消测试：点×关闭 ----------
        print("\n[步骤5] 取消测试：点×关闭变速...")
        # 找关闭按钮（工作台最左边的×）
        close_area = page.locator('text=速').locator('xpath=ancestor::div[1]').locator('svg').first
        close_area.click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(SHOT_DIR / "tc0003_05_after_cancel.png"))

        # 验证工作台已关闭
        workbench_closed = not speed_input.is_visible()
        check("点×后变速工作台关闭", workbench_closed)

        # ---------- 步骤6: 重新打开变速，点生成 ----------
        print("\n[步骤6] 重新打开变速，点生成...")
        speed_btn.click()
        page.wait_for_timeout(800)

        # 重新获取输入框和生成按钮
        speed_input2 = page.locator('input.iae-num')
        speed_input2.fill("")
        speed_input2.fill("2.00")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)

        generate_btn2 = page.locator('.iae-generate-btn')

        if REAL_GENERATE:
            print("  REAL_GENERATE=True，点击生成按钮...")
            generate_btn2.click()
            page.wait_for_timeout(8000)  # 等待变速生成完成
            page.screenshot(path=str(SHOT_DIR / "tc0003_06_after_generate.png"))

            # 验证是否有生成成功提示
            success_tip = page.get_by_text("已生成")
            has_success = success_tip.count() > 0
            check("点生成后出现'已生成'提示", has_success)

            # 验证生成了新节点（画布上应该有3个节点：原始+截取+变速）
            all_audio_nodes = page.locator('.react-flow__node').filter(has_text="00:0")
            new_count = all_audio_nodes.count()
            check(f"变速生成成功，画布音频节点数增加（当前{new_count}个）", new_count >= 3)
        else:
            print("  REAL_GENERATE=False，跳过实际生成")
            check("生成按钮存在（不实际点击）", generate_btn2.is_visible())

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
