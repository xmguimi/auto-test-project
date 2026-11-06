# -*- coding: utf-8 -*-
"""
TC0015 自动化测试：剪辑工作台-转场（纯DOM元素定位）
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
    """找卡片文本对应的+号按钮：找叶子文本→向上找卡片容器→点button。"""
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
    """通过DOM找素材卡片位置，拖到时间线。"""
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

def test():
    log("=== TC0015：转场（纯元素定位） ===")
    errors=[]
    pw=sync_playwright().start(); b=pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    page=next((p for p in b.contexts[0].pages if WT in (p.title() or "")), b.contexts[0].pages[0])
    ed=next(f for f in page.frames if "opencut" in (f.url or ""))
    time.sleep(3)
    try:
        # 步骤1：转场列表
        log("\n=== 步骤1：转场列表 ===")
        click_left_tab(ed, "转场")
        time.sleep(1.5)
        trans = ed.evaluate("""() => {
            const exp=['叠化','淡入黑','淡出白','向左划像','向右划像','向上划像'];
            const f=[];
            document.querySelectorAll('*').forEach(el=>{
                if(el.children.length>0) return;
                const t=(el.innerText||'').trim();
                const r=el.getBoundingClientRect();
                if(r.x>60&&r.x<400&&r.y>150&&r.y<700&&exp.includes(t)) f.push(t);
            });
            return [...new Set(f)];
        }""")
        log(f"  转场: {trans}")
        for t in ['叠化','淡入黑','淡出白','向左划像','向右划像','向上划像']:
            if t not in trans: errors.append(f"缺少转场: {t}")

        # 说明文字
        has_desc = ed.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if ((el.innerText||'').includes('拖到两个片段') && el.getBoundingClientRect().x>60) return true;
            }
            return false;
        }""")
        log(f"  说明文字: {has_desc}")
        if not has_desc: errors.append("缺少说明文字")
        shot(page,"tc0015_list.png")

        # 步骤2：确保两个片段
        log("\n=== 步骤2：准备两个片段 ===")
        n = ed.evaluate(f"()=>document.querySelectorAll('{SEL}').length")
        if n < 2:
            click_left_tab(ed, "素材")
            time.sleep(2)
            # 拖第一个（如果还没有）
            if n < 1:
                drag_asset_to_timeline(ed, page, "羊群奔跑.mp4")
                time.sleep(1)
            # 拖第二个
            drag_asset_to_timeline(ed, page, "牛来啦.mp4")
            time.sleep(1)
        n = ed.evaluate(f"()=>document.querySelectorAll('{SEL}').length")
        log(f"  片段数: {n}")
        if n < 2:
            errors.append(f"片段数不足2（实际{n}）")
        else:
            # 步骤3：选中第一个片段，点叠化+号
            log("\n=== 步骤3：应用叠化转场 ===")
            ed.evaluate(f"()=>{{const els=document.querySelectorAll('{SEL}'); if(els[0]) els[0].click();}}")
            time.sleep(1)
            click_left_tab(ed, "转场")
            time.sleep(1.5)
            r = find_card_plus(ed, "叠化")
            log(f"  点叠化+号: {r}")
            time.sleep(2)
            shot(page,"tc0015_applied.png")

            # 步骤4：右侧面板
            log("\n=== 步骤4：右侧面板 ===")
            fields = ed.evaluate("""() => {
                const r=[];
                document.querySelectorAll('*').forEach(el=>{
                    if(el.children.length>0) return;
                    const t=(el.innerText||'').trim();
                    if(!t||t.length>15) return;
                    const b=el.getBoundingClientRect();
                    if(b.x>800&&b.width>0&&b.y<800) r.push(t);
                });
                return [...new Set(r)];
            }""")
            log(f"  字段: {fields}")
            if '类型' not in fields: errors.append("缺少类型字段")
            if '时长' not in fields: errors.append("缺少时长字段")
            shot(page,"tc0015_final.png")

        log("\n"+"="*60)
        if errors:
            log(f"[FAIL] {len(errors)}项:")
            for e in errors: log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0015 通过")
    except Exception as e:
        log(f"[ERROR] {e}"); import traceback; traceback.print_exc()
        try: shot(page,"tc0015_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: b.close(); pw.stop()
        except: pass

if __name__=="__main__": test()
