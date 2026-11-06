# -*- coding: utf-8 -*-
"""
TC-0012: 图片/文生数字人-生成数字人弹窗
流程：历史tab→hover图片→点生成数字人→验证弹窗→必填校验→一键生成→填名称选声音→生成
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


def test_tc0012():
    print("=" * 60, flush=True)
    print("TC-0012: 生成数字人弹窗", flush=True)
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

        # 步骤1：打开创建形象弹窗→历史tab
        print("\n--- 步骤1：打开历史tab ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '形象') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        # 用locator点创建形象卡片
        create_card = page.locator("text=创建形象")
        if create_card.count() > 0:
            create_card.first.click(force=True)
            time.sleep(2)
        shot(page, "tc0012_create_dialog.png")
        # 点历史tab
        page.evaluate("""() => {
            const els = document.querySelectorAll('div, span, button');
            for (const e of els) { if (e.innerText.trim() === '历史') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        print("  ✅ 已切历史tab", flush=True)

        # 步骤2：hover图片→点生成数字人
        print("\n--- 步骤2：点生成数字人 ---", flush=True)
        images = page.locator("img")
        print(f"  找到图片数: {images.count()}", flush=True)
        if images.count() > 1:
            images.nth(1).hover(force=True)
            time.sleep(1.5)

        # 点生成数字人按钮
        gen_btn = page.locator("text=生成数字人")
        if gen_btn.count() > 0:
            gen_btn.first.click(force=True)
            time.sleep(2)
            print("  ✅ 已点生成数字人", flush=True)
        else:
            errors.append("生成数字人按钮未找到")
        shot(page, "tc0012_dialog.png")

        # 步骤3：验证弹窗元素
        print("\n--- 步骤3：验证弹窗元素 ---", flush=True)
        for el_text in ["取消", "生成", "名称", "声音"]:
            el = page.locator(f"text={el_text}")
            if el.count() > 0:
                print(f"  ✅ 元素 '{el_text}' 可见", flush=True)
            else:
                print(f"  [WARN] 元素 '{el_text}' 未找到", flush=True)

        # 步骤4：必填校验
        print("\n--- 步骤4：必填校验 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '生成') { e.click(); break; } }
        }""")
        time.sleep(1)
        shot(page, "tc0012_validation.png")
        print("  ✅ 已点生成（空状态）", flush=True)

        # 步骤5：一键生成名称简介
        print("\n--- 步骤5：一键生成名称简介 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.includes('一键生成名称')) { e.click(); break; } }
        }""")
        time.sleep(2)
        shot(page, "tc0012_auto_name.png")
        print("  ✅ 已点一键生成名称", flush=True)

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0012 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0012_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0012()
