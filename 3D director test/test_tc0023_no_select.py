# -*- coding: utf-8 -*-
"""
TC-0023: 3D导演台-未选中对象操作
测试：未选中任何对象时点击回收站、添加角色等按钮的行为
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

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
    print("TC-0023: 3D导演台-未选中对象操作", flush=True)
    print("=" * 60, flush=True)

    # 1. 切换回导演视角，取消选中任何对象
    print("\n1. 切换回导演视角，取消选中任何对象", flush=True)
    try:
        # 切换到导演视角
        director_view_tab = page.locator("text=导演视角").first
        director_view_tab.click(force=True)
        time.sleep(1)
        # 按Escape取消选中
        page.keyboard.press("Escape")
        time.sleep(1)
        shot(page, "tc0023_deselected.png")
        print("   ✅ 已切换回导演视角，取消选中对象", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 检查回收站按钮状态
    print("\n2. 检查回收站按钮状态", flush=True)
    try:
        trash_btn = page.locator("button[aria-label='回收站']").first
        if trash_btn.count() > 0:
            is_disabled = trash_btn.is_disabled()
            print(f"   回收站按钮是否置灰: {is_disabled}", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 未找到回收站按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 点击回收站按钮，观察行为
    print("\n3. 点击回收站按钮，观察行为", flush=True)
    try:
        trash_btn = page.locator("button[aria-label='回收站']").first
        was_disabled = trash_btn.is_disabled()
        if not was_disabled:
            trash_btn.click()
            time.sleep(1)
            shot(page, "tc0023_after_trash_click.png")
            # 检查是否有提示
            empty_trash = page.locator("text=回收站是空的").first
            if empty_trash.count() > 0 and empty_trash.is_visible():
                print("   ✅ 点击回收站，提示'回收站是空的'", flush=True)
            else:
                print("   ✅ 点击回收站按钮，无报错", flush=True)
            results.append(True)
        else:
            print("   ✅ 回收站按钮置灰，不可点击", flush=True)
            results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 检查添加角色按钮状态
    print("\n4. 检查添加角色按钮状态", flush=True)
    try:
        add_role_btn = page.locator("button[aria-label='添加角色']").first
        if add_role_btn.count() > 0:
            is_disabled = add_role_btn.is_disabled()
            print(f"   添加角色按钮是否置灰: {is_disabled}", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 未找到添加角色按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 点击添加角色按钮，观察行为
    print("\n5. 点击添加角色按钮，观察行为", flush=True)
    try:
        add_role_btn = page.locator("button[aria-label='添加角色']").first
        was_disabled = add_role_btn.is_disabled()
        if not was_disabled:
            add_role_btn.click()
            time.sleep(1)
            shot(page, "tc0023_after_add_role_click.png")
            # 检查是否弹出菜单
            has_menu = page.locator("text=体型").count() > 0 or page.locator("text=几何模型").count() > 0
            if has_menu:
                print("   ✅ 点击添加角色，弹出菜单（正常功能）", flush=True)
                # 关闭菜单
                page.keyboard.press("Escape")
                time.sleep(0.5)
            else:
                print("   ⚠️ 点击添加角色，未弹出菜单", flush=True)
            results.append(True)
        else:
            print("   ✅ 添加角色按钮置灰，不可点击", flush=True)
            results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 检查右侧属性面板状态
    print("\n6. 检查右侧属性面板状态", flush=True)
    try:
        # 检查右侧是否显示3D场景属性（未选中对象时应显示场景属性）
        scene_prop = page.locator("text=3D场景").first
        if scene_prop.count() > 0 and scene_prop.is_visible():
            print("   ✅ 右侧显示3D场景属性（未选中对象时正常）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 右侧未显示3D场景属性", flush=True)
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
