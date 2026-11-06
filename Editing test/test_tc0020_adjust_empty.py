# -*- coding: utf-8 -*-
"""
TC0020 自动化测试：剪辑工作台-调整未选中提示（纯DOM元素定位）
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

def test():
    log("=== TC0020：调整未选中提示 ===")
    errors=[]
    pw=sync_playwright().start(); b=pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    page=next((p for p in b.contexts[0].pages if WT in (p.title() or "")), b.contexts[0].pages[0])
    ed=next(f for f in page.frames if "opencut" in (f.url or ""))
    time.sleep(3)
    try:
        # 步骤1：取消选中，点调整
        log("\n=== 步骤1：未选中片段点调整 ===")
        ed.evaluate("()=>document.body.click()")
        time.sleep(0.5)
        click_left_tab(ed, "调整")
        time.sleep(2)
        has_tip = ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').includes('先在时间线中选中')) return true;
            }
            return false;
        }""")
        log(f"  提示文字: {has_tip}")
        if not has_tip: errors.append("缺少提示文字")
        shot(page,"tc0020_tip.png")

        log("\n"+"="*60)
        if errors:
            log(f"[FAIL] {len(errors)}项:"); [log(f"  - {e}") for e in errors]; sys.exit(1)
        log("[PASS] TC0020 通过")
    except Exception as e:
        log(f"[ERROR] {e}")
        try: shot(page,"tc0020_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: b.close(); pw.stop()
        except: pass

if __name__=="__main__": test()
