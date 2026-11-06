# -*- coding: utf-8 -*-
"""
TC-0008: 语音合成-双人对话模式
验证：双文本框、音色1/音色2独立配置、添加轮次
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


def test_tc0008():
    print("=" * 60, flush=True)
    print("TC-0008: 语音合成-双人对话模式", flush=True)
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

        # 步骤2：切换双人对话
        print("\n--- 步骤2：切换双人对话 ---", flush=True)
        duo = page.locator("text=双人对话")
        if duo.count() > 0:
            duo.first.click(force=True)
            time.sleep(1)
            print("  ✅ 已切换双人对话", flush=True)
            shot(page, "tc0008_duo.png")
        else:
            errors.append("双人对话按钮未找到")

        # 步骤3：验证两个文本框
        print("\n--- 步骤3：双文本框 ---", flush=True)
        editors = page.locator("[contenteditable='true']")
        count = editors.count()
        print(f"  文本框数量: {count}", flush=True)
        if count >= 2:
            print("  ✅ 双文本框存在", flush=True)
        else:
            errors.append(f"文本框数量不足: {count}")

        # 步骤4：输入双方文本
        print("\n--- 步骤4：输入双方文本 ---", flush=True)
        editors.first.click(force=True)
        time.sleep(0.3)
        page.keyboard.type("你好呀，今天天气真不错。")
        time.sleep(0.3)
        page.evaluate("document.querySelectorAll('[contenteditable=\"true\"]')[1].click()")
        time.sleep(0.3)
        page.keyboard.type("是呀，我们一起出去玩吧。")
        time.sleep(0.5)
        print("  ✅ 双方文本已输入", flush=True)
        shot(page, "tc0008_text.png")

        # 步骤5：验证音色1/音色2
        print("\n--- 步骤5：音色1/音色2 ---", flush=True)
        v1 = page.locator("text=Vivi")
        v2 = page.locator("text=魅力女友")
        if v1.count() > 0:
            print("  ✅ 音色1 Vivi 可见", flush=True)
        else:
            errors.append("音色1 Vivi未找到")
        if v2.count() > 0:
            print("  ✅ 音色2 魅力女友 可见", flush=True)
        else:
            errors.append("音色2 魅力女友未找到")

        # 步骤6：添加一轮对话
        print("\n--- 步骤6：添加一轮对话 ---", flush=True)
        add_round = page.locator("text=添加一轮对话")
        if add_round.count() > 0:
            add_round.first.click(force=True)
            time.sleep(0.5)
            new_count = page.locator("[contenteditable='true']").count()
            print(f"  ✅ 添加后文本框数量: {new_count}", flush=True)
            shot(page, "tc0008_round.png")
        else:
            errors.append("添加一轮对话按钮未找到")

        shot(page, "tc0008_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0008 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0008_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0008()
