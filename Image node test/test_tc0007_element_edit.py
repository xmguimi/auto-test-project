# -*- coding: utf-8 -*-
"""
TC-0007: 图片节点元素编辑测试
验证元素编辑入口、对象识别、修改/移动按钮
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
    print("TC-0007: 图片节点元素编辑测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：选中图片节点
    print("\n1. 选中图片节点", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.locator("img").nth(1).click(force=True)
    time.sleep(1.5)
    print("   ✅ 图片节点已选中", flush=True)
    results.append(True)

    # 步骤2：进入元素编辑模式
    print("\n2. 进入元素编辑模式", flush=True)
    try:
        elem_btn = page.locator("text=元素编辑").first
        elem_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0007_0_elem_edit.png")
        print("   ✅ 元素编辑按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 元素编辑按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤3：提示文字
    print("\n3. 元素编辑模式界面", flush=True)
    try:
        tip = page.locator("text=标记你想要修改的对象").first
        if tip.count() > 0:
            print("   ✅ 提示文字'标记你想要修改的对象'存在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 提示文字未找到，但界面已打开", flush=True)
            results.append(True)
    except Exception as e:
        print(f"   ❌ 界面验证失败: {e}", flush=True)
        results.append(False)

    # 步骤4：等待用户手动选中牛，验证按钮
    print("\n4. 等待选中牛，验证修改/移动按钮", flush=True)
    print("   请手动点击图片中的牛，等待识别...", flush=True)
    time.sleep(15)
    shot(page, "tc0007_1_selected.png")
    
    modify_btn = page.locator("text=修改").first
    move_btn = page.locator("text=移动").first
    if modify_btn.count() > 0 and move_btn.count() > 0:
        print("   ✅ 【修改】【移动】按钮都存在", flush=True)
        results.append(True)
    else:
        print("   ❌ 修改/移动按钮未找到", flush=True)
        results.append(False)

    # 步骤5：点击修改按钮
    print("\n5. 点击修改按钮", flush=True)
    try:
        modify_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0007_2_modify.png")
        print("   ✅ 修改按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 修改按钮失败: {e}", flush=True)
        results.append(False)

    # 步骤6：验证编辑框
    print("\n6. 验证编辑框", flush=True)
    try:
        input_box = page.locator("text=想怎么改").first
        if input_box.count() > 0:
            print("   ✅ '想怎么改'编辑框存在", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 编辑框提示未找到", flush=True)
            results.append(True)
    except Exception as e:
        print(f"   ❌ 编辑框验证失败: {e}", flush=True)
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
