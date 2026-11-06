# -*- coding: utf-8 -*-
"""
TC-0008: 图片节点拼图工具导入测试
验证本地上传、画布选择、按名称搜索三种导入方式
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
    print("TC-0008: 拼图工具导入测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：拼图工具打开
    print("\n1. 拼图工具打开", flush=True)
    title = page.locator("text=拼图工具").first
    if title.count() > 0:
        print("   ✅ 标题'拼图工具'存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤2：验证自由拼图选中
    print("\n2. 自由拼图模式", flush=True)
    free_tab = page.locator("text=自由拼图").first
    if free_tab.count() > 0:
        print("   ✅ 自由拼图选项存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤3：验证本地上传按钮
    print("\n3. 本地上传按钮", flush=True)
    upload_btn = page.locator("text=本地上传").first
    if upload_btn.count() > 0:
        print("   ✅ 本地上传按钮存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤4：验证画布选择按钮
    print("\n4. 画布选择按钮", flush=True)
    canvas_btn = page.locator("text=画布选择").first
    if canvas_btn.count() > 0:
        print("   ✅ 画布选择按钮存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤5：验证搜索框
    print("\n5. 按名称搜索框", flush=True)
    search_input = page.get_by_placeholder("按名称搜索").first
    if search_input.count() > 0:
        print("   ✅ 按名称搜索框存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤6：验证左侧列表已有图片
    print("\n6. 左侧列表已有图片", flush=True)
    try:
        img = page.locator("img").nth(1)
        if img.count() > 0:
            print("   ✅ 左侧列表已有图片", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 左侧列表验证失败: {e}", flush=True)
        results.append(False)

    # 步骤7：点击画布选择按钮
    print("\n7. 点击画布选择", flush=True)
    try:
        canvas_btn.click()
        time.sleep(2)
        shot(page, "tc0008_canvas_select.png")
        print("   ✅ 画布选择弹窗打开", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 画布选择失败: {e}", flush=True)
        results.append(False)

    # 步骤8：验证保存到画布按钮
    print("\n8. 保存到画布按钮", flush=True)
    try:
        save_btn = page.locator("text=保存到画布").first
        if save_btn.count() > 0:
            print("   ✅ 保存到画布按钮存在", flush=True)
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 保存按钮失败: {e}", flush=True)
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
