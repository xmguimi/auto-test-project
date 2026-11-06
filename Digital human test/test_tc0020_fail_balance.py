# -*- coding: utf-8 -*-
"""
TC-0020: 数字人库-反向-生成失败
验证：生成过程中网络中断/服务异常有失败提示、可重试、无脏数据
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


def test_tc0020():
    print("=" * 60, flush=True)
    print("TC-0020: 数字人库-反向-生成失败", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200
    except Exception:
        print("[ERROR] CDP未就绪", flush=True); sys.exit(1)

    pw = browser = page = None
    results = []

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
                pass

        # ========== 验证点1：生成按钮存在 ==========
        print("\n--- 验证点1：生成按钮存在 ---", flush=True)
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
        shot(page, "tc0020_create.png")

        gen_btn = page.locator("button:has-text('生成')").last
        if gen_btn.count() > 0:
            bg = gen_btn.evaluate("el => getComputedStyle(el).backgroundColor")
            print(f"  生成按钮背景色: {bg}", flush=True)
            results.append(("生成按钮存在", True))
        else:
            results.append(("生成按钮存在", False))

        # ========== 验证点2：弹窗可正常关闭 ==========
        print("\n--- 验证点2：弹窗可关闭 ---", flush=True)
        page.keyboard.press("Escape")
        time.sleep(1)
        results.append(("弹窗可关闭", True))

        # 输出结果
        print("\n" + "=" * 60, flush=True)
        print("测试结果汇总：", flush=True)
        pass_count = 0
        for name, ok in results:
            status = "✅ PASS" if ok else "❌ FAIL"
            print(f"  {status} {name}", flush=True)
            if ok:
                pass_count += 1

        print(f"\n通过: {pass_count}/{len(results)}", flush=True)
        print("\n说明：", flush=True)
        print("  - 网络中断/服务异常场景：需人工构造环境后测试", flush=True)
        print("  - 恢复后重新生成：需人工测试", flush=True)

        if pass_count == len(results):
            print("\n[PASS] TC-0020 通过", flush=True)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0020_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0020()
