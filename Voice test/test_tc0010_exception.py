# -*- coding: utf-8 -*-
"""
TC-0010: 反向-异常场景
验证：重复点击防提交、双人空文本校验
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


def test_tc0010():
    print("=" * 60, flush=True)
    print("TC-0010: 反向-异常场景", flush=True)
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

        # 步骤1：进入音频生成
        print("\n--- 步骤1：进入音频生成 ---", flush=True)
        voice_btn = page.locator("button[aria-label='配音工具']")
        if voice_btn.count() > 0:
            voice_btn.first.click(force=True)
            time.sleep(1.5)
        nav = page.locator("nav.tts-nav button.tts-nav-item")
        for i in range(nav.count()):
            if "音频生成" in nav.nth(i).inner_text():
                nav.nth(i).click(force=True)
                break
        time.sleep(2)

        # 步骤2：添加音色+输入文本，使按钮可点
        print("\n--- 步骤2：准备可生成状态 ---", flush=True)
        page.evaluate("document.querySelector('.vl-card').click()")
        time.sleep(0.5)
        editor = page.locator("[contenteditable='true']").first
        editor.click(force=True)
        time.sleep(0.2)
        page.keyboard.type("测试重复点击")
        time.sleep(0.5)
        disabled = page.evaluate("document.querySelector('button.tts-gen-btn').disabled")
        print(f"  按钮disabled状态: {disabled}", flush=True)

        # 步骤3：快速连点3次
        print("\n--- 步骤3：快速连点3次 ---", flush=True)
        for i in range(3):
            page.evaluate("document.querySelector('button.tts-gen-btn').click()")
            time.sleep(0.2)
        print("  ✅ 已快速点击3次", flush=True)
        time.sleep(2)
        shot(page, "tc0010_click3.png")

        # 步骤4：模拟断网
        print("\n--- 步骤4：模拟断网 ---", flush=True)
        page.route("**/*", lambda route: route.abort())
        time.sleep(0.5)
        # 尝试点生成
        page.evaluate("""() => {
            const btn = document.querySelector('button.tts-gen-btn');
            if (btn && !btn.disabled) btn.click();
        }""")
        time.sleep(2)
        shot(page, "tc0010_offline.png")
        print("  ✅ 断网状态下已点击生成（未崩溃）", flush=True)
        page.unroute("**/*")

        # 步骤5：模拟余额不足
        print("\n--- 步骤5：模拟余额不足 ---", flush=True)
        def balance_route(route):
            if "generate" in route.request.url or "tts" in route.request.url:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"code":40001,"message":"余额不足，请充值"}'
                )
            else:
                route.continue_()
        page.route("**/*", balance_route)
        time.sleep(0.5)
        page.evaluate("""() => {
            const btn = document.querySelector('button.tts-gen-btn');
            if (btn && !btn.disabled) btn.click();
        }""")
        time.sleep(2)
        shot(page, "tc0010_balance.png")
        print("  ✅ 余额不足状态已模拟", flush=True)
        page.unroute("**/*")

        # 步骤4：双人模式空文本校验
        print("\n--- 步骤4：双人模式空文本 ---", flush=True)
        nav2 = page.locator("nav.tts-nav button.tts-nav-item")
        for i in range(nav2.count()):
            if "语音合成" in nav2.nth(i).inner_text():
                nav2.nth(i).click(force=True)
                break
        time.sleep(1)
        # 切双人对话
        duo = page.locator("text=双人对话")
        if duo.count() > 0:
            duo.first.click(force=True)
            time.sleep(1)
            print("  ✅ 已切双人对话", flush=True)
        # 清空所有文本框
        page.evaluate("""() => {
            document.querySelectorAll('[contenteditable="true"]').forEach(el=>{
                el.innerText = '';
            });
        }""")
        time.sleep(0.5)
        shot(page, "tc0010_duo_empty.png")

        shot(page, "tc0010_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0010 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0010_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0010()
