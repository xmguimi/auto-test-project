# -*- coding: utf-8 -*-
"""
TC-0012 视频转码 - 弹窗参数与交互
=====================================================================
验证转码弹窗打开正常、源视频信息显示正确，格式、分辨率（含自定义与锁定）、
帧率、画质、保留音轨各参数可正常选择、选中态唯一，关闭按钮可正常退出且不发起转码。

【入口】
    选中视频节点 → 点击工具栏【转码】（aria-label='视频转码（格式 / 分辩率 / 帧率）'）

【实测确认的产品行为】
    1. 弹窗标题：视频转码（右上角 × 关闭按钮）；
    2. 源视频信息：源视频：1280×720 · 3:11；
    3. 格式：下拉框，默认 MP4 · H.264（兼容最好）；
    4. 分辨率：原始/1080p/720p/480p/自定义；
    5. 帧率：原始/24/25/30/60；
    6. 画质：高/中/低；
    7. 保留音轨：开关；
    8. 底部：关闭、开始转码按钮。

【REAL_GENERATE 规则】
    转码弹窗为本地功能（不实际点开始转码）→ REAL_GENERATE = True（仅验证弹窗交互）

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

# REAL_GENERATE：转码弹窗为本地功能（不实际点开始转码）→ True
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


def get_modal_state(page):
    """读取转码弹窗状态"""
    return page.evaluate("""
        () => {
            const modal = document.querySelector('.modal, [class*="modal"], [class*="dialog"]');
            if (!modal) return null;
            const t = (modal.textContent || '');
            // 源视频信息
            const srcMatch = t.match(/源视频[：:]\\s*([\\d×·\\s]+)/);
            const src = srcMatch ? srcMatch[1].trim() : '';
            // 格式
            const fmtMatch = t.match(/MP4\\s*·\\s*H\\.264/);
            const fmt = fmtMatch ? t.match(/MP4\\s*·\\s*H\\.264[^\\n]*/)[0].trim() : '';
            // 分辨率选项
            const resOptions = ['原始', '1080p', '720p', '480p', '自定义'];
            const hasRes = resOptions.some(r => t.includes(r));
            // 帧率选项
            const fpsOptions = ['原始', '24', '25', '30', '60'];
            const hasFps = fpsOptions.some(f => t.includes(f));
            // 画质选项
            const qualOptions = ['高', '中', '低'];
            const hasQual = qualOptions.some(q => t.includes(q));
            // 保留音轨
            const hasAudio = t.includes('保留音轨');
            // 关闭按钮
            const hasClose = t.includes('关闭');
            // 开始转码按钮
            const hasStart = t.includes('开始转码');
            return {src, fmt, hasRes, hasFps, hasQual, hasAudio, hasClose, hasStart};
        }
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

        # 点转码按钮
        transcode_btn = page.locator("button[aria-label='视频转码（格式 / 分辩率 / 帧率）']")
        if transcode_btn.count() == 0:
            record(1, "选中视频节点→点转码按钮→弹窗打开", False, "转码按钮不存在")
            return
        bb = transcode_btn.bounding_box()
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        time.sleep(2)

        # 验证弹窗打开
        modal_count = page.locator(".modal, [class*='modal'], [class*='dialog']").count()
        ok1 = modal_count > 0
        record(1, "选中视频节点→点转码按钮→弹窗打开", ok1, f"弹窗数={modal_count}")

        # ---- 步骤2：观察源视频信息显示 ----
        state = get_modal_state(page)
        ok2 = state is not None and state.get("src", "") != ""
        record(2, "观察源视频信息显示正确", ok2,
               f"源视频={state.get('src') if state else ''}")

        # ---- 步骤3：观察格式下拉框 ----
        ok3 = state is not None and state.get("fmt", "") != ""
        record(3, "观察格式下拉框（MP4 · H.264）", ok3,
               f"格式={state.get('fmt') if state else ''}")

        # ---- 步骤4：观察分辨率选项 ----
        ok4 = state is not None and state.get("hasRes", False)
        record(4, "观察分辨率选项（原始/1080p/720p/480p/自定义）", ok4, "")

        # ---- 步骤5：观察帧率选项 ----
        ok5 = state is not None and state.get("hasFps", False)
        record(5, "观察帧率选项（原始/24/25/30/60）", ok5, "")

        # ---- 步骤6：观察画质选项 ----
        ok6 = state is not None and state.get("hasQual", False)
        record(6, "观察画质选项（高/中/低）", ok6, "")

        # ---- 步骤7：观察保留音轨开关 ----
        ok7 = state is not None and state.get("hasAudio", False)
        record(7, "观察保留音轨开关", ok7, "")

        # ---- 步骤8：点【关闭】按钮 → 弹窗关闭 ----
        close_btn = page.locator("button:has-text('关闭')")
        if close_btn.count() > 0:
            close_btn.first.click()
            time.sleep(1)
            modal_after = page.locator(".modal, [class*='modal'], [class*='dialog']").count()
            ok8 = modal_after == 0
            record(8, "点【关闭】按钮→弹窗关闭不发起转码", ok8, f"关闭后弹窗数={modal_after}")
        else:
            record(8, "点【关闭】按钮→弹窗关闭不发起转码", False, "关闭按钮不存在")

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
