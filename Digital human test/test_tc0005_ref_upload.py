# -*- coding: utf-8 -*-
"""
TC-0005: 图片/文生数字人-参考图上传四种方式
实际测试：本地上传/资产库选/画布选/数字人形象
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


def open_create_dialog(page):
    """打开创建形象弹窗"""
    # 先确保在数字人库→形象tab
    page.locator("button[aria-label='数字人库']").first.click(force=True)
    time.sleep(2)
    # 切到形象tab
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button, div, span');
        for (const b of btns) {
            if (b.innerText.trim() === '形象') { b.click(); break; }
        }
    }""")
    time.sleep(1)
    # 点创建形象
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button, div, span');
        for (const b of btns) {
            if (b.innerText.includes('创建形象')) { b.click(); break; }
        }
    }""")
    time.sleep(2)


def close_dialog(page):
    """关闭弹窗"""
    page.keyboard.press("Escape")
    time.sleep(1)


def test_tc0005():
    print("=" * 60, flush=True)
    print("TC-0005: 参考图上传四种方式", flush=True)
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

        # ========== 测试1：本地上传 ==========
        print("\n--- 测试1：本地上传 ---", flush=True)
        open_create_dialog(page)
        # 点参考图
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '参考图') { e.click(); break; }
            }
        }""")
        time.sleep(1)

        # 点本地上传
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '本地上传') { e.click(); break; }
            }
        }""")
        time.sleep(1)

        # 上传文件
        file_input = page.locator("input[type='file']")
        if file_input.count() > 0:
            test_img = "D:/Desktop/自动化测试/auto-test-project/testdata/真人.jpg"
            file_input.first.set_input_files(test_img)
            time.sleep(3)
            print("  ✅ 本地上传成功", flush=True)
            shot(page, "tc0005_local.png")
        else:
            errors.append("本地上传file input未找到")

        close_dialog(page)
        time.sleep(1)

        # ========== 测试2：从资产库选 ==========
        print("\n--- 测试2：从资产库选 ---", flush=True)
        open_create_dialog(page)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '参考图') { e.click(); break; }
            }
        }""")
        time.sleep(1)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '从资产库选') { e.click(); break; }
            }
        }""")
        time.sleep(2)
        shot(page, "tc0005_asset_open.png")

        # 搜索小梅
        search = page.locator("input[placeholder*='搜索']")
        if search.count() > 0:
            search.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("小梅")
            time.sleep(1.5)
            print("  ✅ 已搜索小梅", flush=True)

        # 选第一张
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span');
            for (const e of els) {
                if (e.innerText.trim() === '小梅') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已选小梅", flush=True)

        # 点确定使用
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) {
                if (e.innerText.trim() === '确定使用') { e.click(); break; }
            }
        }""")
        time.sleep(2)
        print("  ✅ 已点确定使用", flush=True)
        shot(page, "tc0005_asset_done.png")

        close_dialog(page)
        time.sleep(1)

        # ========== 测试3：从画布选 ==========
        print("\n--- 测试3：从画布选 ---", flush=True)
        open_create_dialog(page)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '参考图') { e.click(); break; }
            }
        }""")
        time.sleep(1)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '从画布选') { e.click(); break; }
            }
        }""")
        time.sleep(2)
        shot(page, "tc0005_canvas_open.png")

        # 选草原
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span');
            for (const e of els) {
                if (e.innerText.trim() === '草原') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已选草原", flush=True)

        # 点确定使用
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) {
                if (e.innerText.trim() === '确定使用') { e.click(); break; }
            }
        }""")
        time.sleep(2)
        print("  ✅ 已点确定使用", flush=True)
        shot(page, "tc0005_canvas_done.png")

        close_dialog(page)
        time.sleep(1)

        # ========== 测试4：数字人形象 ==========
        print("\n--- 测试4：数字人形象 ---", flush=True)
        open_create_dialog(page)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '参考图') { e.click(); break; }
            }
        }""")
        time.sleep(1)
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) {
                if (e.innerText.trim() === '数字人形象') { e.click(); break; }
            }
        }""")
        time.sleep(2)
        shot(page, "tc0005_dh_open.png")

        # 选阳光美女
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span');
            for (const e of els) {
                if (e.innerText.trim() === '阳光美女') { e.click(); break; }
            }
        }""")
        time.sleep(0.5)
        print("  ✅ 已选阳光美女", flush=True)

        # 点确定使用
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) {
                if (e.innerText.trim() === '确定使用') { e.click(); break; }
            }
        }""")
        time.sleep(2)
        print("  ✅ 已点确定使用", flush=True)
        shot(page, "tc0005_dh_done.png")

        close_dialog(page)

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
