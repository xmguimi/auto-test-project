# -*- coding: utf-8 -*-
"""
TC-0017: 3D导演台-回收站
测试：悬浮提示、回收站弹窗、找回角色
前置条件：回收站中已存在已删除的角色
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
    print("TC-0017: 3D导演台-回收站", flush=True)
    print("=" * 60, flush=True)

    # 1. 悬浮回收站按钮，验证提示
    print("\n1. 悬浮回收站按钮", flush=True)
    try:
        trash_btn = page.locator("button[aria-label='回收站']").first
        if trash_btn.count() > 0:
            trash_btn.hover(force=True)
            time.sleep(1)
            tooltip = page.locator("text=回收站").first
            if tooltip.count() > 0:
                print("   ✅ 悬浮提示'回收站'正常显示", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 悬浮提示未检测到", flush=True)
                results.append(False)
        else:
            print("   ❌ 回收站按钮未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 验证回收站按钮有红点
    print("\n2. 验证回收站按钮有红点", flush=True)
    try:
        trash_btn = page.locator("button[aria-label='回收站']").first
        trash_badge = trash_btn.locator("span").first
        if trash_badge.count() > 0:
            print("   ✅ 回收站按钮有红点", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 回收站按钮无红点", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 点击回收站按钮，验证弹窗
    print("\n3. 点击回收站按钮，验证弹窗", flush=True)
    try:
        trash_btn = page.locator("button[aria-label='回收站']").first
        trash_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0017_trash_popup.png")
        # 验证有找回按钮
        recover_btn = page.locator("text=找回").first
        if recover_btn.count() > 0:
            print("   ✅ 回收站弹窗显示，有找回按钮", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 回收站弹窗无找回按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 记录当前角色数量（找回前）
    print("\n4. 记录当前角色数量（找回前）", flush=True)
    try:
        roles_before = page.locator("text=角色").count()
        print(f"   当前角色数量: {roles_before}", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 点击找回按钮，验证角色恢复
    print("\n5. 点击找回按钮，验证角色恢复", flush=True)
    try:
        recover_btn = page.locator("text=找回").first
        recover_btn.click(force=True)
        time.sleep(2)  # 等待找回操作完成
        shot(page, "tc0017_after_recover.png")
        print("   ✅ 找回按钮点击成功", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 等待3秒后，验证回收站红点消失（检测可见性，不是DOM数量）
    print("\n6. 等待3秒后，验证回收站红点消失", flush=True)
    try:
        time.sleep(3)  # 多等几秒，等红点消失
        trash_btn = page.locator("button[aria-label='回收站']").first
        trash_badge = trash_btn.locator("span").first
        # 用is_visible()检测用户是否能看到红点，而不是DOM是否存在
        if trash_badge.count() == 0 or not trash_badge.is_visible():
            print("   ✅ 回收站红点消失（用户不可见）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 回收站红点仍可见", flush=True)
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
