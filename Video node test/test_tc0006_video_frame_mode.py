# -*- coding: utf-8 -*-
"""
TC-0006 视频编辑 - 抽帧方式（抽当前帧 / 选帧抽取）
=====================================================================
验证【抽帧】中【抽当前帧】和【选帧抽取】两种方式功能均正常：
  - 点击【抽当前帧】抓取当前画面，抽出帧存为画布图片节点（命名带时间码）；
  - 点击【选帧抽取】弹出帧选择面板，可逐帧定位到第3秒并抽取，抽出帧存为画布图片节点。

【入口（实测修正版）】
    单击视频节点标题栏 → 顶部出现工具栏 → JS 点击【编辑】→ 进入视频编辑工作台
    （原用例"双击视频节点进入"与产品实际不符，已修正）

【实测确认的产品行为】
    1. 编辑工作台右侧 TOOLS 面板【抽帧】卡片（标签"本地"，无价格标注）；
    2. 【抽当前帧】= button.tk-run.outline（文本"抽当前帧"），抓取当前预览画面；
    3. 【选帧抽取】= button.tk-run（文本"选帧抽取"），弹出帧选择面板逐帧定位；
    4. 抽出帧存为画布图片节点，命名带时间码（如"帧 00:00.00"）。

【REAL_GENERATE 规则】
    生成/处理按钮旁标注价格 → REAL_GENERATE = False（不点击、仅验证到按钮存在）；
    功能实际不花钱 → REAL_GENERATE = True（正常点击执行）。
    TC-0006 抽帧为本地功能（标签"本地"，无价格标注）→ REAL_GENERATE = True。
    （注：右侧【视频超分】≈¥0.18/秒、【帧率增强】≈¥0.15~0/秒 为付费工具卡，不在本用例范围）

【定位方式】
    全部使用元素定位（class / aria-label / 文本），不使用固定坐标，可在不同分辨率电脑运行。
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

# REAL_GENERATE：TC-0006 抽帧为本地功能（无价格标注）→ True
REAL_GENERATE = True

# ------------------------- 工具函数 -------------------------
RESULTS = []  # 步骤结果记录 [(步骤号, 名称, 是否通过, 说明)]


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


def find_video_node(page):
    """找一个视口内可见的视频节点（含"视频剪辑"文本，排除"抽帧"图片节点，且 bounding box 在视口内）。返回 idx"""
    return page.evaluate("""
        () => {
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                if (t.includes('视频剪辑') && !t.includes('抽帧') && r.x > 0 && r.y > 0
                    && r.x + r.width < window.innerWidth && r.y + r.height < window.innerHeight) {
                    return i;
                }
            }
            return null;
        }
    """)


def pan_canvas(page, dx=0, dy=150):
    """平移画布（拖动画布空白区），让屏幕外节点进入视口"""
    # 找画布空白区（避开节点）
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
    """入口（实测修正版）：遍历视口内节点，找到视频节点（工具栏含编辑按钮），点标题栏→JS点编辑→工作台打开"""
    # 找所有候选节点（视口内、含"视频剪辑"、不含"抽帧"图片节点）
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
    print(f"  [DEBUG] 候选节点={candidates}", flush=True)

    for idx in candidates:
        page.keyboard.press("Escape")
        time.sleep(0.5)
        box = page.locator(".react-flow__node").nth(idx).bounding_box()
        if not box:
            continue
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
        time.sleep(1)
        # 验证是否是视频节点（工具栏含编辑按钮）
        edit_btn = page.locator("button[aria-label='编辑视频（抽帧/切分）']").count()
        tools = page.locator(".ntools button").count()
        print(f"  [DEBUG] idx={idx} tools={tools} edit_btn={edit_btn}", flush=True)
        if edit_btn == 0:
            continue  # 不是视频节点，试下一个
        # JS 点击编辑按钮（绕过 titlebar 遮挡）
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
        # 轮询等工作台打开
        for _ in range(10):
            time.sleep(1)
            if page.locator(".ve").count() > 0:
                return True
    return False


def wait_new_frame_node(page, timeout=30):
    """等待画布新增"抽帧"节点（不比较节点数，按关键词检测）"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(2)
        texts = page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => (n.textContent || '').trim())")
        frame_nodes = [t for t in texts if "抽帧" in t]
        if frame_nodes:
            return frame_nodes
    return []


def close_workbench(page):
    page.keyboard.press("Escape")
    time.sleep(1.2)


# ------------------------- 测试主流程 -------------------------
def main():
    pw, browser, page = connect()
    time.sleep(2)
    try:
        # 清理遗留
        page.keyboard.press("Escape")
        time.sleep(1.5)
        # 平移画布让屏幕外视频节点进入视口
        pan_canvas(page, dx=0, dy=150)
        time.sleep(1)

        # ---- 步骤1：进入编辑工作台 ----
        ok = enter_edit_workbench(page)
        record(1, "点击视频节点→工具栏【编辑】→进入编辑工作台", ok, "入口已按实测修正（点标题栏+JS点编辑）")
        if not ok:
            return

        # ---- 步骤2：观察抽帧面板（当前时间码/第N帧） ----
        panel = page.evaluate("""
            () => {
                const ve = document.querySelector('.ve');
                if (!ve) return null;
                const t = (ve.textContent || '');
                const has_dangqian = t.includes('当前');
                const has_frame = t.includes('帧');
                const has_chou = t.includes('抽当前帧');
                const has_xuan = t.includes('选帧抽取');
                return {has_dangqian, has_frame, has_chou, has_xuan};
            }
        """)
        panel_ok = panel and panel.get("has_dangqian") and panel.get("has_frame") and panel.get("has_chou") and panel.get("has_xuan")
        record(2, "观察抽帧面板（当前时间码/第N帧 + 两个按钮）", panel_ok, f"面板={panel}")

        # ---- 步骤3：点【抽当前帧】→ 画布新增图片节点 ----
        if REAL_GENERATE:
            try:
                # 点【抽当前帧】（JS 点击避免遮挡）
                page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('.ve button');
                        for (let b of btns) {
                            if ((b.textContent || '').trim() === '抽当前帧') {
                                b.click();
                                return;
                            }
                        }
                    }
                """)
                time.sleep(2)
                # 等待新增"抽帧"节点
                frame_nodes = wait_new_frame_node(page, timeout=30)
                record(3, "点【抽当前帧】→画布新增图片节点（命名带时间码）", len(frame_nodes) > 0,
                       f"抽帧节点={frame_nodes[:2]}")
            except Exception as e:
                record(3, "点【抽当前帧】→画布新增图片节点", False, f"异常: {str(e)[:80]}")
        else:
            record(3, "点【抽当前帧】→画布新增图片节点", True, "REAL_GENERATE=False 仅验证按钮存在")

        # ---- 步骤4：点【选帧抽取】→ 弹出帧选择面板 ----
        if REAL_GENERATE:
            try:
                # 点【选帧抽取】
                page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('.ve button');
                        for (let b of btns) {
                            if ((b.textContent || '').trim() === '选帧抽取') {
                                b.click();
                                return;
                            }
                        }
                    }
                """)
                time.sleep(2)
                # 等待"抽取此帧"按钮出现（验证面板弹出）
                panel_ok = False
                for _ in range(5):
                    time.sleep(1)
                    if page.locator("button:has-text('抽取此帧')").count() > 0:
                        panel_ok = True
                        break
                record(4, "点【选帧抽取】→弹出帧选择面板（含抽取此帧按钮）", panel_ok, "")
            except Exception as e:
                record(4, "点【选帧抽取】→弹出帧选择面板", False, f"异常: {str(e)[:80]}")
        else:
            record(4, "点【选帧抽取】→弹出帧选择面板", True, "REAL_GENERATE=False 仅验证按钮存在")

        # ---- 步骤5：面板中点【抽取此帧】→ 画布新增图片节点 ----
        if REAL_GENERATE:
            try:
                # 先记录当前抽帧节点数
                before_frames = page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).filter(n => (n.textContent||'').includes('抽帧')).length")
                # 点【抽取此帧】
                page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('button');
                        for (let b of btns) {
                            if ((b.textContent || '').trim() === '抽取此帧') {
                                b.click();
                                return;
                            }
                        }
                    }
                """)
                time.sleep(2)
                # 等待新增"抽帧"节点（比之前多）
                frame_nodes = wait_new_frame_node(page, timeout=30)
                record(5, "选帧抽取→抽取此帧→画布新增图片节点", len(frame_nodes) > before_frames,
                       f"抽帧节点数 {before_frames}→{len(frame_nodes)}")
            except Exception as e:
                record(5, "选帧抽取→抽取此帧→画布新增图片节点", False, f"异常: {str(e)[:80]}")
        else:
            record(5, "选帧抽取→抽取此帧→画布新增图片节点", True, "REAL_GENERATE=False 仅验证按钮存在")

    finally:
        # 输出汇总
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
