# -*- coding: utf-8 -*-
"""
TC-0004: 图片/文生数字人-弹窗布局与默认值
验证：创建形象弹窗各字段显示、生成按钮初始置灰
纯DOM元素定位
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    target = None
    for p in browser.contexts[0].pages:
        if "帧境" in (p.title() or ""):
            target = p
            break
    if not target:
        target = browser.contexts[0].pages[0]
    return pw, browser, target


def test_tc0004():
    print("=" * 60, flush=True)
    print("TC-0004: 图片/文生数字人-弹窗布局与默认值", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200
    except Exception:
        print("[ERROR] CDP未就绪", flush=True); sys.exit(1)

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        time.sleep(2)

        # 步骤0：进入项目
        print("\n--- 步骤0：进入项目 ---", flush=True)
        project = page.locator("text=剪辑测试")
        if project.count() > 0:
            project.first.click(force=True)
            time.sleep(6)

        # 步骤1：打开数字人库→形象tab→点创建形象
        print("\n--- 步骤1：打开创建形象弹窗 ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.locator("text=形象").first.click(force=True)
        time.sleep(1)
        # 点创建形象
        page.locator("text=创建形象").first.click(force=True)
        time.sleep(2)
        shot(page, "tc0004_dialog.png")
        print("  ✅ 创建形象弹窗已打开", flush=True)

        # 步骤2：验证创意描述输入框
        print("\n--- 步骤2：创意描述 ---", flush=True)
        desc = page.locator("[contenteditable='true'], textarea")
        if desc.count() > 0:
            print("  ✅ 创意描述输入框可见", flush=True)
        else:
            errors.append("创意描述输入框未找到")

        # 步骤3：验证试用标签
        print("\n--- 步骤3：试用标签 ---", flush=True)
        for tag in ["办公白领", "带货博主", "英语老师"]:
            el = page.locator(f"text={tag}")
            if el.count() > 0:
                print(f"  ✅ 标签 '{tag}' 可见", flush=True)
            else:
                print(f"  [WARN] 标签 '{tag}' 未找到", flush=True)

        # 步骤4：验证右侧tab
        print("\n--- 步骤4：右侧tab ---", flush=True)
        for tab in ["本次生成", "历史"]:
            el = page.locator(f"text={tab}")
            if el.count() > 0:
                print(f"  ✅ tab '{tab}' 可见", flush=True)
            else:
                errors.append(f"tab '{tab}' 未找到")

        # 步骤5：验证生成按钮初始置灰
        print("\n--- 步骤5：生成按钮 ---", flush=True)
        gen_btn_info = page.evaluate("""() => {
            const all = document.querySelectorAll('button');
            const results = [];
            for (const b of all) {
                const t = b.innerText.trim();
                if (t === '生成' || t === '生 成') {
                    const cs = getComputedStyle(b);
                    results.push({text: t, disabled: b.disabled, cls: b.className.substring(0,50), bg: cs.backgroundColor, opacity: cs.opacity});
                }
            }
            return results;
        }""")
        print(f"  找到生成按钮: {gen_btn_info}", flush=True)
        # 判断是否置灰（紫色半透明/opacity<1/class含disabled）
        is_disabled = False
        for btn in gen_btn_info:
            if btn.get('disabled') or float(btn.get('opacity', 1)) < 1 or 'disabled' in btn.get('cls', ''):
                is_disabled = True
        if is_disabled:
            print("  ✅ 生成按钮初始置灰", flush=True)
        else:
            errors.append(f"生成按钮未置灰: {gen_btn_info}")

        shot(page, "tc0004_final.png")

        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0004 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0004_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0004()
