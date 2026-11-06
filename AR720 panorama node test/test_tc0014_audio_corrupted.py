# -*- coding: utf-8 -*-
"""
TC-0014: 音频节点-损坏音频文件上传测试
补充验证：破损文件上传后，变速按钮置灰不可点
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
TEST_AUDIO = r"D:\Desktop\自动化测试\auto-test-project\testdata\损坏音频.mp3"

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

        page = None
        for pg in ctx.pages:
            if "帧境" in pg.title():
                page = pg
                break
        page.bring_to_front()
        page.wait_for_timeout(1000)

        print("=== TC-0014: 损坏音频上传后变速按钮状态验证 ===")

        # 选中最后一个音频节点（已上传破损音频的节点）
        nodes = page.locator('.react-flow__node')
        node = nodes.nth(nodes.count() - 1)
        node.click(force=True)
        time.sleep(1.5)

        # 找变速按钮
        node_btns = node.locator('button')
        speed_btn = None
        for j in range(node_btns.count()):
            btn = node_btns.nth(j)
            label = btn.get_attribute('aria-label') or ''
            text = btn.text_content() or ''
            if '变速' in label or '变速' in text:
                speed_btn = btn
                print(f"找到变速按钮: {label} / {text}")
                break

        check("变速按钮存在", speed_btn is not None)

        if speed_btn:
            is_disabled = speed_btn.is_disabled()
            print(f"变速按钮是否置灰: {is_disabled}")
            check("破损文件上传后变速按钮置灰不可点", is_disabled)

        page.screenshot(path=str(SHOT_DIR / "tc0014_01_speed_btn_state.png"))
        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
