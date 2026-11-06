# -*- coding: utf-8 -*-
"""
TC-0021: AR720全景节点-信息面板内容与操作
1. 复制按钮：点后按钮变"已复制"，粘贴验证
2. 重新生成：点后画布新增节点
3. 一键复用：点后中控台出现提示词
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

def find_info_btn(page):
    btns = page.locator('button')
    for i in range(btns.count()):
        btn = btns.nth(i)
        label = btn.get_attribute('aria-label') or ''
        if btn.is_visible() and '节点信息' in label:
            return btn
    return None

def open_info_panel(page):
    """打开信息面板"""
    page.keyboard.press('Escape')
    time.sleep(0.3)
    # 选中节点
    nodes = page.locator('.react-flow__node')
    for i in range(nodes.count()):
        node = nodes.nth(i)
        box = node.bounding_box()
        if box and box['x'] > 100 and box['y'] > 100:
            node.click()
            time.sleep(0.5)
            break
    # 点信息按钮
    info_btn = find_info_btn(page)
    if info_btn:
        info_btn.click(force=True)
        time.sleep(1)
        return True
    return False

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0021: AR720全景节点-信息面板内容与操作 ===")

        # ---------- 1. 测试复制按钮 ----------
        print("\n[1/3] 测试复制按钮...")
        if open_info_panel(page):
            # 找复制按钮
            copy_btn = page.locator('button:has-text("复制")').last
            check("复制按钮存在", copy_btn.is_visible())
            if copy_btn.is_visible():
                copy_text_before = copy_btn.text_content()
                print(f"  点击前按钮文字: {copy_text_before}")
                copy_btn.click(force=True)
                time.sleep(0.5)
                copy_text_after = copy_btn.text_content()
                print(f"  点击后按钮文字: {copy_text_after}")
                check("点复制后按钮变为已复制", "已复制" in copy_text_after)

        # ---------- 2. 测试重新生成按钮 ----------
        print("\n[2/3] 测试重新生成按钮...")
        if open_info_panel(page):
            nodes_before = page.locator('.react-flow__node').count()
            print(f"  重新生成前节点数: {nodes_before}")
            regen_btn = page.locator('button:has-text("重新生成")').last
            check("重新生成按钮存在", regen_btn.is_visible())
            if regen_btn.is_visible():
                regen_btn.click(force=True)
                time.sleep(2)
                nodes_after = page.locator('.react-flow__node').count()
                print(f"  重新生成后节点数: {nodes_after}")
                check("重新生成后画布新增节点", nodes_after > nodes_before)

        # ---------- 3. 测试一键复用按钮 ----------
        print("\n[3/3] 测试一键复用按钮...")
        if open_info_panel(page):
            # 中控台输入框
            input_box = page.locator('[contenteditable="true"]').last
            input_before = input_box.text_content() if input_box.is_visible() else ""
            print(f"  一键复用前输入框内容: {input_before[:50]}")

            reuse_btn = page.locator('button:has-text("一键复用")').last
            check("一键复用按钮存在", reuse_btn.is_visible())
            if reuse_btn.is_visible():
                reuse_btn.click(force=True)
                time.sleep(1)
                input_after = input_box.text_content() if input_box.is_visible() else ""
                print(f"  一键复用后输入框内容: {input_after[:50]}")
                check("一键复用后中控台出现提示词", len(input_after) > len(input_before))

        page.screenshot(path=str(SHOT_DIR / "tc0021_01_panel_buttons.png"))

        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
