# -*- coding: utf-8 -*-
"""
TC0011 自动化测试：剪辑工作台-音效（导入音频+音频属性面板）

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有视频片段

环境变量（可选）：
    FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR
    FJ_AUDIO_FILE — 要导入的音频文件绝对路径（默认 testdata/欢呼声.mp3）

测试步骤：
    1. 点左侧【音效】tab → 断言初始显示"暂无可用音效"
    2. 点左侧【素材】tab → 点【+导入】→ filechooser 选择本地音频
    3. 断言音频出现在素材列表
    4. 将音频拖入时间线 → 断言生成音频轨道
    5. 选中音频片段 → 右侧面板显示音量/静音/淡入/淡出
    6. 音量设为 10，断言读回
    7. 静音开关打开/关闭
    8. 淡入 0.5 / 淡出 0.5
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

# 默认音频文件路径（相对项目目录）
DEFAULT_AUDIO = Path(__file__).parent.parent / "testdata" / "欢呼声.mp3"
AUDIO_FILE = os.getenv("FJ_AUDIO_FILE", str(DEFAULT_AUDIO))

EDITOR_FRAME_HINTS = ["opencut", "editing", "clip"]
SEL_CLIP = "button.absolute.inset-0.size-full.flex.flex-col"
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


def click_left_tab(editor, tab_name):
    """点左侧边栏图标（素材/音效/文字等）。"""
    editor.evaluate("""(name) => {
        for (const el of document.querySelectorAll('button, div, span')) {
            const t = (el.innerText||'').trim();
            if (t === name && el.getBoundingClientRect().x < 60) { el.click(); return; }
        }
    }""", tab_name)
    time.sleep(1.0)


def get_sound_hint(editor):
    """读取音效面板提示文字。"""
    return editor.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.children.length > 0) continue;
            const t = (el.innerText||'').trim();
            const r = el.getBoundingClientRect();
            if (r.x > 60 && r.x < 400 && r.width > 50 && t && t.length < 30) {
                if (t.includes('音效') || t.includes('可用')) return t;
            }
        }
        return null;
    }""")


def click_import_button(editor):
    """点素材面板的【+导入】按钮。"""
    editor.evaluate("""() => {
        for (const el of document.querySelectorAll('button')) {
            const t = (el.innerText||'').trim();
            const r = el.getBoundingClientRect();
            if (t.includes('导入') && r.x > 60 && r.x < 200 && r.y < 60) {
                el.click(); return;
            }
        }
    }""")
    time.sleep(1.0)


def find_audio_in_assets(editor, audio_name="欢呼声"):
    """在素材列表中找音频文件，返回元素 bounding rect。"""
    return editor.evaluate("""(name) => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.children.length > 0) continue;
            const t = (el.innerText||'').trim();
            if (t.includes(name)) {
                const r = el.getBoundingClientRect();
                if (r.x > 60 && r.x < 400 && r.width > 20) {
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }
            }
        }
        return null;
    }""", audio_name)


def count_clips(editor):
    try:
        return editor.evaluate(f"""() => {{
            let n = 0;
            document.querySelectorAll('{SEL_CLIP}').forEach(el => {{
                const r = el.getBoundingClientRect();
                if (r.width > 50) n++;
            }});
            return n;
        }}""")
    except Exception:
        return 0


def set_field_by_label(editor, label_text, new_value):
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


def test_tc0011():
    log("=== TC0011：剪辑工作台-音效 ===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)

        # 步骤1：点音效tab → 断言初始提示
        log("\n=== 步骤1：音效面板初始状态 ===")
        click_left_tab(editor, "音效")
        hint = get_sound_hint(editor)
        log(f"  音效面板提示: {hint}")
        shot(page, "tc0011_sound_initial.png")
        if hint != "暂无可用音效":
            errors.append(f"音效面板初始提示不是'暂无可用音效'（实际'{hint}'）")

        # 步骤2：点素材tab → 导入音频
        log("\n=== 步骤2：导入本地音频 ===")
        if not Path(AUDIO_FILE).exists():
            errors.append(f"音频文件不存在: {AUDIO_FILE}")
            raise RuntimeError(f"音频文件不存在: {AUDIO_FILE}")

        click_left_tab(editor, "素材")
        # 注册 filechooser 监听
        fc_triggered = []
        def on_fc(fc):
            fc_triggered.append(True)
            log(f"  [FILECHOOSER] 已触发，选择文件")
            fc.set_files(AUDIO_FILE)
        page.on("filechooser", on_fc)

        click_import_button(editor)
        time.sleep(3.0)
        log(f"  filechooser 触发: {len(fc_triggered) > 0}")
        shot(page, "tc0011_after_import.png")

        # 步骤3：断言音频出现在素材列表
        log("\n=== 步骤3：音频出现在列表 ===")
        audio_pos = find_audio_in_assets(editor, "欢呼声")
        log(f"  音频位置: {audio_pos}")
        if not audio_pos:
            errors.append("导入后素材列表中未找到'欢呼声.mp3'")

        # 步骤4：拖音频到时间线（音频卡片在素材列表右上角，无缩略图）
        log("\n=== 步骤4：拖入时间线 ===")
        # 找包含"欢呼声"的叶子元素，取其位置（向上找带点击区域的父容器）
        box = editor.evaluate("""() => {
            const nodes = document.querySelectorAll('*');
            for (const el of nodes) {
                if ((el.innerText||'').includes('欢呼声') && el.children.length === 0) {
                    let card = el;
                    for (let i = 0; i < 4 && card; i++) {
                        const r = card.getBoundingClientRect();
                        if (r.x > 60 && r.x < 400 && r.width > 50 && r.height > 40 && r.y < 300) {
                            return {x: r.x + r.width/2, y: r.y + r.height/2};
                        }
                        card = card.parentElement;
                    }
                }
            }
            return null;
        }""")
        if box:
            ax, ay = box["x"], box["y"]
            log(f"  拖拽起点: ({ax:.0f}, {ay:.0f})")
            page.mouse.move(ax, 76 + ay); time.sleep(0.4)
            page.mouse.down(); time.sleep(0.5)
            for s in range(1, 61):
                x = ax + (420 - ax) * s / 60
                y = ay + (688 - ay) * s / 60
                page.mouse.move(x, 76 + y)
                time.sleep(0.03)
            time.sleep(0.5)
            page.mouse.up(); time.sleep(2.5)
            shot(page, "tc0011_audio_on_timeline.png")

        n = count_clips(editor)
        log(f"  时间线片段数: {n}")
        if n < 2:
            errors.append(f"拖入音频后片段数 < 2（实际 {n}）")

        # 步骤5：选中音频片段（最后一个），右侧面板
        log("\n=== 步骤5：选中音频片段 ===")
        clips = editor.locator(SEL_CLIP)
        total = clips.count()
        if total >= 2:
            clips.nth(total - 1).click(timeout=3000)
        else:
            clips.first.click(timeout=3000)
        time.sleep(STEP_WAIT)
        shot(page, "tc0011_audio_selected.png")

        # 步骤6：音量=10
        log("\n=== 步骤6：音量 ===")
        v = set_field_by_label(editor, "音量", "10")
        log(f"  音量 → 10，读回: {v}")
        if v != "10":
            errors.append(f"音量设值失败（期望 10，实际 {v}）")

        # 步骤7：静音开关
        log("\n=== 步骤7：静音 ===")
        mute_state = editor.evaluate("""() => {
            const btns = document.querySelectorAll('[role=switch], button[aria-checked]');
            for (const el of btns) {
                const r = el.getBoundingClientRect();
                if (r.x > 800 && r.width > 0) return el.getAttribute('aria-checked');
            }
            return null;
        }""")
        log(f"  静音初始: {mute_state}")
        if mute_state is not None:
            editor.evaluate("""() => {
                const btns = document.querySelectorAll('[role=switch], button[aria-checked]');
                for (const el of btns) {
                    const r = el.getBoundingClientRect();
                    if (r.x > 800 && r.width > 0) { el.click(); return; }
                }
            }""")
            time.sleep(0.4)
            mute_state = editor.evaluate("""() => {
                const btns = document.querySelectorAll('[role=switch], button[aria-checked]');
                for (const el of btns) {
                    const r = el.getBoundingClientRect();
                    if (r.x > 800 && r.width > 0) return el.getAttribute('aria-checked');
                }
                return null;
            }""")
            log(f"  静音切换后: {mute_state}")

        # 步骤8：淡入/淡出=0.5
        log("\n=== 步骤8：淡入/淡出 ===")
        v1 = set_field_by_label(editor, "淡入", "0.5")
        v2 = set_field_by_label(editor, "淡出", "0.5")
        log(f"  淡入 → 0.5，读回: {v1}；淡出 → 0.5，读回: {v2}")
        if v1 not in ("0.5", "0.50"):
            errors.append(f"淡入设值失败（实际 {v1}）")
        if v2 not in ("0.5", "0.50"):
            errors.append(f"淡出设值失败（实际 {v2}）")
        shot(page, "tc0011_final.png")

        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0011，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0011 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0011_error.png")
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
    test_tc0011()
