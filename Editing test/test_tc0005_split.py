# -*- coding: utf-8 -*-
"""
TC0005 自动化测试：剪辑工作台-分割（分割 / 分割并移除左侧 / 分割并移除右侧）

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有至少 1 个视频片段（用户手动拖好，脚本不做拖拽）

运行前置：
    pip install playwright requests
    python -m playwright install chromium

环境变量（可选，换电脑时用）：
    FJ_CDP_HOST         CDP 主机，默认 localhost
    FJ_CDP_PORT         CDP 端口，默认 9222
    FJ_WINDOW_TITLE     帧境窗口标题关键字，默认「帧境」
    FJ_SHOT_DIR         截图目录，默认 ./screenshots

定位策略（已实测，帧境 v2.0.14）：
    - 工具栏按钮无 title / aria-label / 文本（仅 SVG 图标）：
      按源码确认的渲染顺序索引用 DOM el.click() 派发点击。
      索引（需先选中视频片段）：0撤销 1重做 2分割 3分割左 4分割右 5提取音频
      6复制 7定格 8删除 9倒放 10镜像 11旋转 12裁剪 13重选
    - 时间线片段：button.absolute.inset-0.size-full.flex.flex-col
    - 播放头：点击时间标尺行（实测兜底 iframe 内 y≈656）

测试步骤（与 TC0005_测试用例_修改版.md 一致）：
    1. 移动播放头到约 33% 处 → 选中片段 → 点【分割元素】→ 断言片段数 +1
    2. 移动播放头到约 55% 处（右段内）→ 选中最后一段 → 点【分割并移除左侧】
       → 断言总时长缩短（选中片段左半被裁掉）
    3. 移动播放头到约 50% 处（剩余片段内）→ 选中最后一段 → 点【分割并移除右侧】
       → 断言总时长进一步缩短（选中片段右半被裁掉）
    4. 断言预览区正常显示

重复运行注意：
    脚本会改动时间线状态（分割/裁剪叠加）。连续重复运行前，请将时间线重置为
    「1 个未分割的片段」（在剪辑工作台删除全部片段后，重新从素材面板拖入视频）。
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ==================== 配置区 ====================
CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
WINDOW_TITLE_KEYWORD = os.getenv("FJ_WINDOW_TITLE", "帧境")
SHOT_DIR = Path(os.getenv("FJ_SHOT_DIR", "screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

EDITOR_FRAME_HINTS = ["opencut", "editing", "clip"]

SEL_CLIP = "button.absolute.inset-0.size-full.flex.flex-col"
SEL_TOOLBAR = "div.flex.h-10.items-center.justify-between.border-b.px-2.py-1"
SEL_RULER = "button.relative.w-full.cursor-default.select-none"

# 工具栏按钮索引（选中视频片段时，源码顺序 + 实测确认）
IDX_SPLIT = 2          # 分割元素
IDX_REMOVE_LEFT = 3    # 分割并移除左侧
IDX_REMOVE_RIGHT = 4  # 分割并移除右侧

OPEN_TIMEOUT = 20
STEP_WAIT = 0.8


# ==================== 基础工具 ====================
def log(msg):
    print(msg, flush=True)


def shot(page, name):
    try:
        p = SHOT_DIR / name
        page.screenshot(path=str(p))
        log(f"[SHOT] {p}")
    except Exception as e:
        log(f"[SHOT-FAIL] {name}: {e}")


def is_cdp_ready(host=CDP_HOST, port=CDP_PORT):
    try:
        r = requests.get(f"http://{host}:{port}/json/version", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def connect():
    if not is_cdp_ready():
        raise RuntimeError(
            f"CDP 未就绪：请确认帧境已带 --remote-debugging-port={CDP_PORT} 启动"
        )
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    pages = browser.contexts[0].pages
    target = None
    for p in pages:
        try:
            if WINDOW_TITLE_KEYWORD in (p.title() or ""):
                target = p
                break
        except Exception:
            pass
    if not target:
        target = pages[0]
    log(f"[OK] 已连接主页面: title='{target.title()}'")
    return pw, browser, target


def find_editor_frame(page, timeout=OPEN_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        for f in page.frames:
            try:
                if f == page.main_frame:
                    continue
                url = (f.url or "").lower()
                if any(k in url for k in EDITOR_FRAME_HINTS):
                    log(f"[OK] 命中剪辑工作台 iframe: {f.url}")
                    return f
            except Exception:
                pass
        time.sleep(0.4)
    raise RuntimeError("找不到剪辑工作台 iframe（请确认已进入剪辑工作台）")


def get_iframe_offset(page, editor_frame):
    try:
        iframes = page.locator("iframe")
        for i in range(iframes.count()):
            el = iframes.nth(i)
            src = (el.get_attribute("src") or "").lower()
            if any(k in src for k in EDITOR_FRAME_HINTS):
                box = el.bounding_box()
                if box:
                    return box["x"], box["y"], box["width"], box["height"]
        box = iframes.first.bounding_box()
        if box:
            return box["x"], box["y"], box["width"], box["height"]
    except Exception as e:
        log(f"  get_iframe_offset 异常: {e}")
    return 0, 0, 0, 0


# ==================== 工作台内定位 ====================
def count_clips(editor):
    try:
        return editor.evaluate(f"""() => {{
            const vh = window.innerHeight;
            const els = document.querySelectorAll('{SEL_CLIP}');
            let n = 0;
            els.forEach(el => {{
                const r = el.getBoundingClientRect();
                if (r.top > vh * 0.55 && r.width > 50) n++;
            }});
            return n;
        }}""")
    except Exception as e:
        log(f"  count_clips 异常: {e}")
        return 0


def select_clip(editor, index=0):
    """选中第 index 个主轨片段（0=第一个，-1=最后一个）。"""
    try:
        loc = editor.locator(SEL_CLIP)
        if index < 0:
            loc.nth(loc.count() + index).click(timeout=3000)
        else:
            loc.nth(index).click(timeout=3000)
        time.sleep(STEP_WAIT)
        return True
    except Exception as e:
        log(f"  select_clip({index}) 异常: {e}")
        return False


def get_all_timecodes(editor):
    """读取 iframe 内所有时间码字符串（格式 HH:MM:SS:FF），按出现顺序。"""
    try:
        return editor.evaluate("""() => {
            const res = [];
            document.querySelectorAll('*').forEach(el => {
                const t = (el.innerText || '').trim();
                if (/^\\d{2}:\\d{2}:\\d{2}:\\d{2}$/.test(t) && !res.includes(t)) res.push(t);
            });
            return res;
        }""")
    except Exception:
        return []


def get_playhead_tc(editor):
    tcs = get_all_timecodes(editor)
    return tcs[0] if tcs else None


def get_total_duration(editor):
    """总时长 = 时间码数组中最后一个（播放头在前，总时长在后）。"""
    tcs = get_all_timecodes(editor)
    return tcs[-1] if len(tcs) >= 2 else (tcs[0] if tcs else None)


def tc_to_seconds(tc):
    """HH:MM:SS:FF → 秒（粗略，FF 按 30fps 换算，仅用于比较大小）。"""
    try:
        h, m, s, f = tc.split(":")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(f) / 30.0
    except Exception:
        return 0


def move_playhead(page, editor, ox, oy, iw, pct):
    """移动播放头到时间线 pct 比例处，返回播放头时间码。"""
    tx = iw * pct
    page.mouse.click(ox + tx, oy + 656)
    time.sleep(STEP_WAIT)
    tc = get_playhead_tc(editor)
    log(f"[OK] 播放头→{pct*100:.0f}% iframe({tx:.0f},656) 时间码={tc}")
    return tc


def click_toolbar_btn(editor, name, idx, timeout=10):
    """按索引点击工具栏按钮（DOM el.click 派发）。"""
    tb = editor.locator(SEL_TOOLBAR)
    if tb.count() == 0:
        log(f"[FAIL] 未找到工具栏容器")
        return False
    tb = tb.first
    btns = tb.locator("button")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if btns.count() <= idx:
                time.sleep(0.3)
                continue
            b = btns.nth(idx)
            if b.evaluate("el => el.disabled"):
                time.sleep(0.3)
                continue
            b.evaluate("el => el.click()")
            log(f"[OK] 点击工具栏「{name}」(button#{idx}, el.click)")
            time.sleep(STEP_WAIT)
            return True
        except Exception as e:
            log(f"  click_toolbar_btn 异常: {e}")
            time.sleep(0.3)
    log(f"[FAIL] 点击工具栏「{name}」(button#{idx}) 失败")
    return False


# ==================== 主测试流程 ====================
def test_tc0005():
    log("=== TC0005：剪辑工作台-分割（分割/移除左侧/移除右侧）===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0005_workbench.png")

        ox, oy, iw, ih = get_iframe_offset(page, editor)
        log(f"[INFO] iframe 偏移=({ox:.0f},{oy:.0f}) 尺寸=({iw:.0f}x{ih:.0f})")

        # ── 前置检查 ──
        cnt0 = count_clips(editor)
        dur0 = get_total_duration(editor)
        log(f"  初始片段数: {cnt0}  总时长: {dur0}")
        if cnt0 == 0:
            log("[FAIL] 时间线无片段，请先在剪辑工作台手动放入至少 1 个视频片段")
            shot(page, "tc0005_noclip.png")
            sys.exit(1)

        # ── 步骤1：分割 ──
        log("\n=== 步骤1：分割 ===")
        move_playhead(page, editor, ox, oy, iw, 0.33)
        select_clip(editor, 0)
        before_split = count_clips(editor)
        if not click_toolbar_btn(editor, "分割元素", IDX_SPLIT):
            errors.append("点击【分割元素】失败")
        after_split = count_clips(editor)
        log(f"  分割: {before_split} → {after_split}")
        if after_split != before_split + 1:
            errors.append(f"分割未生效：片段数 {before_split} → {after_split}（期望 +1）")
        shot(page, "tc0005_after_split.png")

        # ── 步骤2：分割并移除左侧 ──
        log("\n=== 步骤2：分割并移除左侧 ===")
        dur_before_left = get_total_duration(editor)
        move_playhead(page, editor, ox, oy, iw, 0.55)
        select_clip(editor, -1)  # 选中最后一段（右段）
        if not click_toolbar_btn(editor, "分割并移除左侧", IDX_REMOVE_LEFT):
            errors.append("点击【分割并移除左侧】失败")
        dur_after_left = get_total_duration(editor)
        n_after_left = count_clips(editor)
        log(f"  移除左侧: 总时长 {dur_before_left} → {dur_after_left}  片段数 {n_after_left}")
        if not dur_before_left or not dur_after_left:
            errors.append(f"移除左侧后无法读取总时长（before={dur_before_left}, after={dur_after_left}）")
        elif tc_to_seconds(dur_after_left) >= tc_to_seconds(dur_before_left):
            errors.append(f"移除左侧未生效：总时长未缩短（{dur_before_left} → {dur_after_left}）")
        shot(page, "tc0005_after_remove_left.png")

        # ── 步骤3：分割并移除右侧 ──
        log("\n=== 步骤3：分割并移除右侧 ===")
        dur_before_right = get_total_duration(editor)
        move_playhead(page, editor, ox, oy, iw, 0.50)
        select_clip(editor, -1)  # 选中最后一段
        if not click_toolbar_btn(editor, "分割并移除右侧", IDX_REMOVE_RIGHT):
            errors.append("点击【分割并移除右侧】失败")
        dur_after_right = get_total_duration(editor)
        n_after_right = count_clips(editor)
        log(f"  移除右侧: 总时长 {dur_before_right} → {dur_after_right}  片段数 {n_after_right}")
        if not dur_before_right or not dur_after_right:
            errors.append(f"移除右侧后无法读取总时长（before={dur_before_right}, after={dur_after_right}）")
        elif tc_to_seconds(dur_after_right) >= tc_to_seconds(dur_before_right):
            errors.append(f"移除右侧未生效：总时长未缩短（{dur_before_right} → {dur_after_right}）")
        shot(page, "tc0005_after_remove_right.png")

        # ── 步骤4：预览区检查 ──
        log("\n=== 步骤4：预览与时间轴同步 ===")
        preview_ok = False
        try:
            preview_ok = editor.evaluate("""() => {
                const body = document.body.innerText || '';
                return body.includes('画质') || body.includes('比例');
            }""")
        except Exception as e:
            log(f"  预览检查异常: {e}")
        if preview_ok:
            log("  [OK] 预览区正常显示（含画质/比例控制）")
        else:
            errors.append("预览区未检测到（预览与时间轴可能未同步）")

        # ── 汇总 ──
        shot(page, "tc0005_final.png")
        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0005，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0005 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0005_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            browser.close()
            pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    test_tc0005()
