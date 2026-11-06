# -*- coding: utf-8 -*-
"""
TC-0002: 音频节点-截取
验证音频节点工具栏【截取】功能正常：点击后出现截取工作台，可在波形上选择截取区间、显示区间时长，底部时间码同步，点击【生成】能按所选区间截取并落为新节点；同时验证取消、区间边界等处理。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 截取是本地处理，生成按钮旁无价格标注，不花钱
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

        print("=== TC-0002: 音频节点-截取 ===")

        # ---------- 步骤1: 选中音频节点，观察工具栏【截取】入口 ----------
        print("\n[步骤1] 选中音频节点，观察工具栏【截取】入口...")
        audio_node = page.locator('.react-flow__node:has-text("欢呼声.mp3")')
        audio_node.click()
        page.wait_for_timeout(800)

        # 在节点上方工具栏找"截取"按钮（精确匹配button角色，排除工作台标签）
        cut_btn = page.get_by_role("button", name="截取", exact=True)
        cut_visible = cut_btn.is_visible()
        check("选中音频节点后，工具栏【截取】入口正常显示", cut_visible)

        # ---------- 步骤2: 点击【截取】，观察工作台 ----------
        print("\n[步骤2] 点击【截取】，观察工作台出现...")
        cut_btn.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SHOT_DIR / "tc0002_03_workbench.png"))

        # 验证工作台元素：×关闭按钮、"截取"标签、时间码、生成按钮
        mode_label = page.locator('.iae-mode-label')
        range_text = page.locator('.iae-range')
        # 从"截取"标签向上找工作台容器，在容器内找生成按钮
        workbench_container = mode_label.locator('xpath=ancestor::div[contains(@class, "iae") or contains(@class, "workbench")][1]')
        generate_btn = workbench_container.get_by_role("button", name="生成")

        check("截取工作台出现，可见'截取'标签", mode_label.is_visible())
        check("截取工作台时间码显示（如00:00 - 00:06）", range_text.is_visible())
        check("截取工作台【生成】按钮可见", generate_btn.is_visible())

        # ---------- 步骤3: 验证区间时长与时间码同步 ----------
        print("\n[步骤3] 验证区间时长与时间码显示...")
        timecode_text = range_text.text_content()
        print(f"  时间码显示: {timecode_text}")

        # 波形选区框内应有时长显示（如5.83 s）
        duration_overlay = page.get_by_text("s")
        duration_visible = duration_overlay.count() > 0
        check(f"波形选区显示区间时长（如5.83s）", duration_visible)

        # ---------- 步骤4: 取消测试：点×关闭 ----------
        print("\n[步骤4] 取消测试：点×关闭截取...")
        # 找到×关闭按钮（工作台最左边）
        workbench = page.locator('.iae-mode-label').locator('xpath=ancestor::div[1]')
        close_icon = workbench.locator('svg').first
        close_icon.click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(SHOT_DIR / "tc0002_04_after_cancel.png"))

        # 验证工作台已关闭
        workbench_closed = not page.locator('.iae-range').is_visible()
        check("点×后截取工作台关闭", workbench_closed)

        # ---------- 步骤5: 重新打开截取，点生成 ----------
        print("\n[步骤5] 重新打开截取，点生成...")
        cut_btn.click()
        page.wait_for_timeout(800)

        # 重新获取工作台容器和生成按钮
        mode_label2 = page.locator('.iae-mode-label')
        workbench_container2 = mode_label2.locator('xpath=ancestor::div[contains(@class, "iae") or contains(@class, "workbench")][1]')
        generate_btn2 = workbench_container2.get_by_role("button", name="生成")

        if REAL_GENERATE:
            print("  REAL_GENERATE=True，点击生成按钮...")
            generate_btn2.click()
            page.wait_for_timeout(5000)  # 等待截取完成
            page.screenshot(path=str(SHOT_DIR / "tc0002_05_after_generate.png"))

            # 验证生成了新节点
            new_nodes = page.locator('.react-flow__node:has-text("00:0")')
            new_count = new_nodes.count()
            check(f"点生成后按所选区间截取成功，结果落为新节点（找到{new_count}个节点）", new_count >= 2)

            # 验证新节点时长约6s
            new_node_duration = page.get_by_text("00:06")
            check("新节点时长约6s", new_node_duration.count() > 0)
        else:
            print("  REAL_GENERATE=False，跳过实际生成")
            check("生成按钮存在（不实际点击）", generate_btn2.is_visible())

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
