# -*- coding: utf-8 -*-
"""
TC-0011: 图片/文生数字人-存入数字人形象库
流程：打开创建弹窗→历史tab→hover图片→点存入→填名字→保存
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


def test_tc0011():
    print("=" * 60, flush=True)
    print("TC-0011: 存入数字人形象库", flush=True)
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

        # 步骤1：打开数字人库→形象tab→创建形象弹窗
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
        shot(page, "tc0011_create_dialog.png")

        # 步骤2：点历史tab
        print("\n--- 步骤2：点历史tab ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) { if (e.innerText.trim() === '历史') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        shot(page, "tc0011_history.png")
        print("  ✅ 已切历史tab", flush=True)

        # 步骤3：hover成功图片（第二张，第一张是审核失败的）
        print("\n--- 步骤3：hover图片 ---", flush=True)
        images = page.locator("img")
        print(f"  找到图片数: {images.count()}", flush=True)
        if images.count() > 1:
            images.nth(1).hover(force=True)
            time.sleep(1)
            print("  ✅ 已hover第二张图片", flush=True)

        # 步骤4：点存入数字人形象库
        print("\n--- 步骤4：点存入按钮 ---", flush=True)
        save_btn = page.locator("[aria-label='存入数字人形象库']")
        if save_btn.count() > 0:
            save_btn.first.click(force=True)
            time.sleep(2)
            print("  ✅ 已点存入数字人形象库", flush=True)
            shot(page, "tc0011_save_dialog.png")
        else:
            errors.append("存入按钮未找到")

        # 步骤5：填名字保存
        print("\n--- 步骤5：填名字保存 ---", flush=True)
        name_input = page.locator("input[placeholder*='名字'], input[placeholder*='名称'], input[type='text']")
        if name_input.count() > 0:
            name_input.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("测试形象TC0011")
            time.sleep(0.5)
            print("  ✅ 已输入名字", flush=True)

            # 点保存
            page.evaluate("""() => {
                const els = document.querySelectorAll('button, div, span');
                for (const e of els) {
                    if (e.innerText.trim() === '保存') { e.click(); break; }
                }
            }""")
            time.sleep(2)
            print("  ✅ 已点保存", flush=True)
            shot(page, "tc0011_saved.png")
        else:
            errors.append("名字输入框未找到")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0011 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0011_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0011()
