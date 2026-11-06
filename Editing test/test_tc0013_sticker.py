# -*- coding: utf-8 -*-
"""
TC0013 自动化测试：剪辑工作台-贴纸

前置：帧境以 --remote-debugging-port=9222 启动，已进入剪辑工作台
环境变量：FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR
"""

import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
WINDOW_TITLE_KEYWORD = os.getenv("FJ_WINDOW_TITLE", "帧境")
SHOT_DIR = Path(os.getenv("FJ_SHOT_DIR", "screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)
SEL_CLIP = "button.absolute.inset-0.size-full.flex.flex-col"

def log(m): print(m, flush=True)
def shot(page, n):
    try: page.screenshot(path=str(SHOT_DIR/n)); log(f"[SHOT] {n}")
    except: pass

def connect():
    pw = sync_playwright().start()
    b = pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    pages = b.contexts[0].pages
    target = next((p for p in pages if WINDOW_TITLE_KEYWORD in (p.title() or "")), pages[0])
    return pw, b, target

def find_editor(page):
    for f in page.frames:
        if f != page.main_frame and "opencut" in (f.url or "").lower():
            return f
    raise RuntimeError("no editor frame")

def test():
    log("=== TC0013：贴纸 ===")
    errors = []
    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}"); sys.exit(1)

    try:
        editor = find_editor(page)
        time.sleep(1.0)

        # 步骤1：点贴纸tab，断言分类
        log("\n=== 步骤1：贴纸面板分类 ===")
        editor.evaluate("""() => {
            for (const el of document.querySelectorAll('button,div,span')) {
                if ((el.innerText||'').trim()==='贴纸' && el.getBoundingClientRect().x<60) { el.click(); return; }
            }
        }""")
        time.sleep(1.5)
        cats = editor.evaluate("""() => {
            const expected = ['全部','我的','旗帜','形状'];
            const found = [];
            document.querySelectorAll('button').forEach(el => {
                const t=(el.innerText||'').trim();
                const r=el.getBoundingClientRect();
                if (r.x>50&&r.x<400&&r.y>30&&r.y<60&&expected.includes(t)) found.push(t);
            });
            return [...new Set(found)];
        }""")
        log(f"  分类: {cats}")
        for c in ['全部','我的','旗帜','形状']:
            if c not in cats: errors.append(f"缺少分类: {c}")

        # 断言最近使用+清除
        has_recent = editor.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='最近使用' && el.getBoundingClientRect().x>60) return true;
            }
            return false;
        }""")
        has_clear = editor.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='清除' && el.getBoundingClientRect().x>60) return true;
            }
            return false;
        }""")
        log(f"  最近使用: {has_recent}, 清除: {has_clear}")
        if not has_recent: errors.append("缺少'最近使用'")
        if not has_clear: errors.append("缺少'清除'")

        # 断言旗帜/形状+查看全部
        for cat in ['旗帜','形状']:
            has = editor.evaluate("""(n) => {
                for (const el of document.querySelectorAll('*')) {
                    if ((el.innerText||'').trim()===n && el.getBoundingClientRect().x>60) return true;
                }
                return false;
            }""", cat)
            log(f"  {cat}: {has}")
            if not has: errors.append(f"缺少分类区块: {cat}")

        shot(page, "tc0013_panel.png")

        # 步骤2：DOM方式点旗帜第一个贴纸+号按钮
        log("\n=== 步骤2：添加贴纸 ===")
        editor.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                const r = b.getBoundingClientRect();
                // 旗帜分类第一个+号：x≈126, y≈293, 20x20
                if (Math.abs(r.x - 126) < 5 && Math.abs(r.y - 293) < 5 && r.width === 20) {
                    b.click();
                    return 'ok';
                }
            }
            return 'not found';
        }""")
        time.sleep(2.0)
        shot(page, "tc0013_added.png")

        n = editor.evaluate(f"()=>document.querySelectorAll('{SEL_CLIP}').length")
        log(f"  片段数: {n}")

        # 步骤3：右侧面板字段
        log("\n=== 步骤3：右侧属性面板 ===")
        # 选中最后一个片段
        clips = editor.locator(SEL_CLIP)
        total = clips.count()
        if total > 0:
            clips.nth(total-1).click(timeout=3000)
            time.sleep(1.0)
            fields = editor.evaluate("""() => {
                const out = [];
                document.querySelectorAll('*').forEach(el => {
                    if (el.children.length>0) return;
                    const t=(el.innerText||'').trim();
                    if (!t||t.length>20) return;
                    const r=el.getBoundingClientRect();
                    if (r.x>800&&r.width>0&&r.y<800) out.push(t);
                });
                return [...new Set(out)];
            }""")
            log(f"  右侧字段: {fields}")
            for f in ['位置 X','位置 Y','缩放 X','缩放 Y','旋转']:
                if f not in fields:
                    log(f"  [WARN] 缺少字段: {f}")
        else:
            errors.append("贴纸未添加到时间线")
        shot(page, "tc0013_final.png")

        log("\n"+"="*60)
        if errors:
            log(f"[FAIL] {len(errors)} 项:")
            for e in errors: log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0013 通过")
        log("="*60)
    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback; traceback.print_exc()
        try: shot(page, "tc0013_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: browser.close(); pw.stop()
        except: pass

if __name__ == "__main__":
    test()
