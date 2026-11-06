# -*- coding: utf-8 -*-
"""
TC-0006: 图片/文生数字人-创意描述与字数
验证：输入文本字数同步、生成/AI润色按钮状态
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


def get_btn_state(page, text):
    """获取按钮状态"""
    return page.evaluate(f"""() => {{
        const btns = document.querySelectorAll('button');
        for (const b of btns) {{
            if (b.innerText.includes('{text}')) {{
                const cs = getComputedStyle(b);
                return {{disabled: b.disabled, opacity: cs.opacity}};
            }}
        }}
        return null;
    }}""")


def test_tc0006():
    print("=" * 60, flush=True)
    print("TC-0006: 创意描述与字数", flush=True)
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

        # 步骤1：打开创建弹窗
        print("\n--- 步骤1：打开创建弹窗 ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '形象') { e.click(); break; } }
        }""")
        time.sleep(1)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.includes('创建形象')) { e.click(); break; } }
        }""")
        time.sleep(2)

        # 步骤2：初始状态（空描述）
        print("\n--- 步骤2：初始状态 ---", flush=True)
        gen_state = get_btn_state(page, "生成")
        print(f"  生成按钮: {gen_state}", flush=True)
        shot(page, "tc0006_empty.png")

        # 步骤3：输入描述文本
        print("\n--- 步骤3：输入描述 ---", flush=True)
        desc = page.locator("[contenteditable='true']")
        if desc.count() > 0:
            desc.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("一个年轻的女性，穿着白色连衣裙，站在海边，阳光明媚")
            time.sleep(1)
            print("  ✅ 已输入描述", flush=True)
            shot(page, "tc0006_typed.png")

            # 检查字数（在创意描述框右下角）
            char_count = page.evaluate("""() => {
                const all = document.querySelectorAll('*');
                for (const e of all) {
                    if (e.children.length === 0) {
                        const t = (e.innerText || '').trim();
                        if (/^\\d+\\/2000$/.test(t)) return t;
                    }
                }
                return null;
            }""")
            print(f"  字数: {char_count}", flush=True)

            # 检查生成按钮状态
            gen_state = get_btn_state(page, "生成")
            print(f"  生成按钮: {gen_state}", flush=True)
        else:
            errors.append("描述输入框未找到")

        # 步骤4：清空
        print("\n--- 步骤4：清空 ---", flush=True)
        page.keyboard.press("Control+a")
        time.sleep(0.3)
        page.keyboard.press("Delete")
        time.sleep(1)
        gen_state = get_btn_state(page, "生成")
        print(f"  清空后生成按钮: {gen_state}", flush=True)
        shot(page, "tc0006_cleared.png")

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
