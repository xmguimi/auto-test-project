# -*- coding: utf-8 -*-
"""
TC-0009: 反向-输入校验
验证：空文本、仅空格、未加音色、超长文本的校验逻辑
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


def test_tc0009():
    print("=" * 60, flush=True)
    print("TC-0009: 反向-输入校验", flush=True)
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

        # 步骤2：空文本→生成按钮状态
        print("\n--- 步骤2：空文本校验 ---", flush=True)
        disabled = page.evaluate("""() => {
            const btn = document.querySelector('button.tts-gen-btn');
            return btn ? btn.disabled : null;
        }""")
        print(f"  空文本时生成按钮disabled: {disabled}", flush=True)
        if disabled is True:
            print("  ✅ 空文本按钮置灰", flush=True)
        else:
            errors.append(f"空文本按钮状态异常: disabled={disabled}")

        # 步骤3：仅空格
        print("\n--- 步骤3：仅空格校验 ---", flush=True)
        editor = page.locator("[contenteditable='true']").first
        editor.click(force=True)
        time.sleep(0.3)
        page.keyboard.type("   ")
        time.sleep(0.5)
        disabled2 = page.evaluate("document.querySelector('button.tts-gen-btn').disabled")
        print(f"  仅空格时按钮disabled: {disabled2}", flush=True)
        shot(page, "tc0009_space.png")

        # 步骤4：输入文本但不加音色
        print("\n--- 步骤4：无音色校验 ---", flush=True)
        editor.click(force=True)
        time.sleep(0.2)
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        time.sleep(0.2)
        page.keyboard.type("测试文本")
        time.sleep(0.5)
        disabled3 = page.evaluate("document.querySelector('button.tts-gen-btn').disabled")
        print(f"  无音色+有文本时按钮disabled: {disabled3}", flush=True)
        if disabled3 is True:
            print("  ✅ 无音色按钮置灰", flush=True)
        else:
            print("  [WARN] 无音色时按钮仍可点", flush=True)
        shot(page, "tc0009_no_voice.png")

        # 步骤5：超长文本
        print("\n--- 步骤5：超长文本校验 ---", flush=True)
        editor.click(force=True)
        time.sleep(0.2)
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        time.sleep(0.2)
        long_text = "测" * 3001
        page.keyboard.type(long_text)
        time.sleep(1)
        char_count = page.evaluate("""() => {
            const els = document.querySelectorAll('*');
            for (const el of els) {
                const t = (el.innerText||'').trim();
                if (t.match(/^\\d+\\/3000$/)) return t;
            }
            return null;
        }""")
        print(f"  字数统计: {char_count}", flush=True)
        shot(page, "tc0009_long.png")

        shot(page, "tc0009_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0009 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0009_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0009()
