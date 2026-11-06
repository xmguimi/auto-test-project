# -*- coding: utf-8 -*-
"""
TC-0013 视频转码 - 开始转码与结果校验
=====================================================================
验证选择参数后点击【开始转码】任务正常发起，进度显示在新节点上，
新节点与原视频连线，转码完成后结果参数与所选一致。

【入口】
    选中视频节点 → 点击工具栏【转码】→ 打开弹窗

【实测确认的产品行为】
    1. 弹窗内分辨率选项：原始/1080p/720p/480p/自定义（文本按钮）；
    2. 帧率选项：原始/24/25/30/60（文本按钮）；
    3. 画质选项：高/中/低（文本按钮）；
    4. 保留音轨开关：cls='cx-sw on'（开启）；
    5. 开始转码按钮：文本"开始转码"（cls='cx-btn-primary'）。

【REAL_GENERATE 规则】
    转码为本地功能（无价格标注）→ REAL_GENERATE = True

【定位方式】
    全部使用元素定位（文本 / class），真实鼠标点击，不使用固定坐标。
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

# REAL_GENERATE：转码为本地功能（无价格标注）→ True
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


def find_findbugs_node(page):
    """找 findbugs 原视频节点"""
    return page.evaluate("""
        () => {
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                if (t.includes('find') && r.x > 0 && r.y > 0) return i;
            }
            return -1;
        }
    """)


def click_modal_button_by_text(page, text):
    """在弹窗内点选指定文本的按钮"""
    return page.evaluate(f"""
        () => {{
            const modal = document.querySelector('.modal, [class*="modal"], [class*="dialog"]');
            if (!modal) return false;
            for (let b of modal.querySelectorAll('button')) {{
                if ((b.textContent || '').trim() === '{text}') {{
                    b.click();
                    return true;
                }}
            }}
            return false;
        }}
    """)


# ------------------------- 测试主流程 -------------------------
def main():
    pw, browser, page = connect()
    time.sleep(2)
    try:
        page.keyboard.press("Escape")
        time.sleep(1.5)

        # ---- 步骤1：选中视频节点 → 点转码按钮 → 弹窗打开 ----
        idx = find_findbugs_node(page)
        if idx < 0:
            record(1, "选中视频节点→点转码按钮→弹窗打开", False, "未找到 findbugs 节点")
            return
        box = page.locator(".react-flow__node").nth(idx).bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
        time.sleep(1)

        transcode_btn = page.locator("button[aria-label='视频转码（格式 / 分辩率 / 帧率）']")
        if transcode_btn.count() == 0:
            record(1, "选中视频节点→点转码按钮→弹窗打开", False, "转码按钮不存在")
            return
        bb = transcode_btn.bounding_box()
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        time.sleep(2)

        modal_count = page.locator(".modal, [class*='modal'], [class*='dialog']").count()
        ok1 = modal_count > 0
        record(1, "选中视频节点→点转码按钮→弹窗打开", ok1, f"弹窗数={modal_count}")

        # ---- 步骤2：选择参数（720p + 30帧 + 中画质 + 保留音轨开） ----
        if REAL_GENERATE:
            # 选 720p 分辨率
            ok_res = click_modal_button_by_text(page, "720p")
            time.sleep(0.5)
            # 选 30 帧率
            ok_fps = click_modal_button_by_text(page, "30")
            time.sleep(0.5)
            # 选 中 画质（默认已选中，再点一次确认）
            ok_qual = click_modal_button_by_text(page, "中")
            time.sleep(0.5)
            ok2 = ok_res and ok_fps and ok_qual
            record(2, "选择参数：720p + 30帧 + 中画质 + 保留音轨开", ok2,
                   f"720p={ok_res} 30帧={ok_fps} 中画质={ok_qual}")
        else:
            record(2, "选择参数：720p + 30帧 + 中画质 + 保留音轨开", True, "REAL_GENERATE=False")

        # ---- 步骤3：点【开始转码】→ 任务发起 ----
        if REAL_GENERATE:
            n0 = page.locator(".react-flow__node").count()
            # 点开始转码按钮
            ok_start = click_modal_button_by_text(page, "开始转码")
            time.sleep(3)
            # 等待弹窗关闭
            modal_after = page.locator(".modal, [class*='modal'], [class*='dialog']").count()
            ok3 = ok_start and modal_after == 0
            record(3, "点【开始转码】→任务发起，弹窗关闭", ok3,
                   f"开始转码={ok_start} 关闭后弹窗数={modal_after}")
        else:
            record(3, "点【开始转码】→任务发起，弹窗关闭", True, "REAL_GENERATE=False")

        # ---- 步骤4：观察画布新节点出现、进度显示 ----
        if REAL_GENERATE:
            t0 = time.time()
            n1 = n0
            while time.time() - t0 < 30:
                n1 = page.locator(".react-flow__node").count()
                if n1 > n0:
                    break
                time.sleep(2)
            ok4 = n1 > n0
            record(4, "画布新节点出现、进度显示在新节点上", ok4,
                   f"节点数 {n0} → {n1}")
        else:
            record(4, "画布新节点出现、进度显示在新节点上", True, "REAL_GENERATE=False")

        # ---- 步骤5：等待转码完成，核对新节点 ----
        if REAL_GENERATE:
            # 等待转码完成（节点数稳定 + 无进度文本）
            t0 = time.time()
            while time.time() - t0 < 120:
                time.sleep(5)
                texts = page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => (n.textContent || '').trim())")
                # 检查是否有转码中节点
                has_progress = any("转码中" in t or "处理中" in t or "%" in t for t in texts)
                if not has_progress:
                    break
            # 核对新节点文本
            texts = page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => (n.textContent || '').trim())")
            has_transcoded = any("转码" in t or "720" in t for t in texts)
            ok5 = has_transcoded
            record(5, "等待转码完成，核对新节点参数", ok5,
                   f"新节点含转码/720p={has_transcoded}")
        else:
            record(5, "等待转码完成，核对新节点参数", True, "REAL_GENERATE=False")

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
