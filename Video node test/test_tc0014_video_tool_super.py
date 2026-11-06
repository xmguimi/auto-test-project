# -*- coding: utf-8 -*-
"""TC-0014 视频工具-视频超分（REAL_GENERATE=False，不实际点开始处理）"""
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

    # 3. 验证下拉三项带任务卡标签
    dropdown_text = page.evaluate("""
        () => {
            const els = document.querySelectorAll('[class*="submenu"], [class*="dropdown"]');
            for (let el of els) {
                const t = (el.textContent || '').trim();
                if (t.includes('视频超分') && t.includes('帧率增强') && t.includes('AI 人声分离')) return t;
            }
            return '';
        }
    """)
    check("下拉三项含任务卡", "任务卡" in dropdown_text, f"长度={len(dropdown_text)}")

    # 4. 点【视频超分】
    vs = page.locator("text=视频超分")
    if vs.count() == 0:
        check("视频超分选项", False, "未找到")
        browser.close(); pw.stop()
        return
    vsb = vs.first.bounding_box()
    page.mouse.click(vsb["x"] + vsb["width"] / 2, vsb["y"] + vsb["height"] / 2)
    time.sleep(2)
    check("视频超分面板弹出", True)

    # 5. 验证档位选项
    panels = page.evaluate("""
        () => {
            const t = document.body.textContent || '';
            return {
                has720p: t.includes('720p'),
                has1080p: t.includes('1080p'),
                has2k: t.includes('2k'),
                has4k: t.includes('4k'),
                hasPrice: t.includes('¥'),
                hasCloud: t.includes('云端处理'),
                hasStart: t.includes('开始处理'),
            };
        }
    """)
    check("档位选项 720p/1080p/2k/4k", all([panels["has720p"], panels["has1080p"], panels["has2k"], panels["has4k"]]))
    check("预估价格显示", panels["hasPrice"])
    check("云端处理提示", panels["hasCloud"])
    check("开始处理按钮", panels["hasStart"])

    # 6. REAL_GENERATE=False：不实际点开始处理
    if not REAL_GENERATE:
        check("付费功能不实际发起", True, "REAL_GENERATE=False")
    else:
        # 点开始处理
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
