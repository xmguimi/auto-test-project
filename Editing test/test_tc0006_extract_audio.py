# -*- coding: utf-8 -*-
"""
TC0006 自动化测试：剪辑工作台-提取音频

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
    - 工具栏按钮 idx5 = 提取音频（选中视频片段时）
    - 时间线片段：button.absolute.inset-0.size-full.flex.flex-col
    - 视频片段 y≈671 h≈65；音频片段 y≈742 h≈50（在视频轨下方）

测试步骤：
    1. 选中主轨视频片段
    2. 点【提取音频】
    3. 断言：片段数 +1（视频片段保留 + 新增音频片段），音频片段在视频片段下方
    4. 断言：预览区正常、无报错弹窗
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
IDX_EXTRACT_AUDIO = 5

OPEN_TIMEOUT = 20
STEP_WAIT = 0.8


def log(msg):
    print(msg, flush=True)


def shot(page, name):
    try:
        p = SHOT_DIR / name
        page.screenshot(path=str(p))
        log(f"[SHOT] {p}")
    except Exception as e:
        log(f"[SHOT-FAIL] {name}: {e}")


def is_cdp_ready():
    try:
        r = requests.get(f"http://{CDP_HOST}:{CDP_PORT}/json/version", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def connect():
    if not is_cdp_ready():
        raise RuntimeError(f"CDP 未就绪：请确认帧境已带 --remote-debugging-port={CDP_PORT} 启动")
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


def get_clip_rects(editor):
    """返回所有主轨片段的位置和尺寸。"""
    try:
        return editor.evaluate(f"""() => {{
            const vh = window.innerHeight;
            const els = document.querySelectorAll('{SEL_CLIP}');
            const out = [];
            els.forEach(el => {{
                const r = el.getBoundingClientRect();
                if (r.top > vh * 0.55 && r.width > 50) {{
                    out.push({{x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), text: (el.innerText||'').trim().slice(0,20)}});
                }}
            }});
            return out;
        }}""")
    except Exception as e:
        log(f"  get_clip_rects 异常: {e}")
        return []


def get_dialogs(editor):
    try:
        return editor.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[role=dialog], [role=alertdialog], [data-radix-popper-content-wrapper], .modal').forEach(el => {
                const t = (el.innerText||'').trim();
                if (t) out.push(t.slice(0, 100));
            });
            return out;
        }""")
    except Exception:
        return []


def click_toolbar_btn(editor, name, idx, timeout=10):
    tb = editor.locator(SEL_TOOLBAR)
    if tb.count() == 0:
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
        except Exception:
            time.sleep(0.3)
    return False


def test_tc0006():
    log("=== TC0006：剪辑工作台-提取音频 ===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0006_workbench.png")

        clips_before = get_clip_rects(editor)
        log(f"  初始片段数: {len(clips_before)}")
        for c in clips_before:
            log(f"    y={c['y']} h={c['h']} text={c['text']!r}")
        if len(clips_before) == 0:
            log("[FAIL] 时间线无片段，请先手动放入至少 1 个视频片段")
            sys.exit(1)

        # 选中第一个片段（视频片段）
        editor.locator(SEL_CLIP).first.click(timeout=3000)
        time.sleep(STEP_WAIT)

        # 点提取音频
        if not click_toolbar_btn(editor, "提取音频", IDX_EXTRACT_AUDIO):
            errors.append("点击【提取音频】失败")
        # 等待音频分离完成
        time.sleep(2.0)

        clips_after = get_clip_rects(editor)
        log(f"\n  提取后片段数: {len(clips_after)}")
        for c in clips_after:
            log(f"    y={c['y']} h={c['h']} text={c['text']!r}")
        shot(page, "tc0006_after_extract.png")

        # 断言1：片段数 +1
        if len(clips_after) != len(clips_before) + 1:
            errors.append(f"提取音频后片段数 {len(clips_before)} → {len(clips_after)}（期望 +1）")

        # 断言2：视频片段保留（y≈671 的片段仍在）
        video_before = min(clips_before, key=lambda c: c["y"])
        video_after = [c for c in clips_after if c["y"] == video_before["y"]]
        if len(video_after) == 0:
            errors.append("视频片段在提取音频后丢失")

        # 断言3：新增音频片段在视频片段下方（y 更大）
        if len(clips_after) >= 2:
            ys = sorted([c["y"] for c in clips_after])
            if ys[1] <= ys[0]:
                errors.append(f"未检测到下方音频片段（y 排序={ys}）")
            else:
                audio_clip = [c for c in clips_after if c["y"] == ys[1]][0]
                log(f"  [OK] 检测到音频片段: y={audio_clip['y']} h={audio_clip['h']}")
        else:
            errors.append("未检测到新增音频片段")

        # 断言4：无报错弹窗
        dialogs = get_dialogs(editor)
        if dialogs:
            errors.append(f"出现弹窗/报错: {dialogs}")

        # 断言5：预览区正常
        preview_ok = False
        try:
            preview_ok = editor.evaluate("() => { const b = document.body.innerText||''; return b.includes('画质') || b.includes('比例'); }")
        except Exception:
            pass
        if preview_ok:
            log("  [OK] 预览区正常显示")
        else:
            errors.append("预览区未检测到")

        shot(page, "tc0006_final.png")
        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0006，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0006 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0006_error.png")
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
    test_tc0006()
