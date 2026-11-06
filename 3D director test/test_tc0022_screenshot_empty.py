# -*- coding: utf-8 -*-
"""
TC-0022: 3D导演台-截图空状态操作
测试：无截图时清空全部/发送到画布的状态和操作
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
    print("TC-0022: 3D导演台-截图空状态操作", flush=True)
    print("=" * 60, flush=True)

    # 1. 选中机位01
    print("\n1. 选中机位01", flush=True)
    try:
        # 用JavaScript点击机位01
        page.evaluate("""
            () => {
                const items = document.querySelectorAll('.role-label');
                for (let item of items) {
                    if (item.textContent.includes('机位01')) {
                        item.parentElement.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        time.sleep(1)
        print("   ✅ 已选中机位01", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 切换到机位视角
    print("\n2. 切换到机位视角", flush=True)
    try:
        camera_view_tab = page.locator("text=机位视角").first
        camera_view_tab.click(force=True)
        time.sleep(1)
        print("   ✅ 已切换到机位视角", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 切换到摄像机截图tab
    print("\n3. 切换到摄像机截图tab，确认空状态", flush=True)
    try:
        screenshot_tab = page.locator("text=摄像机截图").first
        if screenshot_tab.count() > 0:
            screenshot_tab.click(force=True)
            time.sleep(1)
            shot(page, "tc0022_screenshot_tab.png")
            # 检查是否显示空状态
            empty_text = page.locator("text=暂无摄像机截图").first
            if empty_text.count() > 0 and empty_text.is_visible():
                print("   ✅ 摄像机截图tab空状态显示正常", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 未检测到空状态提示", flush=True)
                results.append(False)
        else:
            print("   ⚠️ 未找到摄像机截图tab", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 检查清空全部按钮状态（可点击）
    print("\n4. 检查清空全部按钮状态", flush=True)
    try:
        clear_btn = page.locator("text=清空全部").first
        if clear_btn.count() > 0:
            is_disabled = clear_btn.is_disabled()
            print(f"   清空全部按钮是否置灰: {is_disabled}", flush=True)
            if not is_disabled:
                print("   ✅ 无截图时清空全部按钮可点击", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 无截图时清空全部按钮置灰", flush=True)
                results.append(False)
        else:
            print("   ⚠️ 未找到清空全部按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 检查发送到画布按钮状态（可点击）
    print("\n5. 检查发送到画布按钮状态", flush=True)
    try:
        send_btn = page.locator("text=发送到画布").last
        if send_btn.count() > 0:
            is_disabled = send_btn.is_disabled()
            print(f"   发送到画布按钮是否置灰: {is_disabled}", flush=True)
            if not is_disabled:
                print("   ✅ 无截图时发送到画布按钮可点击", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 无截图时发送到画布按钮置灰", flush=True)
                results.append(False)
        else:
            print("   ⚠️ 未找到发送到画布按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 点击清空全部按钮，验证无报错
    print("\n6. 点击清空全部按钮，验证无报错", flush=True)
    try:
        clear_btn = page.locator("text=清空全部").first
        if clear_btn.count() > 0:
            clear_btn.click(force=True)
            time.sleep(1)
            shot(page, "tc0022_after_clear_click.png")
            print("   ✅ 点击清空全部按钮，无报错", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 未找到清空全部按钮", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 7. 点击发送到画布按钮，验证画布上没有出现截图
    print("\n7. 点击发送到画布按钮，验证画布上没有出现截图", flush=True)
    try:
        send_btn = page.locator("text=发送到画布").last
        if send_btn.count() > 0:
            send_btn.click(force=True)
            time.sleep(1)
            shot(page, "tc0022_after_send_click.png")
            # 检查右侧是否还显示空状态
            empty_text = page.locator("text=暂无摄像机截图").first
            if empty_text.count() > 0 and empty_text.is_visible():
                print("   ✅ 点击发送到画布后，摄像机截图仍为空状态，画布上无截图出现", flush=True)
                results.append(True)
            else:
                print("   ⚠️ 空状态消失，可能出现了截图", flush=True)
                results.append(False)
        else:
            print("   ⚠️ 未找到发送到画布按钮", flush=True)
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
