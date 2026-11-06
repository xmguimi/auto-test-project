# -*- coding: utf-8 -*-
"""
TC-0011: 音频节点-播放控制
验证播放按钮、暂停、时间码同步更新。
"""
import os
import re
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

def get_time_texts(node):
    """从节点里提取所有mm:ss格式的时间字符串"""
    text = node.text_content()
    times = re.findall(r'\d{2}:\d{2}', text)
    return times

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.bring_to_front()
        page.wait_for_timeout(500)

        print("=== TC-0011: 音频节点-播放控制 ===")

        # 选中第一个节点
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        node = page.locator('.react-flow__node').first
        node.click()
        page.wait_for_timeout(800)
        print("选中第一个节点")

        # ---------- 步骤1: 验证播放按钮存在（限定在选中节点内） ----------
        print("\n[步骤1] 验证播放按钮存在...")
        play_btn = node.locator('button[title="播放"]').first
        check("播放按钮可见（title=播放）", play_btn.is_visible())

        # ---------- 步骤2: 验证时间码显示 ----------
        print("\n[步骤2] 验证时间码显示（当前时间+总时长）...")
        times_before = get_time_texts(node)
        print(f"  节点上的时间码: {times_before}")
        check("节点显示至少2个时间码（当前+总时长）", len(times_before) >= 2)

        # ---------- 步骤3: 点播放，验证时间码更新 ----------
        print("\n[步骤3] 点播放按钮，验证时间码同步更新...")
        play_btn.click()
        page.wait_for_timeout(2000)  # 等2秒播放

        times_after_play = get_time_texts(node)
        print(f"  播放2秒后的时间码: {times_after_play}")

        # 第一个时间是当前时间，应该从00:00变成00:02左右
        current_time_before = times_before[0] if times_before else "00:00"
        current_time_after = times_after_play[0] if times_after_play else "00:00"
        print(f"  当前时间: {current_time_before} → {current_time_after}")
        check("播放后当前时间码更新（从00:00变了）", current_time_after != current_time_before)

        # ---------- 步骤4: 点暂停 ----------
        print("\n[步骤4] 验证暂停按钮...")
        pause_btn = node.locator('button[title="暂停"]').first
        if pause_btn.is_visible():
            pause_btn.click()
            page.wait_for_timeout(1000)
            print("  点了暂停按钮")
            check("播放中出现暂停按钮并可点击", True)
        else:
            print("  没找到暂停按钮")
            check("播放中出现暂停按钮", False)

        # ---------- 步骤5: 进度条跳转验证 ----------
        print("\n[步骤5] 点击进度条中间位置，验证时间码跳转...")
        # 找节点里的进度条/波形区域（大概在播放按钮上方）
        node_box = node.bounding_box()
        if node_box:
            # 进度条大概在节点中间偏上的位置，点击水平中点
            click_x = node_box['x'] + node_box['width'] / 2
            click_y = node_box['y'] + node_box['height'] * 0.4  # 大概40%高度位置是波形区
            page.mouse.click(click_x, click_y)
            page.wait_for_timeout(1000)

            times_after_seek = get_time_texts(node)
            print(f"  点击进度条中间后的时间码: {times_after_seek}")
            current_time_seek = times_after_seek[0] if times_after_seek else "00:00"
            print(f"  当前时间: {current_time_after} → {current_time_seek}")
            check("点击进度条后时间码跳转到对应位置", current_time_seek != current_time_after)
        else:
            check("点击进度条后时间码跳转到对应位置", False)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
