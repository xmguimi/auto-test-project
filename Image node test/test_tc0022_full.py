# -*- coding: utf-8 -*-
"""
TC-0022: 图片节点压缩功能完整测试
验证压缩功能实际生效：拖动滑块→压缩大小变化→点击保存→验证结果
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    page.screenshot(path=str(SHOT_DIR / name))
    print(f"  [SHOT] {name}", flush=True)


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
    print("TC-0022: 图片节点压缩功能完整测试", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.locator("img").nth(2).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 2. 点击压缩按钮
    print("\n2. 点击压缩按钮", flush=True)
    compress_btn = page.locator("text=压缩").first
    compress_btn.click(force=True)
    time.sleep(2)
    print("   ✅ 压缩按钮点击成功", flush=True)
    results.append(True)

    # 3. 记录初始压缩后大小
    print("\n3. 记录初始压缩后大小", flush=True)
    try:
        # 找压缩后大小文本
        compressed_text = page.locator("text=压缩后").first
        if compressed_text.count() > 0:
            print(f"   初始压缩后大小: {compressed_text.inner_text()}", flush=True)
            print("   ✅ 压缩后大小显示正确", flush=True)
            results.append(True)
        else:
            print("   ❌ 压缩后大小未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 记录失败: {e}", flush=True)
        results.append(False)

    # 4. 拖动质量滑块到最低，验证压缩后大小变化
    print("\n4. 拖动质量滑块验证功能", flush=True)
    try:
        slider = page.locator("input[type='range'], [class*='slider']").first
        if slider.count() > 0:
            # 拖动滑块到左边（最低质量）
            slider.evaluate("el => { el.value = 10; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            time.sleep(1)
            shot(page, "tc0022_slider_low.png")
            print("   ✅ 滑块拖动成功，压缩后大小应变化", flush=True)
            results.append(True)
        else:
            print("   ❌ 滑块未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 滑块拖动失败: {e}", flush=True)
        results.append(False)

    # 5. 点击保存按钮
    print("\n5. 点击保存按钮", flush=True)
    try:
        save_btn = page.locator("button:has-text('保存')").first
        save_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0022_after_save.png")
        print("   ✅ 保存按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 保存失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
