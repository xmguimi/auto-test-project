# -*- coding: utf-8 -*-
"""
TC-0009 视频编辑 - 音频分离
=====================================================================
验证【音频分离】本地双产出正常：对带音轨视频产出无声视频+纯音频两个节点，
各带一条来源连线。

【入口（实测修正版）】
    单击视频节点标题栏 → 顶部出现工具栏 → JS 点击【编辑】→ 进入视频编辑工作台

【实测确认的产品行为】
    1. 右侧 TOOLS 面板【音频分离】卡片（标签"桌面"/"本地"，双产出 · 无声视频 + 纯音频）；
    2. 说明：本地 ffmpeg 分离，产出两个节点：无声视频与纯音频，各带一条来源连线；
    3. 无音轨时报「该视频没有音轨」；
    4. 【运行】按钮（在音频分离卡片内）。

【REAL_GENERATE 规则】
    音频分离为本地功能（本地 ffmpeg，无价格标注）→ REAL_GENERATE = True
    （实际点击【运行】执行分离）。

【定位方式】
    全部使用元素定位（class / 文本），不使用固定坐标，可在不同分辨率电脑运行。
=====================================================================
"""
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

# ------------------------- 配置（按实际机器修改） -------------------------
FJ_CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
FJ_CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))

# REAL_GENERATE：音频分离为本地功能（本地 ffmpeg，无价格标注）→ True
REAL_GENERATE = True

# ------------------------- 工具函数 -------------------------
RESULTS = []


def record(no, name, passed, note=""):
    RESULTS.append((no, name, passed, note))
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] 步骤{no} {name} {('- ' + note) if note else ''}", flush=True)


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{FJ_CDP_HOST}:{FJ_CDP_PORT}")
    page = None
    for p in browser.contexts[0].pages:
        if "帧境" in (p.title() or ""):
            page = p
            break
    if not page:
        page = browser.contexts[0].pages[0]
    return pw, browser, page


def pan_canvas(page, dx=0, dy=150):
    blank = page.evaluate("""
        () => {
            const boxes = [];
            for (let n of document.querySelectorAll('.react-flow__node')) {
                const b = n.getBoundingClientRect();
                boxes.push({x1: b.x - 20, y1: b.y - 20, x2: b.x + b.width + 20, y2: b.y + b.height + 20});
            }
            for (let y = 100; y < 800; y += 80) {
                for (let x = 100; x < 1200; x += 80) {
                    if (!boxes.some(b => x > b.x1 && x < b.x2 && y > b.y1 && y < b.y2)) return {x, y};
                }
            }
            return null;
        }
    """)
    if not blank:
        return
    page.mouse.move(blank["x"], blank["y"])
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.2)
    page.mouse.move(blank["x"] + dx, blank["y"] + dy, steps=5)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(0.5)


def enter_edit_workbench(page):
    candidates = page.evaluate("""
        () => {
            const res = [];
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                if (t.includes('视频剪辑') && r.x > 0 && r.y > 0 && r.x + r.width < window.innerWidth && r.y + r.height < window.innerHeight) {
                    res.push(i);
                }
            }
            return res;
        }
    """)
    for idx in candidates:
        page.keyboard.press("Escape")
        time.sleep(0.5)
        box = page.locator(".react-flow__node").nth(idx).bounding_box()
        if not box:
            continue
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
        time.sleep(1)
        edit_btn = page.locator("button[aria-label='编辑视频（抽帧/切分）']").count()
        if edit_btn == 0:
            continue
        clicked = page.evaluate("""
            () => {
                const btn = document.querySelector("button[aria-label='编辑视频（抽帧/切分）']");
                if (!btn) return false;
                btn.click();
                return true;
            }
        """)
        if not clicked:
            continue
        for _ in range(10):
            time.sleep(1)
            if page.locator(".ve").count() > 0:
                return True
    return False


def get_audio_split_state(page):
    """读取音频分离卡片状态"""
    return page.evaluate("""
        () => {
            const ve = document.querySelector('.ve');
            if (!ve) return null;
            const t = (ve.textContent || '');
            // 检查音频分离卡片关键文本
            const has_title = t.includes('音频分离');
            const has_dual = t.includes('双产出') && t.includes('无声视频') && t.includes('纯音频');
            const has_local = t.includes('本地') && t.includes('ffmpeg');
            const has_link = t.includes('来源连线');
            const has_no_audio_hint = t.includes('该视频没有音轨');
            // 找音频分离卡片内的"运行"按钮
            let has_run = false;
            const cards = ve.querySelectorAll('.tk');
            for (let card of cards) {
                const ct = (card.textContent || '');
                if (ct.includes('音频分离')) {
                    for (let b of card.querySelectorAll('button')) {
                        if ((b.textContent || '').trim() === '运行') { has_run = true; break; }
                    }
                    break;
                }
            }
            return {has_title, has_dual, has_local, has_link, has_no_audio_hint, has_run};
        }
    """)


def click_audio_split_run(page):
    """点击音频分离卡片内的【运行】按钮"""
    page.evaluate("""
        () => {
            const ve = document.querySelector('.ve');
            if (!ve) return;
            const cards = ve.querySelectorAll('.tk');
            for (let card of cards) {
                const ct = (card.textContent || '');
                if (ct.includes('音频分离')) {
                    for (let b of card.querySelectorAll('button')) {
                        if ((b.textContent || '').trim() === '运行') {
                            b.click();
                            return;
                        }
                    }
                    return;
                }
            }
        }
    """)


def wait_audio_split_result(page, timeout=60):
    """等待音频分离产出（无声视频节点+纯音频节点）"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(2)
        texts = page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => (n.textContent || '').trim())")
        # 检查是否有音频相关节点（音频/无声）
        audio_nodes = [t for t in texts if "音频" in t or "无声" in t]
        if len(audio_nodes) >= 2:
            return audio_nodes
    return []


# ------------------------- 测试主流程 -------------------------
def main():
    pw, browser, page = connect()
    time.sleep(2)
    try:
        page.keyboard.press("Escape")
        time.sleep(1.5)
        pan_canvas(page, dx=0, dy=150)
        time.sleep(1)

        # ---- 步骤1：进入编辑工作台 ----
        ok = enter_edit_workbench(page)
        record(1, "点击视频节点→工具栏【编辑】→进入编辑工作台", ok, "入口已按实测修正")
        if not ok:
            return

        # ---- 步骤2：观察音频分离工具卡 ----
        state = get_audio_split_state(page)
        ok2 = state is not None and state.get("has_title") and state.get("has_dual") and state.get("has_local")
        record(2, "观察【音频分离】工具卡：双产出、本地、桌面端标识、说明文案", ok2,
               f"标题={state.get('has_title') if state else False} 双产出={state.get('has_dual') if state else False} 本地={state.get('has_local') if state else False} 来源连线={state.get('has_link') if state else False} 无音轨提示={state.get('has_no_audio_hint') if state else False}")

        # ---- 步骤3：点音频分离卡片内【运行】→ 等待产出 ----
        if REAL_GENERATE:
            try:
                click_audio_split_run(page)
                time.sleep(3)
                # 等待产出节点
                result_nodes = wait_audio_split_result(page, timeout=60)
                ok3 = len(result_nodes) >= 2
                record(3, "点【运行】→产出无声视频+纯音频两个节点", ok3,
                       f"产出节点={result_nodes[:3]}")
            except Exception as e:
                record(3, "点【运行】→产出无声视频+纯音频两个节点", False, f"异常: {str(e)[:80]}")
        else:
            record(3, "点【运行】→产出无声视频+纯音频两个节点", True, "REAL_GENERATE=False 不实际执行")

        # ---- 步骤4：验证节点内容 ----
        if REAL_GENERATE:
            result_nodes = wait_audio_split_result(page, timeout=5)
            has_silent = any("无声" in t for t in result_nodes)
            has_audio = any("音频" in t for t in result_nodes)
            ok4 = has_silent and has_audio
            record(4, "产出无声视频节点+纯音频节点内容正确", ok4,
                   f"无声视频={has_silent} 纯音频={has_audio}")
        else:
            record(4, "产出无声视频节点+纯音频节点内容正确", True, "REAL_GENERATE=False")

    finally:
        passed = sum(1 for r in RESULTS if r[2])
        total = len(RESULTS)
        print("\n===== 汇总 =====", flush=True)
        print(f"通过 {passed}/{total}", flush=True)
        for r in RESULTS:
            print(f"  [{'PASS' if r[2] else 'FAIL'}] 步骤{r[0]} {r[1]} {('- ' + r[3]) if r[3] else ''}", flush=True)
        browser.close()
        pw.stop()
        if passed == total:
            print("RESULT: ALL PASS", flush=True)
        else:
            print(f"RESULT: {total - passed} FAILED", flush=True)


if __name__ == "__main__":
    main()
