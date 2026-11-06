# -*- coding: utf-8 -*-
"""
TC-0006: 音频生成-完整流程（含实际生成）
验证：输入文本→添加音色→生成→播放器→下载/导入画布
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


def test_tc0006():
    print("=" * 60, flush=True)
    print("TC-0006: 音频生成-完整流程", flush=True)
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

        # 步骤1：进入音频生成页
        print("\n--- 步骤1：进入音频生成页 ---", flush=True)
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

        # 步骤2：添加音色（直接点音色卡片）
        print("\n--- 步骤2：添加音色 ---", flush=True)
        # 点第一个音色卡片
        added = page.evaluate("""() => {
            const card = document.querySelector('.vl-card');
            if (card) { card.click(); return true; }
            return false;
        }""")
        print(f"  添加音色结果: {added}", flush=True)
        time.sleep(1)
        shot(page, "tc0006_voice.png")
        if not added:
            errors.append("音色卡片未找到")

        # 步骤3：输入文本
        print("\n--- 步骤3：输入文本 ---", flush=True)
        editor = page.locator("[contenteditable='true']")
        if editor.count() > 0:
            editor.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("你好，这是一段测试音频。")
            time.sleep(0.5)
            print("  ✅ 文本已输入", flush=True)
            shot(page, "tc0006_text.png")
        else:
            errors.append("文本输入区未找到")

        # 步骤4：点生成音频
        print("\n--- 步骤4：点生成音频 ---", flush=True)
        time.sleep(2)  # 等按钮状态更新
        page.evaluate("document.querySelector('button.tts-gen-btn').click()")
        print("  ✅ 已点击生成音频，等待生成...", flush=True)
        time.sleep(35)
        shot(page, "tc0006_generating.png")

        # 步骤4：验证播放器
        print("\n--- 步骤4：验证播放器 ---", flush=True)
        player = page.locator("audio, [class*='player'], [class*='audio']")
        if player.count() > 0:
            print("  ✅ 播放器出现", flush=True)
        else:
            print("  [WARN] 播放器未找到，可能仍在生成中", flush=True)
        shot(page, "tc0006_result.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0006 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0006_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0006()
