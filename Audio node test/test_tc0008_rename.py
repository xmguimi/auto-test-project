# -*- coding: utf-8 -*-
"""
TC-0008: 音频节点-重命名
验证音频节点支持重命名：点击工具栏【重命名】进入编辑态，输入新名称并确认后正确保存并更新显示。
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

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
    """找第一个视口内可见的节点并选中"""
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    all_nodes = page.locator('.react-flow__node')
    node_count = all_nodes.count()
    for i in range(node_count):
        node = all_nodes.nth(i)
        try:
            box = node.bounding_box()
            if box and box['x'] > 0 and box['y'] > 0:
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

        print("=== TC-0008: 音频节点-重命名 ===")

        # ---------- 步骤1: 选中节点，验证重命名按钮存在 ----------
        print("\n[步骤1] 选中节点，验证重命名按钮存在...")
        select_visible_audio_node(page)

        rename_btn = page.get_by_role("button", name="重命名")
        check("工具栏重命名按钮可见", rename_btn.is_visible())

        # ---------- 步骤2: 点重命名，输入新名称确认 ----------
        print("\n[步骤2] 点重命名，输入新名称回车确认...")
        rename_btn.click()
        page.wait_for_timeout(500)

        name_input = page.locator('input[placeholder="输入节点名称"]')
        check("点重命名后出现名称输入框", name_input.is_visible())

        original_name = name_input.input_value()
        print(f"  原名称: {original_name}")

        name_input.fill("测试音频A")
        page.wait_for_timeout(200)
        page.keyboard.press("Enter")
        page.wait_for_timeout(800)

        # 验证名称更新
        renamed_count = page.locator('.react-flow__node:has-text("测试音频A")').count()
        check("重命名后节点名称正确更新", renamed_count >= 1)
        page.screenshot(path=str(SHOT_DIR / "tc0008_01_renamed.png"))

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
