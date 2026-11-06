# -*- coding: utf-8 -*-
"""
TC-0015: 音频节点-超大音频上传边界测试
补充测试：变速滑块滑动后，生成按钮是否置灰
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

        print("=== TC-0015: 变速滑块滑动后生成按钮状态 ===")

        # 选中最后一个音频节点
        nodes = page.locator('.react-flow__node')
        node = nodes.nth(nodes.count() - 1)
        node.click(force=True)
        time.sleep(1.5)

        # 点变速按钮
        node_btns = node.locator('button')
        speed_btn = None
        for j in range(node_btns.count()):
            btn = node_btns.nth(j)
            label = btn.get_attribute('aria-label') or ''
            text = btn.text_content() or ''
            if '变速' in label or '变速' in text:
                speed_btn = btn
                break

        if speed_btn:
            speed_btn.click(force=True)
            time.sleep(1.5)
            print("变速弹窗打开")

            # 找生成按钮
            gen_btn = None
            btns = page.locator('button')
            for j in range(btns.count()):
                btn = btns.nth(j)
                if btn.is_visible():
                    text = btn.text_content() or ''
                    if '生成' in text:
                        gen_btn = btn
                        print(f"找到生成按钮: {text}")
                        break

            if gen_btn:
                is_disabled = gen_btn.is_disabled()
                print(f"未滑动滑块时生成按钮置灰: {is_disabled}")
                check("初始状态生成按钮置灰", is_disabled)

                # 滑动滑块（点一下滑块位置）
                slider = page.locator('input[type="range"]').first
                if slider.is_visible():
                    slider.click(position={"x": 50, "y": 5})
                    time.sleep(0.5)
                    print("已滑动滑块")

                    # 再检查生成按钮
                    gen_btn2 = None
                    btns = page.locator('button')
                    for j in range(btns.count()):
                        btn = btns.nth(j)
                        if btn.is_visible():
                            text = btn.text_content() or ''
                            if '生成' in text:
                                gen_btn2 = btn
                                break

                    if gen_btn2:
                        still_disabled = gen_btn2.is_disabled()
                        print(f"滑动滑块后生成按钮仍置灰: {still_disabled}")
                        check("滑动滑块后生成按钮仍置灰", still_disabled)

        page.screenshot(path=str(SHOT_DIR / "tc0015_04_speed_gen_btn.png"))
        browser.close()

        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
