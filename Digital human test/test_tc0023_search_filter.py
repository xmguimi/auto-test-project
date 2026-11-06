# -*- coding: utf-8 -*-
"""
TC-0023: 数字人tab搜索与筛选
验证：搜索已有名称匹配、搜索不存在名称空态、清空恢复
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


def test_tc0023():
    print("=" * 60, flush=True)
    print("TC-0023: 数字人tab搜索与筛选", flush=True)
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

        # 步骤1：打开数字人库→数字人tab
        print("\n--- 步骤1：数字人tab ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '数字人') { e.click(); break; } }
        }""")
        time.sleep(2)
        shot(page, "tc0023_0_list.png")

        # 验证点1：搜索框存在
        print("\n--- 验证点1：搜索框存在 ---", flush=True)
        search_box = page.locator("input[placeholder*='搜数字人']").first
        if search_box.count() > 0:
            print("  ✅ 搜索框存在", flush=True)
            results.append(("搜索框存在", True))
        else:
            results.append(("搜索框存在", False))

        # 验证点2：搜索已有名称"小美"
        print("\n--- 验证点2：搜索已有名称 ---", flush=True)
        if search_box.count() > 0:
            search_box.fill("小美")
            time.sleep(1.5)
            shot(page, "tc0023_1_search_xiaomei.png")
            xiaomei = page.locator("text=小美").first
            if xiaomei.count() > 0:
                print("  ✅ 搜索'小美'匹配成功", flush=True)
                results.append(("搜索已有名称匹配", True))
            else:
                results.append(("搜索已有名称匹配", False))

        # 验证点3：搜索不存在名称
        print("\n--- 验证点3：搜索不存在名称 ---", flush=True)
        if search_box.count() > 0:
            search_box.fill("不存在的数字人xyz")
            time.sleep(1.5)
            shot(page, "tc0023_2_search_none.png")
            empty_text = page.locator("text=/没有叫/").first
            if empty_text.count() > 0:
                print(f"  ✅ 搜索无结果: {empty_text.inner_text()}", flush=True)
                results.append(("搜索无结果空态", True))
            else:
                results.append(("搜索无结果空态", False))

        # 验证点4：清空恢复
        print("\n--- 验证点4：清空恢复 ---", flush=True)
        if search_box.count() > 0:
            search_box.fill("")
            time.sleep(1.5)
            shot(page, "tc0023_3_clear.png")
            xiaomei2 = page.locator("text=小美").first
            if xiaomei2.count() > 0:
                print("  ✅ 清空后恢复显示全部", flush=True)
                results.append(("清空恢复全部", True))
            else:
                results.append(("清空恢复全部", False))

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

        if pass_count == len(results):
            print("\n[PASS] TC-0023 通过", flush=True)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0023_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0023()
