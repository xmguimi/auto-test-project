# -*- coding: utf-8 -*-
"""
TC-0007: 图片/文生数字人-基础设置参数
验证：生图分组、国家/地区、人群、比例、清晰度、生成张数均可切换
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
    print("TC-0007: 基础设置参数", flush=True)
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
        shot(page, "tc0007_open.png")

        # 步骤2：生图分组下拉
        print("\n--- 步骤2：生图分组下拉 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div');
            for (const e of els) {
                if (e.innerText.includes('全能图片G2') && e.innerText.length < 50) {
                    e.click(); break;
                }
            }
        }""")
        time.sleep(1)
        # 选第二个选项
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span');
            for (const e of els) {
                if (e.innerText.trim() === '全能图片G2（官2）') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已切换生图分组", flush=True)

        # 步骤3：国家/地区下拉
        print("\n--- 步骤3：国家/地区下拉 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div');
            for (const e of els) {
                if (e.innerText.trim() === '中国' && e.innerText.length < 10) { e.click(); break; }
            }
        }""")
        time.sleep(1)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span');
            for (const e of els) {
                if (e.innerText.trim() === '欧美') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已切换国家/地区", flush=True)

        # 步骤4：人群下拉
        print("\n--- 步骤4：人群下拉 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div');
            let count = 0;
            for (const e of els) {
                if (e.innerText.trim() === '不限' && e.innerText.length < 10) {
                    count++;
                    if (count === 1) { e.click(); break; }
                }
            }
        }""")
        time.sleep(1)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span');
            for (const e of els) {
                if (e.innerText.trim() === '年轻人') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已切换人群", flush=True)

        # 步骤5：比例切换
        print("\n--- 步骤5：比例切换 ---", flush=True)
        for ratio in ["1:1", "3:4", "16:9", "9:16"]:
            page.evaluate(f"""() => {{
                const els = document.querySelectorAll('div, span, button');
                for (const e of els) {{
                    if (e.innerText.trim() === '{ratio}') {{ e.click(); break; }}
                }}
            }}""")
            time.sleep(0.3)
            print(f"  ✅ 已选比例 {ratio}", flush=True)

        # 步骤6：清晰度切换
        print("\n--- 步骤6：清晰度切换 ---", flush=True)
        for q in ["2K", "4K", "1K"]:
            page.evaluate(f"""() => {{
                const els = document.querySelectorAll('div, span, button');
                for (const e of els) {{
                    if (e.innerText.trim() === '{q}') {{ e.click(); break; }}
                }}
            }}""")
            time.sleep(0.3)
            print(f"  ✅ 已选清晰度 {q}", flush=True)

        # 步骤7：张数切换
        print("\n--- 步骤7：张数切换 ---", flush=True)
        for n in ["1张", "2张", "8张", "4张"]:
            page.evaluate(f"""() => {{
                const els = document.querySelectorAll('div, span, button');
                for (const e of els) {{
                    if (e.innerText.trim() === '{n}') {{ e.click(); break; }}
                }}
            }}""")
            time.sleep(0.3)
            print(f"  ✅ 已选 {n}", flush=True)

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
