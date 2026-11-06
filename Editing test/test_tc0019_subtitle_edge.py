# -*- coding: utf-8 -*-
"""
TC0019 自动化测试：剪辑工作台-字幕内容边界输入（纯DOM元素定位）
环境变量：FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_HOST=os.getenv("FJ_CDP_HOST","localhost"); CDP_PORT=int(os.getenv("FJ_CDP_PORT","9222"))
WT=os.getenv("FJ_WINDOW_TITLE","帧境"); SHOT_DIR=Path(os.getenv("FJ_SHOT_DIR","screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

def log(m): print(m,flush=True)
def shot(p,n):
    try: p.screenshot(path=str(SHOT_DIR/n)); log(f"[SHOT] {n}")
    except: pass

def click_left_tab(ed, name):
    ed.evaluate("""(n) => {
        for (const el of document.querySelectorAll('button,div,span')) {
            if ((el.innerText||'').trim()===n && el.getBoundingClientRect().x<60) { el.click(); return; }
        }
    }""", name)
    time.sleep(1.5)

def set_num_field(ed, label, value):
    return ed.evaluate("""({label, val}) => {
        const inputs = document.querySelectorAll('input');
        for (const el of inputs) {
            const r = el.getBoundingClientRect();
            if (r.x <= 800 || r.width === 0 || el.type === 'file') continue;
            let c = el.parentElement;
            for (let i=0;i<6&&c;i++) {
                if ((c.innerText||'').includes(label)) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                    setter.call(el, String(val));
                    el.dispatchEvent(new Event('input',{bubbles:true}));
                    el.dispatchEvent(new Event('change',{bubbles:true}));
                    el.blur();
                    return el.value;
                }
                c = c.parentElement;
            }
        }
        return null;
    }""", {"label": label, "val": value})

def test():
    log("=== TC0019：字幕边界输入 ===")
    errors=[]
    pw=sync_playwright().start(); b=pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    page=next((p for p in b.contexts[0].pages if WT in (p.title() or "")), b.contexts[0].pages[0])
    ed=next(f for f in page.frames if "opencut" in (f.url or ""))
    time.sleep(3)
    try:
        # 步骤1：新建字幕
        log("\n=== 步骤1：新建字幕 ===")
        click_left_tab(ed, "字幕")
        time.sleep(2)
        ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='开始使用') { el.click(); return; }
            }
        }""")
        time.sleep(2)

        # 步骤2：数字字段边界测试
        log("\n=== 步骤2：字号边界测试 ===")
        for val in ['abc','汉字','@#$','0','-10','9999']:
            v = set_num_field(ed, "字号", val)
            log(f"  字号={val} → 读回={v}")
            time.sleep(0.3)
        shot(page,"tc0019_bounds.png")

        # 步骤3：空态
        log("\n=== 步骤3：未选中字幕空态 ===")
        ed.evaluate("()=>document.body.click()")
        time.sleep(1)
        has_empty = ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').includes('点击时间线上的元素')) return true;
            }
            return false;
        }""")
        log(f"  空态提示: {has_empty}")
        shot(page,"tc0019_empty.png")

        log("\n"+"="*60)
        log("[PASS] TC0019 通过（无崩溃）")
    except Exception as e:
        log(f"[ERROR] {e}")
        try: shot(page,"tc0019_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: b.close(); pw.stop()
        except: pass

if __name__=="__main__": test()
