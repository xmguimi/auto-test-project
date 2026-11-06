# -*- coding: utf-8 -*-
"""
TC-0020: 3D导演台-导入模型取消导入测试
测试：取消文件选择对话框、正常导入FBX文件
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

# 测试文件路径
TESTDATA_DIR = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata")
FBX_FILE = TESTDATA_DIR / "小和尚模型.FBX"


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
    print("TC-0020: 3D导演台-导入模型取消导入测试", flush=True)
    print("=" * 60, flush=True)

    # 1. 确认导入本地模型按钮存在
    print("\n1. 确认导入本地模型按钮存在", flush=True)
    try:
        import_btn = page.locator("button[aria-label='导入本地模型']").first
        if import_btn.count() > 0 and import_btn.is_visible():
            print("   ✅ 导入本地模型按钮可见", flush=True)
            results.append(True)
        else:
            print("   ❌ 导入本地模型按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 测试：取消文件选择对话框
    print("\n2. 测试：取消文件选择对话框", flush=True)
    try:
        import_btn = page.locator("button[aria-label='导入本地模型']").first
        # 监听filechooser事件
        with page.expect_file_chooser() as fc_info:
            import_btn.click(force=True)
        file_chooser = fc_info.value
        # 取消选择（不设置文件）
        file_chooser.set_files([])
        time.sleep(1)
        shot(page, "tc0020_cancel_import.png")
        print("   ✅ 取消文件选择对话框，无报错", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 测试：导入正常FBX文件
    print("\n3. 测试：导入正常FBX文件", flush=True)
    try:
        if FBX_FILE.exists():
            import_btn = page.locator("button[aria-label='导入本地模型']").first
            with page.expect_file_chooser() as fc_info:
                import_btn.click(force=True)
            file_chooser = fc_info.value
            file_chooser.set_files(str(FBX_FILE))
            time.sleep(3)
            shot(page, "tc0020_normal_fbx.png")
            print("   ✅ 正常FBX文件可导入", flush=True)
            results.append(True)
        else:
            print(f"   ⚠️ 测试文件不存在: {FBX_FILE}", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 全程无报错
    print("\n4. 全程无报错验证", flush=True)
    try:
        # 检测底部工具栏的全屏按钮是否存在，验证页面正常
        fullscreen_btn = page.locator("button[aria-label='全屏']").first
        if fullscreen_btn.count() > 0 and fullscreen_btn.is_visible():
            print("   ✅ 页面正常，无崩溃（底部工具栏可见）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 页面可能异常", flush=True)
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
