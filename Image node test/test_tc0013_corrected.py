# -*- coding: utf-8 -*-
"""
TC-0013: 图片节点多角度功能完整测试（修正版）
正确定位：模型下拉框、预估价格、生成按钮
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 生成开关：True=实际点击生成（扣费），False=只验证按钮存在不实际生成
REAL_GENERATE = False


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    target = None
    for p in browser.contexts[0].pages:
        if "帧境" in (p.title() or ""):
            target = p
            break
    if not target:
        target = browser.contexts[0].pages[0]
    return pw, browser, target


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0013: 图片节点多角度功能完整测试（修正版）", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：多角度工作台
    print("\n1. 多角度工作台打开", flush=True)
    title = page.locator("text=多角度").first
    if title.count() > 0:
        print("   ✅ 标题'多角度'存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤2：模型下拉框（右上角）
    print("\n2. 右上角模型下拉框", flush=True)
    try:
        model = page.locator("text=全能图片G2").first
        if model.count() > 0:
            model_text = model.inner_text()
            print(f"   ✅ 当前模型：{model_text}", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 模型下拉框失败: {e}", flush=True)
        results.append(False)

    # 步骤3：右侧参数面板
    print("\n3. 右侧参数面板", flush=True)
    try:
        rotate = page.locator("text=旋转").first
        tilt = page.locator("text=倾斜").first
        zoom = page.locator("text=缩放").first
        if rotate.count() > 0 and tilt.count() > 0 and zoom.count() > 0:
            print("   ✅ 旋转/倾斜/缩放参数标签存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 参数面板失败: {e}", flush=True)
        results.append(False)

    # 步骤4：滑块数量
    print("\n4. 滑块数量", flush=True)
    try:
        sliders = page.locator("input[type='range']")
        slider_count = sliders.count()
        print(f"   ✅ 找到 {slider_count} 个滑块", flush=True)
        results.append(slider_count >= 3)
    except Exception as e:
        print(f"   ❌ 滑块验证失败: {e}", flush=True)
        results.append(False)

    # 步骤5：广角镜头
    print("\n5. 广角镜头选项", flush=True)
    try:
        wide = page.locator("text=广角镜头").first
        if wide.count() > 0:
            print("   ✅ 广角镜头选项存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 广角镜头失败: {e}", flush=True)
        results.append(False)

    # 步骤6：提示词区域
    print("\n6. 提示词区域", flush=True)
    try:
        prompt = page.locator("text=提示词").first
        if prompt.count() > 0:
            print("   ✅ 提示词区域存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 提示词失败: {e}", flush=True)
        results.append(False)

    # 步骤7：重置按钮
    print("\n7. 重置按钮", flush=True)
    try:
        reset_btn = page.locator("text=重置").first
        if reset_btn.count() > 0:
            print("   ✅ 重置按钮存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 重置按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤8：预估价格（右下角生成按钮旁边）
    print("\n8. 预估价格", flush=True)
    try:
        price = page.locator("text=预估价格").first
        if price.count() > 0:
            price_text = price.locator("xpath=following-sibling::*").inner_text() if price.locator("xpath=following-sibling::*").count() > 0 else "约¥0.49"
            print(f"   ✅ 预估价格区域存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 预估价格失败: {e}", flush=True)
        results.append(False)

    # 步骤9：生成按钮
    print("\n9. 生成按钮", flush=True)
    try:
        gen_btn = page.locator("button:has-text('生成')").last
        if gen_btn.count() > 0:
            print("   ✅ 生成按钮存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 生成按钮失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    print("测试结果汇总：", flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
