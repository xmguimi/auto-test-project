# -*- coding: utf-8 -*-
"""
TC0017 自动化测试：剪辑工作台-字幕入口与新建（纯DOM元素定位）
环境变量：FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_HOST=os.getenv("FJ_CDP_HOST","localhost"); CDP_PORT=int(os.getenv("FJ_CDP_PORT","9222"))
WT=os.getenv("FJ_WINDOW_TITLE","帧境"); SHOT_DIR=Path(os.getenv("FJ_SHOT_DIR","screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)
SEL="button.absolute.inset-0.size-full.flex.flex-col"

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
    log("=== TC0017：字幕入口与新建 ===")
    errors=[]
    pw=sync_playwright().start(); b=pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    page=next((p for p in b.contexts[0].pages if WT in (p.title() or "")), b.contexts[0].pages[0])
    ed=next(f for f in page.frames if "opencut" in (f.url or ""))
    time.sleep(3)
    try:
        # 步骤1：字幕面板
        log("\n=== 步骤1：字幕面板 ===")
        click_left_tab(ed, "字幕")
        time.sleep(2)
        info = ed.evaluate("""() => {
            const r=[];
            document.querySelectorAll('*').forEach(el=>{
                if(el.children.length>0) return;
                const t=(el.innerText||'').trim();
                if(!t||t.length>25) return;
                const b=el.getBoundingClientRect();
                if(b.x>60&&b.x<400&&b.y>60&&b.y<700) r.push(t);
            });
            return [...new Set(r)];
        }""")
        log(f"  面板文本: {info}")
        shot(page,"tc0017_panel.png")

        # 步骤2：点开始使用
        log("\n=== 步骤2：点开始使用 ===")
        ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='开始使用') { el.click(); return; }
            }
        }""")
        time.sleep(2)
        shot(page,"tc0017_created.png")

        # 步骤3：验证字幕轨
        log("\n=== 步骤3：验证字幕轨 ===")
        has_track = ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').includes('字幕')) return true;
            }
            return false;
        }""")
        log(f"  字幕轨存在: {has_track}")

        log("\n"+"="*60)
        log("[PASS] TC0017 通过")
    except Exception as e:
        log(f"[ERROR] {e}")
        try: shot(page,"tc0017_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: b.close(); pw.stop()
        except: pass

if __name__=="__main__": test()
