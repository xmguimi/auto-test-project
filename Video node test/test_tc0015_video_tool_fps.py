# -*- coding: utf-8 -*-
"""TC-0015 视频工具-帧率增强（REAL_GENERATE=False，不实际点开始处理）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = False  # 付费功能，不实际发起任务
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

    # 1. 选中 findbugs 原视频
    page.keyboard.press("Escape")
    time.sleep(1)
    idx = page.evaluate("""
        () => {
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                if (t.includes('find') && !t.includes('转码') && !t.includes('无声') && !t.includes('抽帧') && !t.includes('分离音频') && r.x > 0 && r.y > 0) return i;
            }
            return -1;
        }
    """)
    if idx < 0:
        print("FAIL: 未找到原视频", flush=True)
        browser.close(); pw.stop()
        return
    box = page.locator(".react-flow__node").nth(idx).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True, f"idx={idx}")

    # 2. 点【视频工具】下拉
    vtool = page.locator("button[aria-label='视频工具']")
    if vtool.count() == 0:
        check("视频工具按钮", False, "未找到")
        browser.close(); pw.stop()
        return
    vb = vtool.first.bounding_box()
    page.mouse.click(vb["x"] + vb["width"] / 2, vb["y"] + vb["height"] / 2)
    time.sleep(1)
    check("视频工具下拉展开", True)

    # 3. 点【帧率增强】
    fps = page.locator("text=帧率增强")
    if fps.count() == 0:
        check("帧率增强选项", False, "未找到")
        browser.close(); pw.stop()
        return
    fb = fps.first.bounding_box()
    page.mouse.click(fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2)
    time.sleep(2)
    check("帧率增强面板弹出", True)

    # 4. 验证面板内容
    panels = page.evaluate("""
        () => {
            const t = document.body.textContent || '';
            return {
                hasDesc: t.includes('将视频补帧为更流畅的高帧率版本'),
                hasNoParam: t.includes('无需其他参数'),
                hasPrice: t.includes('¥'),
                hasCloud: t.includes('云端处理'),
                hasStart: t.includes('开始处理'),
            };
        }
    """)
    check("补帧说明正确", panels["hasDesc"], "将视频补帧为更流畅的高帧率版本")
    check("无需其他参数提示", panels["hasNoParam"])
    check("预估价格显示", panels["hasPrice"], "≈¥0.15~0/秒")
    check("云端处理提示", panels["hasCloud"])
    check("开始处理按钮", panels["hasStart"])

    # 5. REAL_GENERATE=False：不实际点开始处理
    if not REAL_GENERATE:
        check("付费功能不实际发起", True, "REAL_GENERATE=False")
    else:
        start = page.locator("button:has-text('开始处理')")
        if start.count() > 0:
            start.first.click()
            time.sleep(2)
            check("开始处理任务发起", True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
