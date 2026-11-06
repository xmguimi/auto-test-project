# -*- coding: utf-8 -*-
"""
TC0016 自动化测试：剪辑工作台-转场异常与边界（纯DOM元素定位）
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
    time.sleep(1.2)

def find_card_plus(ed, card_text):
    return ed.evaluate("""(name) => {
        for (const el of document.querySelectorAll('*')) {
            if (el.children.length>0) continue;
            if ((el.innerText||'').trim()===name) {
                let card = el;
                for (let i=0;i<6&&card;i++) {
                    const btns = card.querySelectorAll ? card.querySelectorAll('button') : [];
                    if (btns.length>0) {
                        btns[btns.length-1].click();
                        return 'ok';
                    }
                    card = card.parentElement;
                }
            }
        }
        return 'not found';
    }""", card_text)

def drag_asset_to_timeline(ed, page, asset_name):
    box = ed.evaluate("""(name) => {
        for (const el of document.querySelectorAll('*')) {
            if ((el.innerText||'').trim()===name) {
                let c=el;
                for(let i=0;i<6&&c;i++){
                    if(c.querySelector&&c.querySelector('img')){
                        const r=c.getBoundingClientRect();
                        return {x:r.x+r.width/2, y:r.y+r.height/2-10};
                    }
                    c=c.parentElement;
                }
            }
        }
        return null;
    }""", asset_name)
    if not box: return False
    page.mouse.move(box['x'],76+box['y']); time.sleep(0.4)
    page.mouse.down(); time.sleep(0.5)
    for s in range(1,61):
        x = box['x'] + (420-box['x'])*s/60
        y = box['y'] + (688-box['y'])*s/60
        page.mouse.move(x,76+y); time.sleep(0.03)
    page.mouse.up(); time.sleep(2.5)
    return True

def get_toast(ed):
    return ed.evaluate("""() => {
        for (const el of document.querySelectorAll('*')) {
            const t=(el.innerText||'').trim();
            if(t.includes('播放头')||t.includes('接缝')||t.includes('片段')||t.includes('先选中')) return t;
        }
        return null;
    }""")

def test():
    log("=== TC0016：转场异常与边界 ===")
    errors=[]
    pw=sync_playwright().start(); b=pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    page=next((p for p in b.contexts[0].pages if WT in (p.title() or "")), b.contexts[0].pages[0])
    ed=next(f for f in page.frames if "opencut" in (f.url or ""))
    time.sleep(3)
    try:
        # 步骤1：只有1个片段时点+号
        log("\n=== 步骤1：只有1个片段时点叠化+号 ===")
        n1 = ed.evaluate(f"()=>document.querySelectorAll('{SEL}').length")
        log(f"  当前片段数: {n1}")
        click_left_tab(ed, "转场")
        time.sleep(1.5)
        r1 = find_card_plus(ed, "叠化")
        time.sleep(1)
        toast1 = get_toast(ed)
        log(f"  点+号结果: {r1}, 提示: {toast1}")
        shot(page,"tc0016_one_clip.png")

        # 步骤2：拖第二个片段
        log("\n=== 步骤2：加第二个片段 ===")
        click_left_tab(ed, "素材")
        time.sleep(2)
        drag_asset_to_timeline(ed, page, "牛来啦.mp4")
        n2 = ed.evaluate(f"()=>document.querySelectorAll('{SEL}').length")
        log(f"  片段数: {n2}")

        # 步骤3：未选中片段时点+号
        log("\n=== 步骤3：未选中片段时点叠化+号 ===")
        ed.evaluate(f"()=>document.body.click()")
        time.sleep(0.5)
        click_left_tab(ed, "转场")
        time.sleep(1.5)
        r3 = find_card_plus(ed, "叠化")
        time.sleep(1)
        toast3 = get_toast(ed)
        log(f"  点+号: {r3}, 提示: {toast3}")

        # 步骤4：选中第一个片段加叠化
        log("\n=== 步骤4：选中片段加叠化 ===")
        ed.evaluate(f"()=>{{const els=document.querySelectorAll('{SEL}'); if(els[0]) els[0].click();}}")
        time.sleep(1)
        click_left_tab(ed, "转场")
        time.sleep(1.5)
        r4 = find_card_plus(ed, "叠化")
        time.sleep(2)
        log(f"  点叠化+号: {r4}")

        # 步骤5：重复加转场
        log("\n=== 步骤5：重复加转场 ===")
        r5 = find_card_plus(ed, "叠化")
        time.sleep(1)
        log(f"  再次点叠化+号: {r5}")

        # 步骤6：删除转场
        log("\n=== 步骤6：删除转场 ===")
        ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').trim()==='删除转场') { el.click(); return; }
            }
        }""")
        time.sleep(1.5)
        shot(page,"tc0016_deleted.png")

        log("\n"+"="*60)
        log("[PASS] TC0016 通过（无崩溃）")
    except Exception as e:
        log(f"[ERROR] {e}")
        try: shot(page,"tc0016_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: b.close(); pw.stop()
        except: pass

if __name__=="__main__": test()
