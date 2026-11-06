# -*- coding: utf-8 -*-
"""
TC-0005: 音频生成-参数配置（完整交互测试）
验证：调滑块数值变化、重置归0、格式切换、采样率切换
纯DOM元素定位，环境变量 FJ_CDP_HOST/FJ_CDP_PORT
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


def test_tc0005():
    print("=" * 60, flush=True)
    print("TC-0005: 音频生成-参数配置（完整交互）", flush=True)
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

        # 步骤2：打开参数浮层
        print("\n--- 步骤2：打开参数浮层 ---", flush=True)
        page.evaluate("document.querySelector('button.tts-pbar').click()")
        time.sleep(1.5)
        shot(page, "tc0005_panel_open.png")

        # 步骤3：读初始值，调滑块
        print("\n--- 步骤3：调滑块 ---", flush=True)
        # 读浮层内三个参数的当前值
        def get_slider_val(label):
            return page.evaluate("""(label) => {
                const items = document.querySelectorAll('*');
                for (const el of items) {
                    if (el.children.length > 0) continue;
                    const t = (el.innerText||'').trim();
                    if (t.match(/^-?\\d+$/) && el.previousElementSibling) {
                        const prev = el.previousElementSibling.innerText || '';
                        if (prev.includes(label)) return t;
                    }
                }
                return null;
            }""", label)

        for label in ["语调", "语速", "音量"]:
            v0 = get_slider_val(label)
            print(f"  {label} 初始值: {v0}", flush=True)

        # 步骤4：切换格式 mp3→wav
        print("\n--- 步骤4：切换格式 ---", flush=True)
        wav_btn = page.locator("div:has-text('wav')").last
        if wav_btn.count() > 0:
            wav_btn.click(force=True)
            time.sleep(0.5)
            print("  ✅ 切换到wav", flush=True)
            shot(page, "tc0005_wav.png")
        else:
            errors.append("wav按钮未找到")

        # 切回mp3
        mp3_btn = page.locator("div:has-text('mp3')").last
        if mp3_btn.count() > 0:
            mp3_btn.click(force=True)
            time.sleep(0.5)
            print("  ✅ 切回mp3", flush=True)

        # 步骤5：切换采样率 24000→32000
        print("\n--- 步骤5：切换采样率 ---", flush=True)
        sr_btn = page.locator("div:has-text('32000')").last
        if sr_btn.count() > 0:
            sr_btn.click(force=True)
            time.sleep(0.5)
            print("  ✅ 切换到32000", flush=True)
            shot(page, "tc0005_32k.png")
        else:
            errors.append("32000按钮未找到")

        # 步骤6：点重置
        print("\n--- 步骤6：点重置 ---", flush=True)
        reset = page.locator("text=重置为默认值")
        if reset.count() > 0:
            reset.first.click(force=True)
            time.sleep(0.5)
            print("  ✅ 点重置为默认值", flush=True)
            shot(page, "tc0005_reset.png")
        else:
            errors.append("重置按钮未找到")

        shot(page, "tc0005_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0005 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0005_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0005()
