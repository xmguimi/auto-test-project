# -*- coding: utf-8 -*-
"""
TC-0004: 音频拼接-弹窗与初始列表
验证点击【拼接】后弹窗正常打开，标题、说明、计数、列表、按钮等元素显示正确，初始列表默认含当前音频节点。
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

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0004: 音频拼接-弹窗与初始列表 ===")

        # 先按Escape关闭可能存在的弹窗
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)

        # ---------- 步骤1: 选中音频节点，点击【拼接】 ----------
        print("\n[步骤1] 选中音频节点，点击工具栏【拼接】...")
        audio_node = page.locator('.react-flow__node:has-text("欢呼声.mp3")').first
        audio_node.click()
        page.wait_for_timeout(500)

        merge_btn = page.get_by_role("button", name="拼接", exact=True)
        merge_btn.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SHOT_DIR / "tc0004_02_dialog_open.png"))

        # ---------- 步骤2: 验证弹窗标题、说明、计数 ----------
        print("\n[步骤2] 验证弹窗标题、说明、计数...")
        title = page.locator('.cx-modal-title')
        description = page.get_by_text("按列表顺序首尾相接")
        count_text = page.get_by_text("已选 1 / 20")

        check("弹窗标题显示「拼接音频」", "拼接音频" in title.text_content())
        check("弹窗说明文字正确", description.is_visible())
        check("计数显示「已选 1 / 20」", count_text.is_visible())

        # ---------- 步骤3: 验证列表项 ----------
        print("\n[步骤3] 验证列表默认含当前音频节点...")
        list_container = page.locator('.acc-list')
        check("列表容器存在", list_container.is_visible())

        # 列表项内：序号、名称、时长、来源
        index_text = page.locator('.acc-index')
        name_text = page.locator('.acc-name')
        duration_text = page.locator('.acc-list .acc-meta').first

        check("列表项序号为1", index_text.text_content().strip() == "1")
        check("列表项名称为「欢呼声.mp3」", "欢呼声.mp3" in name_text.text_content())
        check("列表项时长显示0:17", "0:17" in duration_text.text_content())

        # 来源标签（在列表容器内找）
        source_text = page.locator('.acc-list .acc-meta', has_text="画布")
        check("列表项来源标签为「画布」", source_text.is_visible())

        # 操作按钮：预览、上移、下移、删除
        preview_btn = page.locator('.acc-list button').nth(0)
        up_btn = page.locator('.acc-list button').nth(1)
        down_btn = page.locator('.acc-list button').nth(2)
        delete_btn = page.locator('.acc-list button').nth(3)

        check("列表项预览按钮可见", preview_btn.is_visible())
        check("列表项上移按钮可见", up_btn.is_visible())
        check("列表项下移按钮可见", down_btn.is_visible())
        check("列表项删除按钮可见", delete_btn.is_visible())

        # ---------- 步骤4: 验证底部按钮 ----------
        print("\n[步骤4] 验证底部按钮...")
        add_audio_btn = page.get_by_role("button", name="添加音频")
        cancel_btn = page.get_by_role("button", name="取消")
        start_btn = page.get_by_role("button", name="开始拼接")

        check("底部【添加音频】按钮可见", add_audio_btn.is_visible())
        check("底部【取消】按钮可见", cancel_btn.is_visible())
        check("底部【开始拼接】按钮可见", start_btn.is_visible())

        # ---------- 步骤5: 关闭弹窗 ----------
        print("\n[步骤5] 关闭弹窗...")
        cancel_btn.click()
        page.wait_for_timeout(500)

        dialog_closed = not title.is_visible()
        check("点取消后弹窗关闭", dialog_closed)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
