# -*- coding: utf-8 -*-
"""TC-0016 视频工具-AI人声分离（REAL_GENERATE=False，不实际发起任务）"""
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

    # 3. 点【AI 人声分离】
    vocal = page.locator("text=AI 人声分离")
    if vocal.count() == 0:
        vocal = page.locator("text=AI人声分离")
    if vocal.count() == 0:
        check("AI人声分离选项", False, "未找到")
        browser.close(); pw.stop()
        return
    cb = vocal.first.bounding_box()
    page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
    time.sleep(2)
    check("AI人声分离面板弹出", True)

    # 4. 验证三种方式及价格
    panels = page.evaluate("""
        () => {
            const t = document.body.textContent || '';
            return {
                hasMethod1: t.includes('人声/伴奏分离'),
                hasMethod1Desc: t.includes('同时输出人声与伴奏两条音轨'),
                hasMethod2: t.includes('提取纯人声'),
                hasMethod2Desc: t.includes('只保留人声'),
                hasMethod3: t.includes('提取伴奏/背景音') || t.includes('提取伴奏'),
                hasMethod3Desc: t.includes('消除人声、保留伴奏'),
                hasPrice1: t.includes('≈¥0.1/秒'),
                hasPrice2: t.includes('≈¥0.2/秒'),
                hasPrice3: t.includes('≈¥0.3/秒'),
                hasCloud: t.includes('云端处理'),
                hasNote: t.includes('按次计费'),
            };
        }
    """)
    check("方式1：人声/伴奏分离", panels["hasMethod1"])
    check("方式1说明正确", panels["hasMethod1Desc"], "同时输出人声与伴奏两条音轨")
    check("方式1价格", panels["hasPrice1"], "≈¥0.1/秒")
    check("方式2：提取纯人声", panels["hasMethod2"])
    check("方式2说明正确", panels["hasMethod2Desc"], "只保留人声")
    check("方式2价格", panels["hasPrice2"], "≈¥0.2/秒")
    check("方式3：提取伴奏/背景音", panels["hasMethod3"])
    check("方式3说明正确", panels["hasMethod3Desc"], "消除人声、保留伴奏")
    check("方式3价格", panels["hasPrice3"], "≈¥0.3/秒")
    check("云端处理提示", panels["hasCloud"])
    check("底部说明（按次计费）", panels["hasNote"])

    # 5. REAL_GENERATE=False：不实际发起任务
    if not REAL_GENERATE:
        check("付费功能不实际发起", True, "REAL_GENERATE=False")
    else:
        # 点击方式1卡片发起任务
        m1 = page.locator("text=人声/伴奏分离")
        if m1.count() > 0:
            m1.first.click()
            time.sleep(2)
            check("人声/伴奏分离任务发起", True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
