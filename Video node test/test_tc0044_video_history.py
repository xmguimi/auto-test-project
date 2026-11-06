# -*- coding: utf-8 -*-
"""TC-0044 视频节点-生成历史查看"""
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

    # 0. 按ESC关闭面板
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 找所有左侧栏按钮的title/aria-label
    buttons_info = page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button, [role="button"], .sidebar-item, nav div');
            return Array.from(btns).map(b => ({
                tag: b.tagName,
                text: (b.textContent || '').trim().substring(0, 20),
                aria: b.getAttribute('aria-label') || '',
                title: b.getAttribute('title') || '',
                x: b.getBoundingClientRect().x
            })).filter(b => b.x < 100);
        }
    """)
    print("左侧栏按钮:", flush=True)
    for b in buttons_info:
        print(f"  tag={b['tag']}, text={b['text']}, aria={b['aria']}, title={b['title']}, x={b['x']}", flush=True)

    # 2. JS点击生成历史（按aria-label或title匹配）
    opened = page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button, [role="button"], [aria-label]');
            for (const b of btns) {
                const aria = b.getAttribute('aria-label') || '';
                const title = b.getAttribute('title') || '';
                if (aria.includes('历史') || title.includes('历史') || aria.includes('生成')) {
                    b.click();
                    return aria || title;
                }
            }
            return false;
        }
    """)
    time.sleep(2)
    check("JS点击生成历史", opened is not False, f"按钮={opened}")

    # 3. 截图
    page.screenshot(path=str(ROOT / "tc0044_history.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
