# -*- coding: utf-8 -*-
"""
TC0004 自动化测试：剪辑工作台-时间轴编辑验证（v2，2026-10-31 重写）

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有至少 1 个片段（用户手动拖好，脚本不做拖拽）

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
      按源码确认的渲染顺序索引用 DOM el.click() 派发点击（不用鼠标点击，
      避免 Radix tooltip 打开状态拦截 click 导致业务 onClick 不执行）。
      索引（需先选中视频片段）：0撤销 1重做 2分割 3分割左 4分割右
      5提取音频 6复制 7定格 8删除 9倒放 10镜像 11旋转 12裁剪 13重选
    - 时间线片段：button.absolute.inset-0.size-full.flex.flex-col
    - 播放头：点击时间刻度行；实测兜底坐标 iframe 内 y≈656
      （点击 (560,656) 实测播放头移至 00:00:01:08 / 02:14 附近）
    - 镜像断言：右侧属性面板「缩放 X」变为 -1
    - 撤销/重做断言：循环撤销到片段数回到复制前，循环重做恢复
      （撤销/重做按栈：分割→删除→复制→镜像 依次回退/恢复）

重复运行注意：
    脚本会修改时间线状态（分割/删除/复制/镜像/撤销/重做叠加）。
    连续重复运行前，请将时间线重置为「1 个未分割、未镜像的片段」
    （在剪辑工作台删除全部片段后，重新从素材面板拖入一个视频片段），
    否则断言可能因起始状态不干净而失败。

测试步骤（与 TC0004_测试用例_修改版.md 一致）：
    1. 移动播放头到时间线中部 → 选中片段 → 点【分割元素】→ 断言片段数 +1
    2. 选中片段 → 点【删除元素】→ 断言片段数 -1
    3. 选中片段 → 点【复制元素】→ 断言片段数 +1
    4. 选中片段 → 点【水平镜像】→ 断言缩放 X = -1
    5. 选中片段 → 点【裁剪画面】→ 仅记录点击（当前版本无可见 UI 变化）
    6. 点【撤销】到片段数回退 → 断言；点【重做】恢复 → 断言
    7. 断言预览区正常显示（预览与时间轴同步）
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

# 时间线片段按钮（主轨片段，实测稳定选择器）
SEL_CLIP = "button.absolute.inset-0.size-full.flex.flex-col"
# 工具栏容器（iframe 内时间轴上方）
SEL_TOOLBAR = "div.flex.h-10.items-center.justify-between.border-b.px-2.py-1"
# 时间刻度行按钮（全宽，点击即移动播放头）
SEL_RULER = "button.relative.w-full.cursor-default.select-none"

# 工具栏按钮：tooltip 文本 → 源码顺序索引（兜底用，帧境 v2.0.14 实测）
TOOLTIP_INDEX = {
    "分割元素": 2, "分割并移除左侧": 3, "分割并移除右侧": 4,
    "提取音频": 5, "复制元素": 6, "删除元素": 8, "倒放": 9,
    "水平镜像": 10, "旋转90": 11, "裁剪画面": 12,
    "撤销": 0, "重做": 1,
}

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


def press_escape(page, times=1):
    try:
        for _ in range(times):
            page.keyboard.press("Escape")
            time.sleep(0.3)
    except Exception:
        pass


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
    """找到 opencut 剪辑工作台 iframe。"""
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
    """iframe 在 page 中的偏移，用于 page 级鼠标操作换算。"""
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
def get_tooltip_texts(editor):
    """读取当前 iframe 内所有 tooltip / popper 文本。"""
    try:
        return editor.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[role=tooltip], [data-radix-popper-content-wrapper]')
                .forEach(el => {
                    const t = (el.innerText || '').trim();
                    if (t) out.push(t);
                });
            return out;
        }""")
    except Exception:
        return []


def count_clips(editor):
    """统计时间线主轨片段数。"""
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


def select_first_clip(editor):
    """选中第一个主轨片段（DOM 点击，不依赖坐标）。"""
    try:
        editor.locator(SEL_CLIP).first.click(timeout=3000)
        time.sleep(STEP_WAIT)
        return True
    except Exception as e:
        log(f"  select_first_clip 异常: {e}")
        return False


def get_timecode(editor):
    """读取当前播放头时间码，如 00:00:02:14。"""
    try:
        return editor.evaluate("""() => {
            const els = document.querySelectorAll('*');
            for (const el of els) {
                const t = (el.innerText || '').trim();
                if (/^\\d{2}:\\d{2}:\\d{2}:\\d{2}$/.test(t)) return t;
            }
            return null;
        }""")
    except Exception:
        return None


def move_playhead_to_middle(page, editor, ox, oy, iw):
    """
    移动播放头到时间线约 40% 处，并验证时间码已离开 00:00:00:00。
    优先用时间标尺行（SEL_RULER）定位；若中心不在标尺区(600~720)或点击后
    时间码未变化，则用实测坐标兜底（iframe 内 y≈656 为时间标尺行，点击
    (560,656) 实测可移到 00:00:02:14）。
    返回 True 表示播放头已移动（时间码非 00:00:00:00）。
    """
    clicked = False
    try:
        ruler = editor.locator(SEL_RULER)
        if ruler.count() > 0:
            box = ruler.first.bounding_box()
            if box and 600 <= box["y"] + box["height"] / 2 <= 720:
                ty = box["y"] + box["height"] / 2
                tx = iw * 0.4
                page.mouse.click(ox + tx, oy + ty)
                log(f"[OK] 播放头点击 iframe({tx:.0f},{ty:.0f})")
                clicked = True
    except Exception as e:
        log(f"  move_playhead ruler 异常: {e}")
    if not clicked:
        tx = iw * 0.4
        page.mouse.click(ox + tx, oy + 656)
        log(f"[OK] 播放头点击(实测兜底) iframe({tx:.0f},656)")
        clicked = True
    time.sleep(STEP_WAIT)
    tc = get_timecode(editor)
    log(f"  播放头移动后时间码: {tc}")
    return bool(tc) and not tc.startswith("00:00:00:00")


def get_panel_inputs(editor):
    """
    读取属性面板输入框值（位置X/Y、缩放X/Y、旋转等）。
    采用全量读取后断言「-1」的方式判断镜像是否生效（镜像后缩放 X = -1，
    时间线/播放头等其他输入框值均为非负数，不会误判）。
    """
    try:
        return editor.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.top > 80 && r.height < 60) out.push(el.value);
            });
            return out;
        }""")
    except Exception:
        return []


def click_toolbar_btn(editor, tooltip_text, idx, timeout=10):
    """
    按渲染顺序索引点击工具栏按钮（需先选中视频片段，序列才含提取音频/倒放）：
        0撤销 1重做 2分割 3分割左 4分割右 5提取音频 6复制 7定格
        8删除 9倒放 10镜像 11旋转 12裁剪 13重选
    点击方式：DOM el.click() 派发（实测有效；不用鼠标点击，避免 tooltip
    打开状态拦截/遮挡导致的点击失效）。返回 True/False。
    """
    tb = editor.locator(SEL_TOOLBAR)
    if tb.count() == 0:
        log(f"[FAIL] 未找到工具栏容器「{SEL_TOOLBAR}」")
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
            log(f"[OK] 点击工具栏「{tooltip_text}」(button#{idx}, el.click)")
            time.sleep(STEP_WAIT)
            return True
        except Exception as e:
            log(f"  click_toolbar_btn 异常: {e}")
            time.sleep(0.3)
    log(f"[FAIL] 点击工具栏「{tooltip_text}」(button#{idx}) 失败")
    return False


# ==================== 主测试流程 ====================
def test_tc0004():
    log("=== TC0004：剪辑工作台-时间轴编辑验证 ===")
    errors = []

    # 连接
    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0004_workbench.png")

        ox, oy, iw, ih = get_iframe_offset(page, editor)
        log(f"[INFO] iframe 偏移=({ox:.0f},{oy:.0f}) 尺寸=({iw:.0f}x{ih:.0f})")

        # ── 前置检查：时间线有片段 ──
        cnt0 = count_clips(editor)
        log(f"  初始片段数: {cnt0}  时间码: {get_timecode(editor)}")
        if cnt0 == 0:
            log("[FAIL] 时间线无片段，请先在剪辑工作台手动放入至少 1 个片段")
            shot(page, "tc0004_noclip.png")
            sys.exit(1)

        # ── 步骤1：移动播放头 + 分割 ──
        log("\n=== 步骤1：移动播放头 + 分割 ===")
        if not move_playhead_to_middle(page, editor, ox, oy, iw):
            errors.append("播放头移动失败（未找到时间刻度行）")
        tc_after_move = get_timecode(editor)
        log(f"  播放头移动后时间码: {tc_after_move}")
        if not tc_after_move or tc_after_move.startswith("00:00:00:00"):
            errors.append(f"播放头移动未生效：时间码={tc_after_move}")

        select_first_clip(editor)
        before = count_clips(editor)
        if not click_toolbar_btn(editor, "分割元素", 2):
            errors.append("点击【分割元素】失败")
        after = count_clips(editor)
        log(f"  分割: {before} → {after}")
        if after != before + 1:
            errors.append(f"分割未生效：片段数 {before} → {after}")
        shot(page, "tc0004_after_split.png")

        # ── 步骤2：删除 ──
        log("\n=== 步骤2：删除 ===")
        select_first_clip(editor)
        before = count_clips(editor)
        if not click_toolbar_btn(editor, "删除元素", 8):
            errors.append("点击【删除元素】失败")
        after = count_clips(editor)
        log(f"  删除: {before} → {after}")
        if after != before - 1:
            errors.append(f"删除未生效：片段数 {before} → {after}")
        if after == 0:
            log("[FAIL] 删除后时间线为空，无法继续，请重置工程后重跑")
            shot(page, "tc0004_empty.png")
            sys.exit(1)
        shot(page, "tc0004_after_delete.png")

        # ── 步骤3：复制 ──
        log("\n=== 步骤3：复制 ===")
        select_first_clip(editor)
        copy_before = count_clips(editor)
        if not click_toolbar_btn(editor, "复制元素", 6):
            errors.append("点击【复制元素】失败")
        copy_after = count_clips(editor)
        log(f"  复制: {copy_before} → {copy_after}")
        if copy_after != copy_before + 1:
            errors.append(f"复制未生效：片段数 {copy_before} → {copy_after}")
        shot(page, "tc0004_after_copy.png")

        # ── 步骤4a：镜像 ──
        log("\n=== 步骤4：镜像 ===")
        select_first_clip(editor)
        if not click_toolbar_btn(editor, "水平镜像", 10):
            errors.append("点击【水平镜像】失败")
        vals = get_panel_inputs(editor)
        log(f"  镜像后右侧面板值: {vals}")
        if "-1" not in vals:
            errors.append(f"镜像未生效：右侧面板未出现缩放 X = -1（当前值 {vals}）")
        shot(page, "tc0004_after_mirror.png")

        # ── 步骤4b：裁剪画面 ──
        log("\n=== 步骤5：裁剪画面（仅记录） ===")
        select_first_clip(editor)
        if not click_toolbar_btn(editor, "裁剪画面", 12):
            errors.append("点击【裁剪画面】失败")
        vals_crop = get_panel_inputs(editor)
        log(f"  裁剪后右侧面板值: {vals_crop}")
        log("  [INFO] 当前版本(v2.0.14)点击【裁剪画面】无可见 UI 变化，仅记录点击状态，不做效果断言")
        shot(page, "tc0004_after_crop.png")

        # ── 步骤5：撤销 / 重做 ──
        log("\n=== 步骤6：撤销 / 重做 ===")
        # 循环撤销，直到片段数回到复制前
        undo_steps = 0
        for _ in range(8):
            if count_clips(editor) == copy_before:
                break
            if not click_toolbar_btn(editor, "撤销", 0):
                log("  [WARN] 撤销按钮不可用")
                break
            undo_steps += 1
        c_undo = count_clips(editor)
        log(f"  撤销 {undo_steps} 次 → 片段数 {c_undo}（复制前为 {copy_before}）")
        if c_undo != copy_before:
            errors.append(f"撤销未按栈回退：期望 {copy_before}，实际 {c_undo}")
        shot(page, "tc0004_after_undo.png")

        # 循环重做：恢复到「片段数=复制后 且 镜像属性恢复(-1)」才停止
        # （撤销把 复制+镜像 都回退了，重做也需按栈恢复两者）
        redo_steps = 0
        for _ in range(8):
            c = count_clips(editor)
            select_first_clip(editor)
            v = get_panel_inputs(editor)
            if c == copy_after and "-1" in v:
                break
            if not click_toolbar_btn(editor, "重做", 1):
                log("  [WARN] 重做按钮不可用")
                break
            redo_steps += 1
        c_redo = count_clips(editor)
        select_first_clip(editor)
        vals_redo = get_panel_inputs(editor)
        log(f"  重做 {redo_steps} 次 → 片段数 {c_redo}（复制后为 {copy_after}）")
        if c_redo != copy_after:
            errors.append(f"重做未恢复：期望 {copy_after}，实际 {c_redo}")
        # 重做后镜像也应恢复（缩放 X = -1）
        log(f"  重做后右侧面板值: {vals_redo}")
        if "-1" not in vals_redo:
            errors.append(f"重做后镜像属性未恢复（缩放 X 未回到 -1，当前 {vals_redo}）")
        shot(page, "tc0004_after_redo.png")

        # ── 步骤6：预览与时间轴同步 ──
        log("\n=== 步骤7：预览与时间轴同步 ===")
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
        shot(page, "tc0004_final.png")
        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0004，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0004 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0004_error.png")
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
    test_tc0004()

