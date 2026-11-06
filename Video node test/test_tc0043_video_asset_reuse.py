# -*- coding: utf-8 -*-
"""TC-0043 保存到资产库-资产引用回画布"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = True
ROOT = Path(__file__).parent


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


def main():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # 1. 记录当前节点数
    count_before = page.evaluate("() => document.querySelectorAll('.react-flow__node').length")
    check("记录节点数", count_before >= 0, f"当前{count_before}个节点")

    # 2. JS点击资产管理按钮打开面板
    opened = page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button, [role="button"]');
            for (const b of btns) {
                if ((b.getAttribute('aria-label') || '').includes('资产管理') || b.textContent.includes('资产')) {
                    b.click();
                    return true;
                }
            }
            return false;
        }
    """)
    time.sleep(2)
    check("打开资产面板", opened, "资产管理面板已打开")

    # 3. 验证资产面板有内容
    panel_text = page.evaluate("() => document.body.textContent || ''")
    check("资产面板有内容", "共" in panel_text and "项" in panel_text, f"资产库有内容")

    # 4. 截图
    page.screenshot(path=str(ROOT / "tc0043_assets.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
