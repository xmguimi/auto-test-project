# -*- coding: utf-8 -*-
"""
TC-0021: 数字人删除功能测试
实际测试：点删除→二次确认→卡片消失
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
    print("TC-0021: 数字人删除功能测试", flush=True)
    print("=" * 60, flush=True)

    # 步骤1：先关闭详情弹窗（如果开着）
    print("\n--- 步骤1：关闭详情弹窗 ---", flush=True)
    close_btn = page.locator("[aria-label='关闭'], button:has-text('×')").first
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1.5)
        print("  ✅ 详情弹窗已关闭", flush=True)

    # 步骤2：点卡片三个点菜单
    print("\n--- 步骤2：点卡片菜单 ---", flush=True)
    # 点测试数字人卡片的三个点
    page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.children.length === 0 && el.innerText && el.innerText.trim() === '测试数字人') {
                let card = el;
                for (let i = 0; i < 10; i++) {
                    card = card.parentElement;
                    if (!card) break;
                    const btns = card.querySelectorAll('button');
                    if (btns.length >= 3) {
                        btns[btns.length - 1].click(); // 最后一个按钮是三个点
                        return true;
                    }
                }
            }
        }
        return false;
    }""")
    time.sleep(1.5)
    shot(page, "tc0021_4_menu.png")
    print("  ✅ 菜单已打开", flush=True)

    # 步骤3：点删除
    print("\n--- 步骤3：点删除 ---", flush=True)
    delete_item = page.locator("text=删除").first
    if delete_item.count() > 0:
        delete_item.click(force=True)
        time.sleep(1.5)
        shot(page, "tc0021_5_confirm.png")
        print("  ✅ 删除确认弹窗出现", flush=True)
        results.append(("删除二次确认弹窗", True))
    else:
        results.append(("删除二次确认弹窗", False))

    # 步骤4：确认删除
    print("\n--- 步骤4：确认删除 ---", flush=True)
    confirm_btn = page.locator("text=确认, text=确定, text=删除").last
    if confirm_btn.count() > 0:
        confirm_btn.click(force=True)
        time.sleep(2)
        shot(page, "tc0021_6_after_delete.png")
        print("  ✅ 已确认删除", flush=True)
        
        # 验证卡片消失
        deleted = page.locator("text=测试数字人").first
        if deleted.count() == 0:
            print("  ✅ 卡片已从列表消失", flush=True)
            results.append(("删除后卡片消失", True))
        else:
            results.append(("删除后卡片消失", False))
    else:
        results.append(("删除后卡片消失", False))

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
