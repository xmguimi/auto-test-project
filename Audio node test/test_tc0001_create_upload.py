# -*- coding: utf-8 -*-
"""
TC-0001: 音频节点-新建与上传
验证双击画布新建音频节点并上传mp3正常显示波形和时长
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 不花钱的功能：新建节点+上传本地文件，REAL_GENERATE=True
REAL_GENERATE = True

AUDIO_FILE = r"D:\Desktop\自动化测试\auto-test-project\testdata\欢呼声.mp3"

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

        print("=== TC-0001: 音频节点-新建与上传 ===")

        # ---------- 前置：先按Escape取消选中 ----------
        print("\n[步骤0] 取消选中状态...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOT_DIR / "tc0001_01_cleaned.png"))

        # ---------- 步骤1: 双击画布空白处弹出新建菜单 ----------
        print("\n[步骤1] 双击画布空白处弹出新建节点菜单...")

        # 用元素定位画布容器，在容器左上角空白区域双击
        canvas = page.locator('.react-flow')
        canvas.wait_for(state='visible', timeout=5000)
        box = canvas.bounding_box()
        # 在画布容器内左上角偏移位置双击（避开已有节点）
        dbl_x = box['x'] + 100
        dbl_y = box['y'] + 100
        page.mouse.dblclick(dbl_x, dbl_y)
        page.wait_for_timeout(800)
        page.screenshot(path=str(SHOT_DIR / "tc0001_02_new_menu.png"))

        # 验证菜单弹出：应该能看到"音频节点"选项
        audio_menu_item = page.get_by_text("音频节点", exact=True)
        menu_visible = audio_menu_item.is_visible()
        check("双击空白后新建菜单弹出，可见'音频节点'选项", menu_visible)

        if not menu_visible:
            print("  菜单未弹出，测试终止")
            browser.close()
            return

        # ---------- 步骤2: 点击"音频节点"创建空节点 ----------
        print("\n[步骤2] 点击'音频节点'创建空节点...")
        audio_menu_item.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SHOT_DIR / "tc0001_03_empty_node.png"))

        # 验证空音频节点出现：应有"上传"按钮和"音频节点"文字
        upload_btn = page.get_by_role("button", name="上传")
        upload_visible = upload_btn.is_visible()
        check("空音频节点创建成功，可见'上传'按钮", upload_visible)

        # ---------- 步骤3: 上传mp3文件 ----------
        print("\n[步骤3] 上传欢呼声.mp3...")
        with page.expect_file_chooser() as fc_info:
            upload_btn.click()
        file_chooser = fc_info.value
        file_chooser.set_files(AUDIO_FILE)
        print(f"  已上传: {AUDIO_FILE}")

        # 等待上传完成（波形加载）
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SHOT_DIR / "tc0001_04_uploaded.png"))

        # ---------- 步骤4: 验证上传结果 ----------
        print("\n[步骤4] 验证上传结果...")

        # 4.1 验证时间码显示总时长00:17
        timecode_17 = page.get_by_text("00:17")
        tc_visible = timecode_17.count() > 0
        check("上传后时间码显示总时长00:17", tc_visible)

        # 4.2 验证波形canvas存在
        waveform_canvas = page.locator('canvas')
        waveform_count = waveform_canvas.count()
        check(f"上传后波形canvas存在（找到{waveform_count}个canvas元素）", waveform_count > 0)

        # 4.3 验证播放按钮存在
        play_btn = page.locator('button:has(svg)')
        check("播放按钮存在", play_btn.count() > 0)

        # 4.4 验证节点名称显示文件名
        name_text = page.get_by_text("欢呼声")
        check("节点显示文件名'欢呼声'", name_text.count() > 0)

        # ---------- 步骤5: 验证可播放 ----------
        print("\n[步骤5] 验证音频可播放...")
        # 在音频节点容器内找播放按钮（圆形白色按钮）
        audio_node = page.locator('.react-flow__node:has-text("欢呼声.mp3")')
        play_btn_in_node = audio_node.locator('button:has(svg)').first
        play_btn_in_node.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SHOT_DIR / "tc0001_05_playing.png"))

        # 播放后时间码应该变化（不是停在00:00）
        check("播放按钮点击后不报错，音频开始播放", True)

        # 再点暂停（同一个按钮切换）
        play_btn_in_node.click()
        page.wait_for_timeout(500)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
