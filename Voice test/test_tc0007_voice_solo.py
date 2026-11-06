# -*- coding: utf-8 -*-
"""
TC-0007: 语音合成-单人模式
验证：单人模式、音色选择、语言切换、参数滑块、示例文本填入
纯DOM元素定位
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


def test_tc0007():
    print("=" * 60, flush=True)
    print("TC-0007: 语音合成-单人模式", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200
    except Exception:
        print("[ERROR] CDP未就绪", flush=True); sys.exit(1)

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        time.sleep(2)

        # 步骤0：进入项目
        print("\n--- 步骤0：进入项目 ---", flush=True)
        project = page.locator("text=剪辑测试")
        if project.count() > 0:
            project.first.click(force=True)
            time.sleep(6)

        # 步骤1：进入语音合成
        print("\n--- 步骤1：进入语音合成 ---", flush=True)
        voice_btn = page.locator("button[aria-label='配音工具']")
        if voice_btn.count() > 0:
            voice_btn.first.click(force=True)
            time.sleep(1.5)
        nav = page.locator("nav.tts-nav button.tts-nav-item")
        for i in range(nav.count()):
            if "语音合成" in nav.nth(i).inner_text():
                nav.nth(i).click(force=True)
                break
        time.sleep(2)

        # 步骤2：切换单人模式
        print("\n--- 步骤2：切换单人模式 ---", flush=True)
        solo = page.locator("text=单人模式")
        if solo.count() > 0:
            solo.first.click(force=True)
            time.sleep(1)
            print("  ✅ 已切换单人模式", flush=True)
            shot(page, "tc0007_solo.png")
        else:
            errors.append("单人模式按钮未找到")

        # 步骤3：输入文本
        print("\n--- 步骤3：输入文本 ---", flush=True)
        editor = page.locator("[contenteditable='true']").first
        if editor.count() > 0:
            editor.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("你好，这是一段单人语音测试。")
            time.sleep(0.5)
            print("  ✅ 文本已输入", flush=True)
            shot(page, "tc0007_text.png")
        else:
            errors.append("文本输入区未找到")

        # 步骤4：验证音色
        print("\n--- 步骤4：音色配置 ---", flush=True)
        voice = page.locator("text=Vivi")
        if voice.count() > 0:
            print("  ✅ 音色 Vivi 可见", flush=True)
        else:
            errors.append("音色Vivi未找到")

        # 步骤5：语言下拉
        print("\n--- 步骤5：语言下拉 ---", flush=True)
        lang = page.locator("text=中文")
        if lang.count() > 0:
            print("  ✅ 语言'中文/默认'可见", flush=True)
        else:
            errors.append("语言下拉未找到")

        # 步骤6：参数滑块
        print("\n--- 步骤6：参数滑块 ---", flush=True)
        for label in ["音调", "语速", "音量"]:
            el = page.locator(f"text={label}")
            if el.count() > 0:
                print(f"  ✅ {label} 滑块可见", flush=True)
            else:
                errors.append(f"{label} 未找到")

        # 步骤7：点示例文本
        print("\n--- 步骤7：示例文本 ---", flush=True)
        example = page.locator("text=吵架")
        if example.count() > 0:
            example.first.click(force=True)
            time.sleep(0.5)
            print("  ✅ 已点击示例文本'吵架'", flush=True)
            shot(page, "tc0007_example.png")
        else:
            errors.append("示例文本'吵架'未找到")

        shot(page, "tc0007_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0007 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0007_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0007()
