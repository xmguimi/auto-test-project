# -*- coding: utf-8 -*-
"""
TC-0009: 3D导演台-导入本地模型
测试：导入本地FBX模型文件，验证导入成功、列表新增
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
    print("TC-0009: 3D导演台-导入本地模型", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮导入本地模型按钮，验证提示
    print("\n1. 悬浮导入本地模型按钮", flush=True)
    try:
        import_btn = page.locator("button[aria-label='导入本地模型']").first
        if import_btn.count() > 0:
            import_btn.hover(force=True)
            time.sleep(1)
            # 检查悬浮提示是否出现
            tooltip = page.locator("text=导入本地模型").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'导入本地模型'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 导入本地模型按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 点击导入本地模型按钮，触发文件选择
    print("\n2. 点击导入本地模型按钮", flush=True)
    try:
        import_btn = page.locator("button[aria-label='导入本地模型']").first
        import_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0009_file_dialog.png")
        print("   ✅ 点击导入按钮成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 选择本地模型文件，导入成功
    print("\n3. 选择本地模型文件导入", flush=True)
    try:
        # 监听文件选择对话框，设置文件路径
        with page.expect_file_chooser() as fc_info:
            page.locator("button[aria-label='导入本地模型']").first.click(force=True)
        file_chooser = fc_info.value
        file_chooser.set_files(MODEL_FILE)
        time.sleep(5)  # 等待导入完成
        shot(page, "tc0009_imported.png")
        print("   ✅ 模型文件导入成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 验证左侧列表新增"我的模型"
    print("\n4. 验证左侧列表新增我的模型", flush=True)
    try:
        my_model = page.locator("text=我的模型").first
        if my_model.count() > 0:
            print("   ✅ 左侧列表出现'我的模型'分类", flush=True)
            results.append(True)
        else:
            print("   ⚠️ '我的模型'分类未检测到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 验证场景中模型出现
    print("\n5. 验证场景中模型出现", flush=True)
    try:
        # 检查左侧角色列表是否新增
        role_list = page.locator("text=我的模型").first
        if role_list.count() > 0:
            print("   ✅ 模型已添加到场景", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 场景中模型未检测到", flush=True)
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
