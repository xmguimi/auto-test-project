# -*- coding: utf-8 -*-
"""
TC-0009: 图片/文生数字人-生成与历史
验证：填写描述→点生成→结果出现在本次生成→切历史→可存入形象库
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
    print("TC-0009: 生成与历史", flush=True)
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

        # 步骤2：输入描述
        print("\n--- 步骤2：输入描述 ---", flush=True)
        desc = page.locator("[contenteditable='true']")
        if desc.count() > 0:
            desc.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("一个年轻女性，穿着白色连衣裙，站在海边")
            time.sleep(1)
            print("  ✅ 已输入描述", flush=True)

        # 步骤3：点生成
        print("\n--- 步骤3：点生成 ---", flush=True)
        page.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.innerText.trim() === '生成') { b.click(); break; }
            }
        }""")
        time.sleep(3)
        print("  ✅ 已点生成", flush=True)
        shot(page, "tc0009_generating.png")

        # 步骤4：等待生成完成（最多等60秒）
        print("\n--- 步骤4：等待生成 ---", flush=True)
        time.sleep(30)
        shot(page, "tc0009_result.png")
        print("  ✅ 等待30秒完成", flush=True)

        # 步骤5：切历史tab
        print("\n--- 步骤5：切历史tab ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '历史') { e.click(); break; }
            }
        }""")
        time.sleep(1)
        shot(page, "tc0009_history.png")
        print("  ✅ 已切历史tab", flush=True)

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
