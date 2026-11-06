# -*- coding: utf-8 -*-
"""
TC0007 自动化测试：剪辑工作台-倒放

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有至少 1 个视频片段（用户手动拖好，脚本不做拖拽）

运行前置：
    pip install playwright requests
    python -m playwright install chromium

环境变量（可选，换电脑时用）：
    FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR

定位策略（已实测，帧境 v2.0.14）：
    - 工具栏按钮 idx9 = 倒放（选中视频片段时）
    - 倒放触发进度弹窗「片段倒放中…」，约 3 秒完成（17%→50%→100%）
    - 倒放成功后片段文本变为「原名（倒放）.mp4」

测试步骤：
    1. 选中主轨视频片段，记录片段名
    2. 点【倒放】
    3. 断言：出现进度弹窗并最终消失
    4. 断言：片段名包含「倒放」标记
    5. 断言：无报错 toast、预览区正常
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
WINDOW_TITLE_KEYWORD = os.getenv("FJ_WINDOW_TITLE", "帧境")
SHOT_DIR = Path(os.getenv("FJ_SHOT_DIR", "screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

EDITOR_FRAME_HINTS = ["opencut", "editing", "clip"]
SEL_CLIP = "button.absolute.inset-0.size-full.flex.flex-col"
SEL_TOOLBAR = "div.flex.h-10.items-center.justify-between.border-b.px-2.py-1"
IDX_REVERSE = 9

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
    raise RuntimeError("找不到剪辑工作台 iframe")


def get_clip_text(editor):
    try:
        return editor.evaluate(f"""() => {{
            const vh = window.innerHeight;
            const els = document.querySelectorAll('{SEL_CLIP}');
            for (const el of els) {{
                const r = el.getBoundingClientRect();
                if (r.top > vh * 0.55 && r.width > 50) {{
                    return (el.innerText || '').trim();
                }}
            }}
            return null;
        }}""")
    except Exception:
        return None


def get_popups(editor):
    try:
        return editor.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[role=dialog], [data-radix-popper-content-wrapper], [class*=toast], [class*=Toast]').forEach(el => {
                const t = (el.innerText || '').trim();
                if (t && t.length < 200) out.push(t);
            });
            return [...new Set(out)];
        }""")
    except Exception:
        return []


def get_errors(editor):
    try:
        return editor.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[class*=error], [class*=Error], [class*=destructive]').forEach(el => {
                const t = (el.innerText || '').trim();
                if (t && t.length < 200 && (t.includes('失败') || t.includes('错误') || t.includes('异常'))) out.push(t);
            });
            return [...new Set(out)];
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


def test_tc0007():
    log("=== TC0007：剪辑工作台-倒放 ===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0007_workbench.png")

        clip_before = get_clip_text(editor)
        log(f"  倒放前片段名: {clip_before!r}")
        if not clip_before:
            log("[FAIL] 时间线无片段，请先手动放入至少 1 个视频片段")
            sys.exit(1)

        # 选中第一个片段
        editor.locator(SEL_CLIP).first.click(timeout=3000)
        time.sleep(STEP_WAIT)

        # 点倒放
        if not click_toolbar_btn(editor, "倒放", IDX_REVERSE):
            errors.append("点击【倒放】失败")

        # 等待弹窗出现并完成（最多 20 秒）
        popup_seen = False
        popup_gone = False
        for i in range(20):
            time.sleep(1)
            popups = get_popups(editor)
            if popups:
                popup_seen = True
                log(f"  +{i+1}s 弹窗: {popups}")
            else:
                if popup_seen:
                    popup_gone = True
                    log(f"  +{i+1}s 弹窗已关闭")
                    break

        if not popup_seen:
            errors.append("倒放后未出现进度弹窗")
        elif not popup_gone:
            errors.append("倒放进度弹窗未在 20 秒内消失")

        # 检查报错
        errs = get_errors(editor)
        if errs:
            errors.append(f"出现报错: {errs}")

        # 断言：片段名含「倒放」
        clip_after = get_clip_text(editor)
        log(f"\n  倒放后片段名: {clip_after!r}")
        if not clip_after or "倒放" not in clip_after:
            errors.append(f"倒放未生效：片段名未包含「倒放」（实际: {clip_after!r}）")

        # 预览区检查
        preview_ok = False
        try:
            preview_ok = editor.evaluate("() => { const b = document.body.innerText||''; return b.includes('画质') || b.includes('比例'); }")
        except Exception:
            pass
        if preview_ok:
            log("  [OK] 预览区正常显示")
        else:
            errors.append("预览区未检测到")

        shot(page, "tc0007_final.png")
        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0007，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0007 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0007_error.png")
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
    test_tc0007()
