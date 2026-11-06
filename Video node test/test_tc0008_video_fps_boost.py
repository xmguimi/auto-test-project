# -*- coding: utf-8 -*-
"""
TC-0008 视频编辑 - 帧率增强
=====================================================================
验证【帧率增强】工具卡显示正常：补帧说明、无需其他参数、预估价格、
云端处理提示、【运行】按钮存在（REAL_GENERATE=False，不实际发起付费任务）。

【入口（实测修正版）】
    单击视频节点标题栏 → 顶部出现工具栏 → JS 点击【编辑】→ 进入视频编辑工作台

【实测确认的产品行为】
    1. 右侧 TOOLS 面板【帧率增强】卡片（标签"云端"，预估价格 ≈ ¥0.15~0/秒）；
    2. 说明：补帧 · 无需其他参数；
    3. 预估价格 ≈ ¥0.15~0/秒；
    4. 云端处理提示：源视频不超过 50M；提交后画布上会出现生成中节点。；
    5. 【运行】按钮（class tk-run，紫色）。

【REAL_GENERATE 规则】
    帧率增强为云端付费功能（预估价格 ≈ ¥0.15~0/秒）→ REAL_GENERATE = False
    （不实际点击【运行】发起付费任务，仅验证到按钮存在）。

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

# REAL_GENERATE：帧率增强为云端付费功能（预估价格 ≈ ¥0.15~0/秒）→ False
REAL_GENERATE = False

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


def get_fps_boost_state(page):
    """读取帧率增强卡片状态"""
    return page.evaluate("""
        () => {
            const ve = document.querySelector('.ve');
            if (!ve) return null;
            const t = (ve.textContent || '');
            // 检查帧率增强卡片关键文本
            const has_title = t.includes('帧率增强');
            const has_desc = t.includes('补帧') && t.includes('无需其他参数');
            // 提取预估价格（帧率增强卡片的价格）
            const priceMatch = t.match(/帧率增强[\\s\\S]*?预估价格[\\s\\S]*?(≈\\s*¥[\\d.~]+\\/秒)/);
            const price = priceMatch ? priceMatch[1] : '';
            // 云端处理提示
            const has_cloud = t.includes('云端处理');
            const has_50m = t.includes('50M');
            // 运行按钮
            let has_run = false;
            for (let b of ve.querySelectorAll('button')) {
                if ((b.textContent || '').trim() === '运行') { has_run = true; break; }
            }
            return {has_title, has_desc, price, has_cloud, has_50m, has_run};
        }
    """)


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

        # ---- 步骤2：观察帧率增强工具卡 ----
        state = get_fps_boost_state(page)
        ok2 = state is not None and state.get("has_title") and state.get("has_desc")
        record(2, "观察【帧率增强】工具卡：补帧说明、无需其他参数", ok2,
               f"标题={state.get('has_title') if state else False} 说明={state.get('has_desc') if state else False}")

        # ---- 步骤3：观察预估价格显示 ----
        ok3 = state is not None and state.get("price", "") != ""
        record(3, "预估价格显示正确", ok3,
               f"预估价格={state.get('price') if state else ''}")

        # ---- 步骤4：观察云端处理提示、源视频不超过50M ----
        ok4 = state is not None and state.get("has_cloud") and state.get("has_50m")
        record(4, "观察云端处理提示、源视频不超过50M说明", ok4,
               f"云端={state.get('has_cloud') if state else False} 50M={state.get('has_50m') if state else False}")

        # ---- 步骤5：观察【运行】按钮存在（REAL_GENERATE=False 不点击） ----
        ok5 = state is not None and state.get("has_run")
        record(5, "【运行】按钮存在（REAL_GENERATE=False 不实际发起付费任务）", ok5,
               f"运行按钮={state.get('has_run') if state else False}")

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
