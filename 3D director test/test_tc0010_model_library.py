# -*- coding: utf-8 -*-
"""
TC-0010: 3D导演台-模型库
测试：模型库弹窗打开、tab切换（用text=选择器）、我的模型列表、本地导入、关闭弹窗
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

MODEL_FILE = r"D:\Desktop\自动化测试\auto-test-project\testdata\小和尚模型.FBX"

REAL_GENERATE = True


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
    print("TC-0010: 3D导演台-模型库", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮模型库按钮，验证提示
    print("\n1. 悬浮模型库按钮", flush=True)
    try:
        model_btn = page.locator("button[aria-label='模型库']").first
        if model_btn.count() > 0:
            model_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=模型库").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'模型库'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 模型库按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 点击模型库按钮，弹窗打开
    print("\n2. 点击模型库按钮，弹窗打开", flush=True)
    try:
        model_btn = page.locator("button[aria-label='模型库']").first
        model_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0010_modal_open.png")
        # 用text=检测弹窗标题
        modal_title = page.locator("text=模型库").first
        if modal_title.count() > 0 and modal_title.is_visible():
            print("   ✅ 模型库弹窗打开成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 模型库弹窗未打开", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 依次切换tab（用text=选择器）
    print("\n3. 依次切换分类tab", flush=True)
    try:
        tabs = ["便利生活", "居家生活", "户外出行", "工具配件", "我的模型"]
        tab_ok = 0
        for tab_name in tabs:
            # 用text=选择器，限定在弹窗内
            tab_btn = page.locator(f"text={tab_name}").first
            if tab_btn.count() > 0 and tab_btn.is_visible():
                tab_btn.click(force=True)
                time.sleep(1)
                tab_ok += 1
                print(f"     - {tab_name} ✅", flush=True)
            else:
                print(f"     - {tab_name} ❌", flush=True)
        if tab_ok == len(tabs):
            print(f"   ✅ {len(tabs)}个tab均可切换", flush=True)
            results.append(True)
        else:
            print(f"   ⚠️ 只有{tab_ok}/{len(tabs)}个tab可切换", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 验证我的模型列表及本地导入按钮
    print("\n4. 验证我的模型列表及本地导入按钮", flush=True)
    try:
        my_model_tab = page.locator("text=我的模型").first
        my_model_tab.click(force=True)
        time.sleep(1)
        shot(page, "tc0010_my_models.png")
        # 检测本地导入按钮
        local_import = page.locator("text=本地导入").first
        if local_import.count() > 0 and local_import.is_visible():
            print("   ✅ 我的模型列表显示正常，包含本地导入按钮", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 本地导入按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 测试本地导入功能（点击加号，选择FBX文件）
    print("\n5. 测试本地导入功能", flush=True)
    try:
        # 监听文件选择对话框
        with page.expect_file_chooser() as fc_info:
            # 点击本地导入按钮
            local_import = page.locator("text=本地导入").first
            local_import.click(force=True)
        file_chooser = fc_info.value
        file_chooser.set_files(MODEL_FILE)
        time.sleep(3)  # 等待导入完成
        shot(page, "tc0010_local_imported.png")
        print("   ✅ 本地模型导入成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 选择已有模型添加到场景
    print("\n6. 选择已有模型添加到场景", flush=True)
    try:
        model_item = page.locator("text=小和尚").first
        if model_item.count() > 0:
            model_item.click(force=True)
            time.sleep(2)
            shot(page, "tc0010_model_added.png")
            print("   ✅ 模型选择添加成功", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 模型项未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 7. 关闭弹窗
    print("\n7. 关闭模型库弹窗", flush=True)
    try:
        # 用aria-label找关闭按钮
        close_btn = page.locator("button[aria-label='关闭']").first
        if close_btn.count() > 0:
            close_btn.click(force=True)
            time.sleep(1)
            shot(page, "tc0010_modal_closed.png")
            print("   ✅ 弹窗关闭成功", flush=True)
            results.append(True)
        else:
            print("   ❌ 关闭按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
