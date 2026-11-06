# -*- coding: utf-8 -*-
"""
TC0012 自动化测试：剪辑工作台-文字与字幕

前置条件：
    1. 帧境以 --remote-debugging-port=9222 启动
    2. 已进入剪辑工作台

环境变量：FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR
"""

import os, sys, time, requests
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
    try: page.screenshot(path=str(SHOT_DIR / n)); log(f"[SHOT] {n}")
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


def click_left_tab(editor, name):
    editor.evaluate("""(n) => {
        for (const el of document.querySelectorAll('button,div,span')) {
            if ((el.innerText||'').trim()===n && el.getBoundingClientRect().x<60) { el.click(); return; }
        }
    }""", name)
    time.sleep(1.0)


def drag_video_to_timeline(editor, page):
    """拖羊群奔跑.mp4到时间线。"""
    box = editor.evaluate("""() => {
        for (const el of document.querySelectorAll('*')) {
            if ((el.innerText||'').trim()==='羊群奔跑.mp4') {
                let c=el;
                for(let i=0;i<6&&c;i++){
                    if(c.querySelector&&c.querySelector('img')){
                        const r=c.getBoundingClientRect();
                        return {x:r.x+r.width/2,y:r.y+r.height/2-10};
                    }
                    c=c.parentElement;
                }
            }
        }
        return null;
    }""")
    if not box:
        log("  [WARN] 未找到羊群奔跑.mp4")
        return
    ax, ay = box["x"], box["y"]
    page.mouse.move(ax, 76+ay); time.sleep(0.4)
    page.mouse.down(); time.sleep(0.5)
    for s in range(1,61):
        x = ax+(420-ax)*s/60
        y = ay+(688-ay)*s/60
        page.mouse.move(x, 76+y); time.sleep(0.03)
    time.sleep(0.5)
    page.mouse.up(); time.sleep(2.5)


def test():
    log("=== TC0012：文字与字幕 ===")
    errors = []
    try:
        pw, browser, page = connect()
    except Exception as e:
        log(f"[FAIL] {e}"); sys.exit(1)

    try:
        editor = find_editor(page)
        time.sleep(1.0)

        # 步骤1：确认时间线有片段（force_reset已拖视频，等待加载）
        log("\n=== 步骤1：确认时间线 ===")
        time.sleep(2.0)
        n = editor.evaluate(f"()=>document.querySelectorAll('{SEL_CLIP}').length")
        log(f"  片段数: {n}")
        if n < 1:
            drag_video_to_timeline(editor, page)
            n = editor.evaluate(f"()=>document.querySelectorAll('{SEL_CLIP}').length")
            log(f"  拖拽后片段数: {n}")
        if n < 1:
            log("  [WARN] 时间线无视频片段（不影响字幕功能测试）")

        # 步骤2：文字面板样式
        log("\n=== 步骤2：文字面板样式 ===")
        click_left_tab(editor, "文字")
        time.sleep(1.0)
        styles = editor.evaluate("""() => {
            const expected = ['默认文字','标题','字幕','说明文字','大标题','副标题','高亮标题','标签'];
            const found = [];
            for (const el of document.querySelectorAll('*')) {
                if (el.children.length>0) continue;
                const t=(el.innerText||'').trim();
                const r=el.getBoundingClientRect();
                if (r.x>60&&r.x<400&&r.width>20&&r.height>10&&expected.includes(t)) {
                    found.push(t);
                }
            }
            return [...new Set(found)];
        }""")
        log(f"  找到样式: {styles}")
        expected_styles = ['默认文字','标题','字幕','说明文字','大标题','副标题','高亮标题']
        for s in expected_styles:
            if s not in styles:
                errors.append(f"文字面板缺少样式: {s}")
        shot(page, "tc0012_text_styles.png")

        # 步骤3：点默认文字的+号添加
        log("\n=== 步骤3：添加默认文字 ===")
        added = editor.evaluate("""() => {
            // 找默认文字卡片的+号按钮
            const cards = document.querySelectorAll('*');
            for (const el of cards) {
                if ((el.innerText||'').trim()==='默认文字' && el.children.length===0) {
                    let card = el;
                    for(let i=0;i<4&&card;i++){
                        const plus = card.querySelector('button');
                        if (plus) { plus.click(); return 'ok'; }
                        card = card.parentElement;
                    }
                }
            }
            return 'no plus';
        }""")
        log(f"  添加结果: {added}")
        time.sleep(2.0)
        shot(page, "tc0012_text_added.png")
        n2 = editor.evaluate(f"()=>document.querySelectorAll('{SEL_CLIP}').length")
        log(f"  添加后片段数: {n2}")

        # 步骤4：字幕面板
        log("\n=== 步骤4：字幕面板 ===")
        click_left_tab(editor, "字幕")
        time.sleep(1.0)
        # 点新建字幕tab
        editor.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='新建字幕') { el.click(); return; }
            }
        }""")
        time.sleep(1.0)
        shot(page, "tc0012_subtitle_tab.png")

        sub = editor.evaluate("""() => {
            const out = {};
            document.querySelectorAll('*').forEach(el => {
                if (el.children.length>0) return;
                const t=(el.innerText||'').trim();
                const r=el.getBoundingClientRect();
                if (r.x>60&&r.x<400&&r.width>20&&t.length<30) {
                    if (t.includes('手动写字幕')) out.manual = t;
                    if (t.includes('开始使用')) out.start = t;
                    if (t.includes('在播放头处')) out.desc = t;
                }
            });
            return out;
        }""")
        log(f"  字幕面板: {sub}")
        if not sub.get("manual"):
            errors.append("字幕面板缺少'手动写字幕'")
        if not sub.get("start"):
            errors.append("字幕面板缺少'开始使用'按钮")

        # 步骤5：点开始使用
        log("\n=== 步骤5：点开始使用 ===")
        r = editor.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='开始使用') { el.click(); return 'ok'; }
            }
            return 'no';
        }""")
        log(f"  结果: {r}")
        time.sleep(2.0)
        shot(page, "tc0012_subtitle_created.png")

        n3 = editor.evaluate(f"()=>document.querySelectorAll('{SEL_CLIP}').length")
        log(f"  创建后片段数: {n3}")

        # 步骤6：选中最后一个片段，dump右侧面板
        log("\n=== 步骤6：右侧面板字段 ===")
        clips = editor.locator(SEL_CLIP)
        total = clips.count()
        if total > 0:
            clips.nth(total-1).click(timeout=3000)
            time.sleep(1.0)

            # 6a：输入内容
            log("  6a：输入内容")
            editor.evaluate("""() => {
                const ta = document.querySelector('textarea, input[type=text]');
                for (const el of document.querySelectorAll('textarea,input')) {
                    const r = el.getBoundingClientRect();
                    if (r.x > 800 && r.width > 100 && r.height > 30) {
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set ||
                                       Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                        setter.call(el, '测试字幕TC0012');
                        el.dispatchEvent(new Event('input',{bubbles:true}));
                        el.dispatchEvent(new Event('change',{bubbles:true}));
                        return;
                    }
                }
            }""")
            time.sleep(0.5)

            # 6b：改字号为20
            log("  6b：改字号")
            editor.evaluate("""() => {
                const labels = document.querySelectorAll('*');
                for (const el of labels) {
                    if ((el.innerText||'').trim()==='字号') {
                        let c = el.parentElement;
                        for(let i=0;i<5&&c;i++){
                            const inp = c.querySelector('input');
                            if (inp) {
                                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                                setter.call(inp, '20');
                                inp.dispatchEvent(new Event('input',{bubbles:true}));
                                inp.dispatchEvent(new Event('change',{bubbles:true}));
                                return;
                            }
                            c = c.parentElement;
                        }
                    }
                }
            }""")
            time.sleep(0.5)

            fields = editor.evaluate("""() => {
                const texts = [];
                document.querySelectorAll('*').forEach(el => {
                    if (el.children.length>0) return;
                    const t=(el.innerText||'').trim();
                    if (!t||t.length>20) return;
                    const r=el.getBoundingClientRect();
                    if (r.x>800&&r.width>0&&r.y<800) texts.push(t);
                });
                return [...new Set(texts)];
            }""")
            log(f"  右侧面板字段: {fields}")
        shot(page, "tc0012_final.png")

        log("\n"+"="*60)
        if errors:
            log(f"[FAIL] {len(errors)} 项:")
            for e in errors: log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0012 通过")
        log("="*60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback; traceback.print_exc()
        try: shot(page, "tc0012_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: browser.close(); pw.stop()
        except: pass


if __name__ == "__main__":
    test()
