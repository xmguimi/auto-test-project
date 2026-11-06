# -*- coding: utf-8 -*-
"""
TC0010 自动化测试：剪辑工作台-蒙版功能（文字蒙版）

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有至少 1 个视频片段

环境变量（可选）：
    FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR

定位策略（已实测，帧境 v2.0.14）：
    - 右侧面板 7 个图标 tab，蒙版是 tab#5（iframe 内 x≈1197, 32x32）
    - 蒙版面板初始："暂无蒙版" + 【添加蒙版】按钮
    - 点【添加蒙版】后弹出类型列表（portal 渲染在 iframe 内），
      "Aa 文字"项为 div（x>1300, innerText==='文字', w≈151, h≈30）
    - 文字蒙版参数面板：
        内容 textarea(x≈1134,y≈113)
        字体下拉(x≈1165,y≈383)
        字号 input(x≈1165,y≈302)
        字间距 input(x≈1165,y≈368) / 行间距 input(x≈1336,y≈368)
        位置X(x≈1159,y≈434) / 位置Y(x≈1329,y≈434)
        缩放 input(x≈1165,y≈500)
        旋转 input(x≈1165,y≈566)
        羽化 input(x≈1165,y≈632)
        描边W input(x≈1163,y≈698) / 颜色 input(x≈1332,y≈693)

测试步骤：
    1. 选中片段 → 蒙版 tab → 添加蒙版 → 选"Aa 文字"
    2. 内容设为"羊咩咩驾到"
    3. 字号设为 12
    4. 字间距 0 / 行间距 1.2
    5. 位置 X=3 / Y=3
    6. 缩放 100
    7. 旋转 10
    8. 羽化 10
    9. 描边 W=2 / 颜色 FBFAFA
    10. 字体下拉尝试选"微软雅黑"（如下拉无此选项则记录跳过）
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
MASK_TAB_INDEX = 5  # 右侧面板第6个图标（0-based）
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


def select_mask_tab(editor):
    """点击右侧面板蒙版 tab（tab#5）。"""
    editor.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        let n = 0;
        for (const el of btns) {
            const r = el.getBoundingClientRect();
            if (r.x > 1190 && r.x < 1230 && r.width === 32 && r.height === 32) {
                if (n === 5) { el.click(); return; }
                n++;
            }
        }
    }""")
    time.sleep(STEP_WAIT)


def click_add_mask(editor):
    """点击【添加蒙版】按钮。"""
    editor.evaluate("""() => {
        for (const el of document.querySelectorAll('button')) {
            if ((el.innerText||'').includes('添加蒙版')) { el.click(); return; }
        }
    }""")
    time.sleep(1.2)


def click_text_mask_type(editor):
    """在弹出的类型列表里点"Aa 文字"项。"""
    result = editor.evaluate("""() => {
        const divs = document.querySelectorAll('div');
        for (const el of divs) {
            const t = (el.innerText||'').trim();
            const r = el.getBoundingClientRect();
            if (t === '文字' && r.x > 1300 && r.width > 100 && r.width < 200) {
                el.click();
                return 'ok';
            }
        }
        return 'not found';
    }""")
    time.sleep(1.5)
    return result


def set_textarea(editor, value):
    """设置内容 textarea。"""
    return editor.evaluate("""(val) => {
        const ta = document.querySelector('textarea');
        if (!ta) return null;
        const r = ta.getBoundingClientRect();
        if (r.x <= 800) return null;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(ta, val);
        ta.dispatchEvent(new Event('input', {bubbles: true}));
        ta.dispatchEvent(new Event('change', {bubbles: true}));
        ta.blur();
        return ta.value;
    }""", value)


def set_input_by_y(editor, y_target, value):
    """按 y 坐标定位右侧面板 input 并设值。返回读回值。"""
    return editor.evaluate("""({y, val}) => {
        const inputs = document.querySelectorAll('input[type=text]');
        let best = null;
        let bestDist = 999;
        for (const el of inputs) {
            const r = el.getBoundingClientRect();
            if (r.x <= 800 || r.width === 0) continue;
            const d = Math.abs(r.y - y);
            if (d < bestDist) { bestDist = d; best = el; }
        }
        if (!best || bestDist > 15) return null;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(best, String(val));
        best.dispatchEvent(new Event('input', {bubbles: true}));
        best.dispatchEvent(new Event('change', {bubbles: true}));
        best.blur();
        return best.value;
    }""", {"y": y_target, "val": value})


def get_all_mask_fields(editor):
    """读取文字蒙版面板所有字段当前值。"""
    return editor.evaluate("""() => {
        const out = {content: null, fontSize: null, letterSpacing: null, lineHeight: null,
                     posX: null, posY: null, scale: null, rotation: null, feather: null,
                     strokeW: null, strokeColor: null, font: null};
        const ta = document.querySelector('textarea');
        if (ta) out.content = ta.value;
        document.querySelectorAll('input[type=text]').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.x <= 800 || r.width === 0) return;
            if (Math.abs(r.y - 302) < 10) out.fontSize = el.value;
            else if (Math.abs(r.y - 368) < 10 && r.x < 1250) out.letterSpacing = el.value;
            else if (Math.abs(r.y - 368) < 10 && r.x > 1250) out.lineHeight = el.value;
            else if (Math.abs(r.y - 434) < 10 && r.x < 1250) out.posX = el.value;
            else if (Math.abs(r.y - 434) < 10 && r.x > 1250) out.posY = el.value;
            else if (Math.abs(r.y - 500) < 10) out.scale = el.value;
            else if (Math.abs(r.y - 566) < 10) out.rotation = el.value;
            else if (Math.abs(r.y - 632) < 10) out.feather = el.value;
            else if (Math.abs(r.y - 698) < 10 && r.x < 1250) out.strokeW = el.value;
            else if (Math.abs(r.y - 693) < 10 && r.x > 1250) out.strokeColor = el.value;
        });
        // 字体下拉
        document.querySelectorAll('*').forEach(el => {
            if (el.children.length === 0) {
                const t = (el.innerText||'').trim();
                const r = el.getBoundingClientRect();
                if (t === 'Arial' || (t.includes('雅黑') && r.x > 1100)) out.font = t;
            }
        });
        return out;
    }""")


def try_set_font(editor, page, errors):
    """尝试点开字体下拉并选'微软雅黑'。"""
    try:
        # 点字体下拉（内容textarea y≈113下方，约 y≈240）
        editor.evaluate("""() => {
            const all = document.querySelectorAll('*');
            for (const el of all) {
                const r = el.getBoundingClientRect();
                if (r.x > 1100 && r.x < 1500 && r.y > 220 && r.y < 280 && r.width > 200) {
                    el.click(); return;
                }
            }
        }""")
        time.sleep(1.0)
        page.screenshot(path=str(SHOT_DIR / "tc0010_font_dropdown.png"))

        # 在下拉选项里找"微软雅黑"
        result = editor.evaluate("""() => {
            const all = document.querySelectorAll('*');
            for (const el of all) {
                const t = (el.innerText||'').trim();
                if (el.children.length === 0 && t.includes('微软雅黑')) {
                    el.click();
                    return 'selected: ' + t;
                }
            }
            // 列出所有选项
            const opts = [];
            for (const el of all) {
                if (el.children.length === 0) {
                    const t = (el.innerText||'').trim();
                    if (t && t.length < 20) {
                        const r = el.getBoundingClientRect();
                        if (r.x > 1100 && r.width > 50) opts.push(t);
                    }
                }
            }
            return 'no 微软雅黑, options: ' + [...new Set(opts)].slice(0, 20).join(',');
        }""")
        log(f"  字体下拉: {result}")
        if result.startswith("selected"):
            time.sleep(0.5)
        else:
            errors.append(f"字体下拉中未找到'微软雅黑'（{result}）")
    except Exception as e:
        errors.append(f"字体下拉操作异常: {e}")


def test_tc0010():
    log("=== TC0010：剪辑工作台-蒙版功能（文字蒙版）===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0010_workbench.png")

        # 步骤1：选中片段 → 蒙版 tab → 添加蒙版 → 选"Aa 文字"
        log("\n=== 步骤1：添加文字蒙版 ===")
        editor.locator(SEL_CLIP).first.click(timeout=3000)
        time.sleep(STEP_WAIT)
        select_mask_tab(editor)
        log("  已切换到蒙版面板")
        click_add_mask(editor)
        log("  已点添加蒙版")
        r = click_text_mask_type(editor)
        log(f"  选择'Aa 文字': {r}")
        if r != "ok":
            errors.append("无法选择'Aa 文字'蒙版类型")
        time.sleep(1.0)
        shot(page, "tc0010_text_mask_added.png")

        before = get_all_mask_fields(editor)
        log(f"  初始字段: {before}")

        # 步骤2：内容设为"羊咩咩驾到"
        log("\n=== 步骤2：内容文字 ===")
        v = set_textarea(editor, "羊咩咩驾到")
        log(f"  内容 → '羊咩咩驾到'，读回: {v}")
        if v != "羊咩咩驾到":
            errors.append(f"内容设值失败（期望'羊咩咩驾到'，实际'{v}'）")
        shot(page, "tc0010_content.png")

        # 步骤3：字号=12
        log("\n=== 步骤3：字号 ===")
        v = set_input_by_y(editor, 302, "12")
        log(f"  字号 → 12，读回: {v}")
        if v != "12":
            errors.append(f"字号设值失败（期望 12，实际 {v}）")
        shot(page, "tc0010_fontsize.png")

        # 步骤4：字间距=0, 行间距=1.2
        log("\n=== 步骤4：间距 ===")
        v1 = set_input_by_y(editor, 368, "0")
        v2 = editor.evaluate("""() => {
            const inputs = document.querySelectorAll('input[type=text]');
            for (const el of inputs) {
                const r = el.getBoundingClientRect();
                if (r.x > 1250 && Math.abs(r.y - 368) < 10) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '1.2');
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.blur();
                    return el.value;
                }
            }
            return null;
        }""")
        log(f"  字间距 → 0，读回: {v1}；行间距 → 1.2，读回: {v2}")
        if v1 != "0":
            errors.append(f"字间距设值失败（期望 0，实际 {v1}）")
        if v2 not in ("1.2", "1.20"):
            errors.append(f"行间距设值失败（期望 1.2，实际 {v2}）")

        # 步骤5：位置 X=3, Y=3
        log("\n=== 步骤5：位置 ===")
        v1 = set_input_by_y(editor, 434, "3")
        v2 = editor.evaluate("""() => {
            const inputs = document.querySelectorAll('input[type=text]');
            for (const el of inputs) {
                const r = el.getBoundingClientRect();
                if (r.x > 1250 && Math.abs(r.y - 434) < 10) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '3');
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.blur();
                    return el.value;
                }
            }
            return null;
        }""")
        log(f"  X → 3，读回: {v1}；Y → 3，读回: {v2}")
        if v1 != "3":
            errors.append(f"位置X设值失败（期望 3，实际 {v1}）")
        if v2 != "3":
            errors.append(f"位置Y设值失败（期望 3，实际 {v2}）")

        # 步骤6：缩放=100
        log("\n=== 步骤6：缩放 ===")
        v = set_input_by_y(editor, 500, "100")
        log(f"  缩放 → 100，读回: {v}")
        if v != "100":
            errors.append(f"缩放设值失败（期望 100，实际 {v}）")

        # 步骤7：旋转=10
        log("\n=== 步骤7：旋转 ===")
        v = set_input_by_y(editor, 566, "10")
        log(f"  旋转 → 10，读回: {v}")
        if v != "10":
            errors.append(f"旋转设值失败（期望 10，实际 {v}）")

        # 步骤8：羽化=10
        log("\n=== 步骤8：羽化 ===")
        v = set_input_by_y(editor, 632, "10")
        log(f"  羽化 → 10，读回: {v}")
        if v != "10":
            errors.append(f"羽化设值失败（期望 10，实际 {v}）")

        # 步骤9：描边 W=2, 颜色 FBFAFA
        log("\n=== 步骤9：描边 ===")
        v1 = set_input_by_y(editor, 698, "2")
        v2 = editor.evaluate("""() => {
            const inputs = document.querySelectorAll('input[type=text]');
            for (const el of inputs) {
                const r = el.getBoundingClientRect();
                if (r.x > 1250 && Math.abs(r.y - 693) < 10) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, 'FBFAFA');
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.blur();
                    return el.value;
                }
            }
            return null;
        }""")
        log(f"  描边W → 2，读回: {v1}；颜色 → FBFAFA，读回: {v2}")
        if v1 != "2":
            errors.append(f"描边宽度设值失败（期望 2，实际 {v1}）")
        if v2 and v2.upper().replace('#','') not in ("FBFAFA",):
            errors.append(f"描边颜色设值失败（期望 FBFAFA，实际 {v2}）")
        shot(page, "tc0010_stroke.png")

        # 步骤10：字体下拉
        log("\n=== 步骤10：字体 ===")
        try_set_font(editor, page, errors)

        # 最终读回
        time.sleep(1.0)
        final = get_all_mask_fields(editor)
        log(f"\n  最终字段: {final}")
        shot(page, "tc0010_final.png")

        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0010，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0010 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0010_error.png")
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
    test_tc0010()
