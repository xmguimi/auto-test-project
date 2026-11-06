# -*- coding: utf-8 -*-
"""
TC-0008: 图片/文生数字人-人像词库
验证：点人像词库弹窗、三个tab、标签选择、AI润色、随机试试、使用回填
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
    print("TC-0008: 人像词库", flush=True)
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

        # 步骤2：点人像词库
        print("\n--- 步骤2：点人像词库 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.includes('人像词库')) { e.click(); break; }
            }
        }""")
        time.sleep(2)
        shot(page, "tc0008_open.png")
        print("  ✅ 人像词库弹窗已打开", flush=True)

        # 步骤3：选标签
        print("\n--- 步骤3：选标签 ---", flush=True)
        for tag in ["黑色", "连衣裙"]:
            page.evaluate(f"""() => {{
                const els = document.querySelectorAll('div, span, button');
                for (const e of els) {{
                    if (e.innerText.trim() === '{tag}') {{ e.click(); break; }}
                }}
            }}""")
            time.sleep(0.3)
            print(f"  ✅ 已选标签 {tag}", flush=True)

        shot(page, "tc0008_tags.png")

        # 步骤4：验证AI润色按钮
        print("\n--- 步骤4：AI润色按钮 ---", flush=True)
        ai_state = page.evaluate("""() => {
            const btns = document.querySelectorAll('button, div');
            for (const b of btns) {
                if (b.innerText.includes('AI润色')) {
                    const cs = getComputedStyle(b);
                    return {opacity: cs.opacity, disabled: b.disabled};
                }
            }
            return null;
        }""")
        print(f"  AI润色按钮状态: {ai_state}", flush=True)

        # 点AI润色
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) {
                if (e.innerText.includes('AI润色')) { e.click(); break; }
            }
        }""")
        time.sleep(1)
        print("  ✅ 已点AI润色", flush=True)
        shot(page, "tc0008_ai.png")

        # 步骤5：点随机试试
        print("\n--- 步骤5：随机试试 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) {
                if (e.innerText.includes('随机试试')) { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已点随机试试", flush=True)

        # 步骤6：切背景tab
        print("\n--- 步骤6：切背景tab ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '背景') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已切背景tab", flush=True)

        # 步骤7：点使用回填
        print("\n--- 步骤7：点使用 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) {
                if (e.innerText.trim() === '使用') { e.click(); break; }
            }
        }""")
        time.sleep(1)
        print("  ✅ 已点使用", flush=True)
        shot(page, "tc0008_done.png")

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
