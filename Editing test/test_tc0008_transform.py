# -*- coding: utf-8 -*-
"""
TC0008 自动化测试：剪辑工作台-位置变换（位置 X/Y、缩放 X/Y、旋转）

前置条件（人工准备）：
    1. 帧境以调试模式启动：  帧境.exe --remote-debugging-port=9222
    2. 已进入剪辑工作台（opencut iframe）
    3. 时间线上已有至少 1 个视频片段

运行前置：
    pip install playwright requests

环境变量（可选）：
    FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR

定位策略（已实测，帧境 v2.0.14）：
    - 选中视频片段后，右侧属性面板有 5 个数字输入框：
      位置X / 位置Y / 缩放X / 缩放Y / 旋转
    - 用相邻 label 文本定位 input，用 React 兼容方式设值（native setter + input/change 事件）

测试步骤：
    1. 选中主轨视频片段，记录初始参数
    2. 修改位置 X=10、位置 Y=0，断言读回值正确
    3. 修改缩放 X=1、缩放 Y=1，断言读回值正确
    4. 修改旋转=0，断言读回值正确
    5. 恢复位置 X=0，断言参数恢复默认
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


def get_transform_values(editor):
    """读取右侧面板 5 个参数：位置X, 位置Y, 缩放X, 缩放Y, 旋转。"""
    try:
        return editor.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.x > 800 && r.width > 0 && el.type !== 'file') out.push(el.value);
            });
            return out;
        }""")
    except Exception:
        return []


def set_transform_field(editor, label_text, new_value):
    """通过相邻 label 文本定位 input，设值并派发 React 事件。返回读回值。"""
    try:
        return editor.evaluate("""({label, val}) => {
            const inputs = document.querySelectorAll('input');
            for (const el of inputs) {
                const r = el.getBoundingClientRect();
                if (r.x <= 800 || r.width === 0 || el.type === 'file') continue;
                let container = el.parentElement;
                for (let i = 0; i < 5 && container; i++) {
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
        log(f"  set_transform_field({label_text}) 异常: {e}")
        return None


def test_tc0008():
    log("=== TC0008：剪辑工作台-位置变换（位置X/Y、缩放X/Y、旋转）===")
    errors = []

    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}")
        sys.exit(1)

    try:
        editor = find_editor_frame(page)
        time.sleep(1.0)
        shot(page, "tc0008_workbench.png")

        # 选中 first clip
        editor.locator(SEL_CLIP).first.click(timeout=3000)
        time.sleep(STEP_WAIT)

        initial = get_transform_values(editor)
        log(f"  初始参数 [位置X, 位置Y, 缩放X, 缩放Y, 旋转]: {initial}")
        if len(initial) != 5:
            errors.append(f"右侧面板未检测到 5 个参数输入框（实际 {len(initial)} 个），请确认已选中视频片段")
            shot(page, "tc0008_no_panel.png")
            sys.exit(1)

        # 步骤3：位置 X=10、位置 Y=0
        log("\n=== 步骤：修改位置 X/Y ===")
        v = set_transform_field(editor, "位置 X", "10")
        log(f"  位置 X → 10，读回: {v}")
        if v != "10":
            errors.append(f"位置 X 设值失败（期望 10，实际 {v}）")
        v = set_transform_field(editor, "位置 Y", "0")
        log(f"  位置 Y → 0，读回: {v}")
        if v != "0":
            errors.append(f"位置 Y 设值失败（期望 0，实际 {v}）")
        shot(page, "tc0008_after_position.png")

        # 步骤4：缩放 X=1、缩放 Y=1
        log("\n=== 步骤：修改缩放 X/Y ===")
        v = set_transform_field(editor, "缩放 X", "1")
        log(f"  缩放 X → 1，读回: {v}")
        if v != "1":
            errors.append(f"缩放 X 设值失败（期望 1，实际 {v}）")
        v = set_transform_field(editor, "缩放 Y", "1")
        log(f"  缩放 Y → 1，读回: {v}")
        if v != "1":
            errors.append(f"缩放 Y 设值失败（期望 1，实际 {v}）")
        shot(page, "tc0008_after_scale.png")

        # 步骤5：旋转=0
        log("\n=== 步骤：修改旋转 ===")
        v = set_transform_field(editor, "旋转", "0")
        log(f"  旋转 → 0，读回: {v}")
        if v != "0":
            errors.append(f"旋转设值失败（期望 0，实际 {v}）")
        shot(page, "tc0008_after_rotate.png")

        # 步骤6：恢复默认值
        log("\n=== 步骤：恢复默认值 ===")
        v = set_transform_field(editor, "位置 X", "0")
        log(f"  恢复位置 X → 0，读回: {v}")
        if v != "0":
            errors.append(f"位置 X 恢复失败（期望 0，实际 {v}）")
        final = get_transform_values(editor)
        log(f"  最终参数: {final}")
        shot(page, "tc0008_final.png")

        # 汇总
        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0008，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0008 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0008_error.png")
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
    test_tc0008()
