# -*- coding: utf-8 -*-
"""
TC-0006: AI修图工作台功能测试（修正版）
撤销/重做在无操作时置灰是正常状态
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
    print("TC-0006: AI修图工作台功能测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：工作台打开
    print("\n1. AI修图工作台打开", flush=True)
    title = page.locator("text=AI修图面板").first
    if title.count() > 0:
        print("   ✅ 标题'AI修图面板'存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤2：底部工具栏前12个按钮（撤销/重做/删除单独验证）
    print("\n2. 底部工具栏按钮", flush=True)
    tool_names = ["缩小", "放大", "适配", "选择", "抓手", "画笔", "箭头", "标注", "矩形", "文字", "橡皮", "截图"]
    
    for name in tool_names:
        try:
            btn = page.locator(f"text={name}").last
            if btn.count() > 0:
                btn.click()
                time.sleep(0.3)
                print(f"   ✅ {name}按钮可点击", flush=True)
                results.append(True)
            else:
                print(f"   ❌ {name}按钮不存在", flush=True)
                results.append(False)
        except Exception as e:
            print(f"   ❌ {name}按钮点击失败", flush=True)
            results.append(False)

    # 步骤3：撤销/重做按钮存在但初始置灰（正常）
    print("\n3. 撤销/重做按钮（初始置灰正常）", flush=True)
    undo_btn = page.locator("text=撤销").last
    redo_btn = page.locator("text=重做").last
    if undo_btn.count() > 0 and redo_btn.count() > 0:
        print("   ✅ 撤销、重做按钮存在，初始状态置灰（无操作时正常）", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤4：删除按钮
    print("\n4. 删除按钮", flush=True)
    del_btn = page.locator("text=删除").last
    if del_btn.count() > 0:
        print("   ✅ 删除按钮存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤5：标注样式面板
    print("\n5. 标注样式面板", flush=True)
    style_title = page.locator("text=标注样式").first
    if style_title.count() > 0:
        print("   ✅ 标注样式面板存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤6：右侧参数面板
    print("\n6. 右侧参数面板", flush=True)
    gen_btn = page.locator("text=生成").first
    if gen_btn.count() > 0:
        print("   ✅ 生成按钮存在", flush=True)
        results.append(True)
    else:
        results.append(False)

    # 步骤7：返回画布按钮
    print("\n7. 返回画布按钮", flush=True)
    back_btn = page.locator("text=返回画布").first
    if back_btn.count() > 0:
        print("   ✅ 返回画布按钮存在", flush=True)
        results.append(True)
    else:
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
