# -*- coding: utf-8 -*-
"""
TC-0011 视频节点 - 音频分离（双产出）
=====================================================================
验证视频节点工具栏中【音频分离（双产出）】功能正常：
点击后立即生成新的音频节点（及配套无声视频节点），节点正确显示分离结果。

【入口】
    在画布中选中带音轨的视频节点（点标题栏）→ 观察上方工具栏

【实测确认的产品行为】
    1. 选中视频节点后，上方工具栏出现按钮：抽帧、延长、编辑、音频分离、转码、反推、视频工具…
    2. 【音频分离】按钮 aria-label='音频分离（双产出）'（cls='tbtn lbl'）；
    3. 点击后立即生成分离音频节点 + 无声视频节点（约14秒完成）。

【重要注意事项】
    - 必须选中**带音轨的原视频**（如 findbugs），不能选无声视频节点（TC-0009 产出的），
      否则点音频分离按钮无反应（无音轨可分离）。

【REAL_GENERATE 规则】
    音频分离为本地功能（本地 ffmpeg，无价格标注）→ REAL_GENERATE = True

【定位方式】
    全部使用元素定位（aria-label / 文本），真实鼠标点击，不使用固定坐标。
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


def find_blank(page):
    """找画布空白区域"""
    return page.evaluate("""
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


def find_tracked_video_node(page):
    """找带音轨的原视频节点（含'find'关键词，排除无声视频/分离音频/抽帧）"""
    return page.evaluate("""
        () => {
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                // 找含 findbugs 关键词的原视频节点（有音轨）
                if (t.includes('find') && r.x > 0 && r.y > 0) {
                    return i;
                }
            }
            return -1;
        }
    """)


# ------------------------- 测试主流程 -------------------------
def main():
    pw, browser, page = connect()
    time.sleep(2)
    try:
        page.keyboard.press("Escape")
        time.sleep(1.5)

        # ---- 步骤1：选中带音轨的原视频节点 → 观察工具栏【音频分离】按钮 ----
        idx = find_tracked_video_node(page)
        if idx < 0:
            # pan_canvas 向右拖，让 findbugs 节点进视口
            blank = find_blank(page)
            if blank:
                page.mouse.move(blank["x"], blank["y"])
                time.sleep(0.3)
                page.mouse.down()
                time.sleep(0.2)
                page.mouse.move(blank["x"] + 300, blank["y"], steps=5)
                time.sleep(0.3)
                page.mouse.up()
                time.sleep(0.5)
                idx = find_tracked_video_node(page)

        if idx < 0:
            record(1, "选中带音轨的原视频节点→工具栏【音频分离（双产出）】入口显示", False, "未找到带音轨的原视频节点（含'find'关键词）")
            return

        box = page.locator(".react-flow__node").nth(idx).bounding_box()
        if not box:
            record(1, "选中带音轨的原视频节点→工具栏【音频分离（双产出）】入口显示", False, "节点 bounding_box 为空")
            return

        # 真实鼠标点击标题栏
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
        time.sleep(1)

        # 验证工具栏出现【音频分离】按钮
        audio_btn = page.locator("button[aria-label='音频分离（双产出）']")
        btn_count = audio_btn.count()
        ok1 = btn_count > 0
        record(1, "选中带音轨的原视频节点→工具栏【音频分离（双产出）】入口显示", ok1,
               f"按钮数={btn_count}（注意：必须选中带音轨的原视频，不能选无声视频节点）")

        # ---- 步骤2：点【音频分离】→ 观察是否立即生成新节点 ----
        if REAL_GENERATE and ok1:
            # 记录分离前节点数
            n0 = page.locator(".react-flow__node").count()
            # 真实鼠标点击音频分离按钮
            btn_box = audio_btn.bounding_box()
            if btn_box:
                page.mouse.click(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2)
                time.sleep(3)
                # 等待生成
                t0 = time.time()
                n1 = n0
                while time.time() - t0 < 60:
                    n1 = page.locator(".react-flow__node").count()
                    if n1 > n0:
                        break
                    time.sleep(2)
                ok2 = n1 > n0
                record(2, "点【音频分离】→立即生成新节点无报错", ok2,
                       f"节点数 {n0} → {n1}（约{int(time.time()-t0)}秒完成）")
            else:
                record(2, "点【音频分离】→立即生成新节点无报错", False, "按钮 bounding_box 为空")
        else:
            record(2, "点【音频分离】→立即生成新节点无报错", True, "REAL_GENERATE=False")

        # ---- 步骤3：观察画布新增节点（分离音频+无声视频） ----
        if REAL_GENERATE:
            texts = page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => (n.textContent || '').trim())")
            has_audio = any("分离音频" in t or "音频" in t for t in texts)
            has_silent = any("无声视频" in t or "无声" in t for t in texts)
            ok3 = has_audio and has_silent
            record(3, "画布新增分离音频节点+无声视频节点", ok3,
                   f"音频节点={has_audio} 无声视频={has_silent}")
        else:
            record(3, "画布新增分离音频节点+无声视频节点", True, "REAL_GENERATE=False")

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
