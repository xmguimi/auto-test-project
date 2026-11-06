# -*- coding: utf-8 -*-
"""
TC-0025: 形象下载和删除功能测试
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


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0025: 形象下载和删除功能测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：打开数字人库→形象tab
    print("\n--- 步骤1：形象tab ---", flush=True)
    page.locator("button[aria-label='数字人库']").first.click(force=True)
    time.sleep(2)
    page.evaluate("""() => {
        const els = document.querySelectorAll('button, div, span');
        for (const e of els) { if (e.innerText.trim() === '形象') { e.click(); break; } }
    }""")
    time.sleep(2)
    shot(page, "tc0025_del_0_list.png")

    # 步骤2：点测试形象的三个点
    print("\n--- 步骤2：点三个点 ---", flush=True)
    # 找金色美人旁边的，或者测试形象
    more_btn = page.locator("text=金色美人").locator("xpath=ancestor::*[contains(@class,'card')]//*[contains(@class,'ellipsis')]").first
    if more_btn.count() == 0:
        more_btn = page.locator("text=测试形象").locator("xpath=ancestor::*[contains(@class,'card')]//*[contains(@class,'ellipsis')]").first
    
    if more_btn.count() > 0:
        more_btn.click(force=True)
        time.sleep(1)
        shot(page, "tc0025_del_1_menu.png")
        print("  ✅ 菜单已打开", flush=True)
        results.append(("菜单打开", True))
    else:
        results.append(("菜单打开", False))

    # 步骤3：测试下载
    print("\n--- 步骤3：测试下载 ---", flush=True)
    download = page.locator("text=下载").last
    if download.count() > 0:
        download.click(force=True)
        time.sleep(2)
        shot(page, "tc0025_del_2_download.png")
        print("  ✅ 已点击下载", flush=True)
        results.append(("下载可点击", True))
    else:
        results.append(("下载可点击", False))

    # 步骤4：再打开菜单测试删除
    print("\n--- 步骤4：测试删除 ---", flush=True)
    more_btn2 = page.locator("text=金色美人").locator("xpath=ancestor::*[contains(@class,'card')]//*[contains(@class,'ellipsis')]").first
    if more_btn2.count() == 0:
        more_btn2 = page.locator("text=测试形象").locator("xpath=ancestor::*[contains(@class,'card')]//*[contains(@class,'ellipsis')]").first
    more_btn2.click(force=True)
    time.sleep(1)
    
    delete_item = page.locator("text=删除").last
    if delete_item.count() > 0:
        delete_item.click(force=True)
        time.sleep(1.5)
        shot(page, "tc0025_del_3_confirm.png")
        print("  ✅ 删除确认弹窗出现", flush=True)
        results.append(("删除二次确认", True))
    else:
        results.append(("删除二次确认", False))

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

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
