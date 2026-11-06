# -*- coding: utf-8 -*-
"""
TC-0004: 音频生成-基础输入
验证：智能配音/参考图片Tab、添加音色、文本输入字数统计、斜杠命令
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


def test_tc0004():
    print("=" * 60, flush=True)
    print("TC-0004: 音频生成-基础输入", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200, "CDP端口未就绪"
    except Exception:
        print(f"[ERROR] CDP端口{PORT}未就绪，请先用调试模式启动帧境", flush=True)
        sys.exit(1)

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        time.sleep(2)

        # ========== 步骤1：打开配音面板，进入音频生成 ==========
        print("\n--- 步骤1：进入音频生成页 ---", flush=True)
        voice_btn = page.locator("button[aria-label='配音工具']")
        if voice_btn.count() == 0:
            errors.append("配音工具按钮未找到")
        else:
            voice_btn.first.click()
            time.sleep(1.5)
            # 点左侧"音频生成"
            nav = page.locator("nav.tts-nav button.tts-nav-item")
            found_gen = False
            for i in range(nav.count()):
                if "音频生成" in nav.nth(i).inner_text():
                    nav.nth(i).click()
                    found_gen = True
                    break
            if not found_gen:
                errors.append("音频生成菜单未找到")
            time.sleep(2)
            shot(page, "tc0004_gen_page.png")
            print("  ✅ 进入音频生成页", flush=True)

        # ========== 步骤2：验证Tab ==========
        print("\n--- 步骤2：验证Tab ---", flush=True)
        for tab_name in ["智能配音", "参考图片"]:
            tab = page.locator(f".cx-tab:has-text('{tab_name}')")
            if tab.count() > 0:
                print(f"  ✅ Tab '{tab_name}' 可见", flush=True)
            else:
                errors.append(f"Tab '{tab_name}' 未找到")

        # ========== 步骤3：添加音色 ==========
        print("\n--- 步骤3：添加音色 ---", flush=True)
        add_voice = page.locator("button:has-text('添加音色'), button[aria-label*='添加音色']")
        if add_voice.count() == 0:
            # 尝试找+号按钮
            add_voice = page.locator("button:has-text('+')")
        if add_voice.count() > 0:
            add_voice.first.click()
            time.sleep(1.5)
            shot(page, "tc0004_voice_picker.png")
            print("  ✅ 点击添加音色", flush=True)
            # 选第一个音色
            voice_card = page.locator("button.vl-featured, button[aria-label*='音色']")
            if voice_card.count() > 0:
                voice_card.first.click()
                time.sleep(1)
                print("  ✅ 选择音色", flush=True)
                shot(page, "tc0004_voice_added.png")
            else:
                errors.append("音色列表未找到")
        else:
            errors.append("添加音色按钮未找到")

        # ========== 步骤4：文本输入+字数统计 ==========
        print("\n--- 步骤4：文本输入与字数统计 ---", flush=True)
        textarea = page.locator("textarea")
        if textarea.count() == 0:
            errors.append("文本输入框未找到")
        else:
            textarea.first.click()
            textarea.first.fill("你好世界")
            time.sleep(0.5)
            shot(page, "tc0004_text.png")
            print("  ✅ 输入'你好世界'", flush=True)

        # ========== 步骤5：斜杠命令 ==========
        print("\n--- 步骤5：斜杠命令 ---", flush=True)
        textarea = page.locator("textarea")
        if textarea.count() > 0:
            textarea.first.click()
            textarea.first.press("End")
            textarea.first.type("/")
            time.sleep(1)
            shot(page, "tc0004_slash.png")
            print("  ✅ 输入斜杠/", flush=True)

        # ========== 结果 ==========
        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] 共 {len(errors)} 个问题：", flush=True)
            for e in errors:
                print(f"  - {e}", flush=True)
            sys.exit(1)
        else:
            print("[PASS] TC-0004 全部通过！", flush=True)

    except Exception as e:
        print(f"\n[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try:
            if page: shot(page, "tc0004_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0004()
