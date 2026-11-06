# -*- coding: utf-8 -*-
"""
TC0009 自动化测试：剪辑工作台-音频属性（音量、静音、淡入/淡出时长）

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有至少 1 个视频片段

环境变量（可选）：
    FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR

定位策略（已实测，帧境 v2.0.14）：
    - 提取音频后，选中音频轨道片段（y 更大的那条）
    - 右侧面板：音量 input(label=音量)、静音开关(button role=switch)、
      淡入时长 input(label=s, y≈173)、淡出时长 input(label=s, y≈239)
    - 音量最大值 20，输入 50 自动变回 20

测试步骤：
    1. 选中视频片段 → 提取音频 → 选中音频片段
    2. 音量设为 10，断言读回；再测试最大值（设50自动变20）
    3. 静音开关打开/关闭，断言 aria-checked 状态切换
    4. 淡入时长设 0.5，断言读回
    5. 淡出时长设 0.5，断言读回
    6. 恢复默认值
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
IDX_EXTRACT_AUDIO = 5
OPEN_TIMEOUT = 20
STEP_WAIT = 0.5


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


def count_clips(editor):
    try:
        return editor.evaluate(f"""() => {{
            const vh = window.innerHeight;
            let n = 0;
            document.querySelectorAll('{SEL_CLIP}').forEach(el => {{
                const r = el.getBoundingClientRect();
                if (r.top > vh * 0.55 && r.width > 50) n++;
            }});
            return n;
        }}""")
    except Exception:
        return 0


def set_field_by_label(editor, label_text, new_value):
    """通过相邻 label 文本定位 input，React 兼容设值。返回读回值。"""
    try:
        return editor.evaluate("""({label, val}) => {
            const inputs = document.querySelectorAll('input');
            for (const el of inputs) {
                const r = el.getBoundingClientRect();
                if (r.x <= 800 || r.width === 0 || el.type === 'file') continue;
                let container = el.parentElement;
                for (let i = 0; i < 6 && container; i++) {
                    if ((container.innerText||'').includes(label)) {
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(el, String(val));
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                        el.blur();
                        return el.value;
                    }
                    container = container.parentElement;
                }
            }
            return null;
        }""", {"label": label_text, "val": new_value})
    except Exception as e:
        log(f"  set_field({label_text}) 异常: {e}")
        return None


def get_mute_state(editor):
    """返回静音开关 aria-checked ('true'/'false')。"""
    try:
        return editor.evaluate("""() => {
            const btns = document.querySelectorAll('[role=switch], button[aria-checked]');
            for (const el of btns) {
                const r = el.getBoundingClientRect();
                if (r.x > 800 && r.width > 0) return el.getAttribute('aria-checked');
            }
            return null;
        }""")
    except Exception:
        return None


def toggle_mute(editor):
    """点击静音开关，返回新状态。"""
    try:
        editor.evaluate("""() => {
            const btns = document.querySelectorAll('[role=switch], button[aria-checked]');
            for (const el of btns) {
                const r = el.getBoundingClientRect();
                if (r.x > 800 && r.width > 0) { el.click(); return; }
            }
        }""")
        time.sleep(0.4)
        return get_mute_state(editor)
    except Exception as e:
        log(f"  toggle_mute 异常: {e}")
        return None


def get_audio_fields(editor):
    """读取音量、淡入、淡出三个 input 值。"""
    try:
        return editor.evaluate("""() => {
            const out = {volume: null, fadeIn: null, fadeOut: null};
            document.querySelectorAll('input').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.x <= 800 || r.width === 0 || el.type === 'file') return;
                let container = el.parentElement;
                for (let i = 0; i < 6 && container; i++) {
                    const t = container.innerText || '';
                    if (t.includes('音量')) out.volume = el.value;
                    else if (t.includes('淡入')) out.fadeIn = el.value;
                    else if (t.includes('淡出')) out.fadeOut = el.value;
                    container = container.parentElement;
                }
            });
            return out;
        }""")
    except Exception:
        return {}


def test_tc0009():
    log("=== TC0009：剪辑工作台-音频属性（音量、静音、淡入/淡出）===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0009_workbench.png")

        # 步骤1：选中视频片段 → 提取音频
        editor.locator(SEL_CLIP).first.click(timeout=3000)
        time.sleep(STEP_WAIT)
        tb = editor.locator(SEL_TOOLBAR).first
        btns = tb.locator("button")
        btns.nth(IDX_EXTRACT_AUDIO).evaluate("el => el.click()")
        log("[OK] 已点击提取音频")
        time.sleep(2.5)

        n = count_clips(editor)
        log(f"  提取音频后片段数: {n}")
        if n < 2:
            errors.append("提取音频后未生成音频轨道（片段数 < 2）")

        # 选中音频片段（最后一个）
        clips = editor.locator(SEL_CLIP)
        clips.nth(clips.count() - 1).click(timeout=3000)
        time.sleep(STEP_WAIT)
        shot(page, "tc0009_audio_selected.png")

        initial = get_audio_fields(editor)
        log(f"  初始音频参数: {initial}")

        # 步骤2：音量=10
        log("\n=== 步骤：音量 ===")
        v = set_field_by_label(editor, "音量", "10")
        log(f"  音量 → 10，读回: {v}")
        if v != "10":
            errors.append(f"音量设值失败（期望 10，实际 {v}）")

        # 测试音量最大值：设 50 应自动变 20
        v = set_field_by_label(editor, "音量", "50")
        log(f"  音量 → 50，读回（应自动变回 20）: {v}")
        if v != "20":
            errors.append(f"音量最大值限制未生效（输入 50 后应为 20，实际 {v}）")
        shot(page, "tc0009_volume.png")

        # 步骤3：静音开关
        log("\n=== 步骤：静音开关 ===")
        s = get_mute_state(editor)
        log(f"  静音初始状态: {s}")
        s = toggle_mute(editor)
        log(f"  打开静音后: {s}")
        if s != "true":
            errors.append(f"静音打开失败（aria-checked 应为 true，实际 {s}）")
        s = toggle_mute(editor)
        log(f"  关闭静音后: {s}")
        if s != "false":
            errors.append(f"静音关闭失败（aria-checked 应为 false，实际 {s}）")
        shot(page, "tc0009_mute.png")

        # 步骤4：淡入时长=0.5
        log("\n=== 步骤：淡入时长 ===")
        v = set_field_by_label(editor, "淡入", "0.5")
        log(f"  淡入 → 0.5，读回: {v}")
        if v not in ("0.5", "0.50"):
            errors.append(f"淡入时长设值失败（期望 0.5，实际 {v}）")

        # 步骤5：淡出时长=0.5
        log("\n=== 步骤：淡出时长 ===")
        v = set_field_by_label(editor, "淡出", "0.5")
        log(f"  淡出 → 0.5，读回: {v}")
        if v not in ("0.5", "0.50"):
            errors.append(f"淡出时长设值失败（期望 0.5，实际 {v}）")
        shot(page, "tc0009_fade.png")

        # 恢复默认
        log("\n=== 恢复默认 ===")
        set_field_by_label(editor, "音量", "0")
        set_field_by_label(editor, "淡入", "0")
        set_field_by_label(editor, "淡出", "0")
        final = get_audio_fields(editor)
        log(f"  最终参数: {final}")
        shot(page, "tc0009_final.png")

        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0009，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0009 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0009_error.png")
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
    test_tc0009()
