# -*- coding: utf-8 -*-
"""
TC-0016: AR720节点-生成AR720全景-弹窗与参数编辑
REAL_GENERATE=False（不真实生成）
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

REAL_GENERATE = False

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

        print("=== TC-0016: AR720节点-生成AR720全景-弹窗与参数编辑 ===")

        # ---------- 步骤1: 打开弹窗 ----------
        print("\n[步骤1] 打开生成AR720弹窗...")
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        nodes = page.locator('.react-flow__node')
        for i in range(nodes.count()):
            node = nodes.nth(i)
            box = node.bounding_box()
            if box and box['x'] > 100 and box['y'] > 100:
                text = node.text_content()
                if "AR720" in text and "已生成" in text:
                    node.click()
                    page.wait_for_timeout(1000)
                    break

        gen_btn = page.locator('button[aria-label*="生成 AR720"]').first
        check("生成AR720全景按钮存在", gen_btn.is_visible())
        gen_btn.click()
        page.wait_for_timeout(2000)

        dialog = page.locator('[role="dialog"]').first
        check("弹窗正常打开", dialog.is_visible())

        # ---------- 步骤2: 验证弹窗内容 ----------
        print("\n[步骤2] 验证弹窗内容...")
        text = dialog.text_content()
        check("标题包含生成AR720全景", "生成 AR720 全景" in text)
        check("有描述输入提示", "输入适合环视空间的提示词" in text)
        check("有垫图引导", "垫图引导" in text)
        check("有生成通道", "生成通道" in text)
        check("比例16:9存在", "16:9" in text)
        check("比例21:9存在", "21:9" in text)
        check("场景自动存在", "自动" in text)
        check("场景室内存在", "室内" in text)
        check("场景室外存在", "室外" in text)
        check("有完整提示词展开", "查看提交生成的完整提示词" in text)

        # ---------- 步骤3: 验证未输入时按钮禁用 ----------
        print("\n[步骤3] 验证未输入描述时按钮状态...")
        submit_btn = dialog.locator('button:has-text("生成 AR720 全景")').last
        check("未输入描述时生成按钮禁用", not submit_btn.is_enabled())

        # ---------- 步骤4: 验证输入框 ----------
        print("\n[步骤4] 验证描述输入框...")
        desc_input = dialog.locator('textarea, [contenteditable="true"]').first
        check("描述输入框存在", desc_input.is_visible())
        if desc_input.is_visible():
            desc_input.fill("一个开阔的城市广场，四周有高楼和街道")
            check("输入描述文本成功", True)
            page.wait_for_timeout(500)

        # ---------- 步骤5: 验证输入后按钮可用 ----------
        print("\n[步骤5] 验证输入后按钮状态...")
        check("输入描述后生成按钮可用", submit_btn.is_enabled())

        # ---------- 步骤6: 验证比例和场景可点选 ----------
        print("\n[步骤6] 验证比例和场景可点选...")
        ratio_219 = dialog.locator('button:has-text("21:9")').first
        ratio_219.click()
        check("点21:9比例成功", True)

        scene_indoor = dialog.locator('button:has-text("室内")').first
        scene_indoor.click()
        check("点室内场景成功", True)

        page.screenshot(path=str(SHOT_DIR / "tc0016_01_dialog.png"))

        # 关闭弹窗
        page.keyboard.press('Escape')
        page.wait_for_timeout(1000)

        browser.close()

        # ---------- 结果汇总 ----------
        print(f"\n=== 测试结果: {passed} PASS / {failed} FAIL ===")

if __name__ == "__main__":
    main()
