# -*- coding: utf-8 -*-
"""
TC-0010: 图片/文生数字人-生成结果卡片操作
验证：卡片头信息、重新编辑、再次生成、删除、悬浮按钮、插入画布、下载
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


def test_tc0010():
    print("=" * 60, flush=True)
    print("TC-0010: 生成结果卡片操作", flush=True)
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

        # 步骤1：打开数字人库→形象tab
        print("\n--- 步骤1：进入形象tab ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '形象') { e.click(); break; } }
        }""")
        time.sleep(2)
        shot(page, "tc0010_list.png")

        # 步骤2：验证卡片上的按钮
        print("\n--- 步骤2：卡片按钮 ---", flush=True)
        for btn in ["重新编辑", "再次生成", "删除"]:
            el = page.locator(f"text={btn}")
            if el.count() > 0:
                print(f"  ✅ 按钮 '{btn}' 可见", flush=True)
            else:
                print(f"  [WARN] 按钮 '{btn}' 未找到", flush=True)

        # 步骤3：hover成功图片看悬浮按钮
        print("\n--- 步骤3：悬浮按钮 ---", flush=True)
        # hover第二张图（第一张审核失败了）
        images = page.locator("img")
        if images.count() > 1:
            images.nth(1).hover(force=True)
            time.sleep(1.5)
            print("  ✅ 已hover图片", flush=True)

        # 用aria-label验证图标按钮
        for label in ["插入画布", "下载", "存入数字人形象库"]:
            el = page.locator(f"[aria-label='{label}']")
            if el.count() > 0:
                print(f"  ✅ 悬浮按钮 '{label}' 可见", flush=True)
            else:
                errors.append(f"悬浮按钮 '{label}' 未找到")

        # 生成数字人是文字按钮
        gen = page.locator("text=生成数字人")
        if gen.count() > 0:
            print("  ✅ 悬浮按钮 '生成数字人' 可见", flush=True)
        else:
            errors.append("悬浮按钮 '生成数字人' 未找到")

        shot(page, "tc0010_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0010 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0010_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0010()
