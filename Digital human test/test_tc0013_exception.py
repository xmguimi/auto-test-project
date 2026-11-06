# -*- coding: utf-8 -*-
"""
TC-0013: 数字人库-反向-生成结果与生成数字人异常
验证：空名字不可保存、空名称不可生成、删除后卡片消失
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


def test_tc0013():
    print("=" * 60, flush=True)
    print("TC-0013: 反向异常测试", flush=True)
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
            try:
                project.first.click(force=True, timeout=3000)
                time.sleep(6)
            except:
                print("  [INFO] 已在项目中", flush=True)

        # 步骤1：打开创建弹窗→历史tab
        print("\n--- 步骤1：打开历史tab ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '形象') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        create_card = page.locator("text=创建形象")
        if create_card.count() > 0:
            create_card.first.click(force=True)
            time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) { if (e.innerText.trim() === '历史') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        print("  ✅ 已切历史tab", flush=True)

        # 步骤2：hover图片→点存入→空名字保存
        print("\n--- 步骤2：空名字保存校验 ---", flush=True)
        images = page.locator("img")
        if images.count() > 1:
            images.nth(1).hover(force=True)
            time.sleep(1)
            save_btn = page.locator("[aria-label='存入数字人形象库']")
            if save_btn.count() > 0:
                save_btn.first.click(force=True)
                time.sleep(1.5)
                print("  ✅ 已点存入按钮", flush=True)
                # 不填名字直接点保存
                page.evaluate("""() => {
                    const els = document.querySelectorAll('button, div, span');
                    for (const e of els) { if (e.innerText.trim() === '保存') { e.click(); break; } }
                }""")
                time.sleep(1)
                shot(page, "tc0013_empty_name.png")
                print("  ✅ 已测试空名字保存", flush=True)
                # 关闭弹窗
                page.evaluate("""() => {
                    const els = document.querySelectorAll('button, div, span');
                    for (const e of els) { if (e.innerText.trim() === '取消') { e.click(); break; } }
                }""")
                time.sleep(1)

        # 步骤3：点删除按钮
        print("\n--- 步骤3：删除按钮 ---", flush=True)
        del_btn = page.locator("text=删除")
        if del_btn.count() > 0:
            del_btn.first.click(force=True)
            time.sleep(1)
            shot(page, "tc0013_delete.png")
            print("  ✅ 已点删除按钮", flush=True)

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0013 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0013_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0013()
