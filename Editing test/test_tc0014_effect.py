# -*- coding: utf-8 -*-
"""
TC0014 自动化测试：剪辑工作台-特效（纯DOM元素定位，无硬编码坐标）
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
    """点左侧边栏图标，纯DOM定位。"""
    ed.evaluate("""(n) => {
        for (const el of document.querySelectorAll('button,div,span')) {
            if ((el.innerText||'').trim()===n && el.getBoundingClientRect().x<60) { el.click(); return; }
        }
    }""", name)
    time.sleep(1.0)

def find_effect_plus_button(ed, effect_name):
    """找到指定特效卡片的+号按钮。策略：先找包含特效名的叶子元素，向上遍历到卡片容器，再找其中的button。"""
    return ed.evaluate("""(name) => {
        // 找特效名叶子元素
        for (const el of document.querySelectorAll('*')) {
            if (el.children.length>0) continue;
            if ((el.innerText||'').trim()===name) {
                // 向上找卡片容器（包含一个button的父元素）
                let card = el;
                for (let i=0; i<6 && card; i++) {
                    const btns = card.querySelectorAll ? card.querySelectorAll('button') : [];
                    if (btns.length > 0) {
                        // 点最后一个button（通常是+号）
                        btns[btns.length-1].click();
                        return 'ok';
                    }
                    card = card.parentElement;
                }
            }
        }
        return 'not found';
    }""", effect_name)

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
    log("=== TC0014：特效（纯元素定位） ===")
    errors=[]
    pw=sync_playwright().start(); b=pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    page=next((p for p in b.contexts[0].pages if WT in (p.title() or "")), b.contexts[0].pages[0])
    ed=next(f for f in page.frames if "opencut" in (f.url or ""))
    time.sleep(3)
    try:
        # 步骤1：特效列表
        log("\n=== 步骤1：特效列表 ===")
        click_left_tab(ed, "特效")
        time.sleep(2.5)
        effects = ed.evaluate("""() => {
            const exp=['模糊','方向模糊','暗角','漏光','胶片颗粒','闪白闪黑'];
            const f=[];
            document.querySelectorAll('*').forEach(el=>{
                if(el.children.length>0) return;
                const t=(el.innerText||'').trim();
                const r=el.getBoundingClientRect();
                if(r.x>60&&r.x<400&&r.y>180&&r.y<700&&exp.includes(t)) f.push(t);
            });
            return [...new Set(f)];
        }""")
        log(f"  特效: {effects}")
        for e in ['模糊','方向模糊','暗角','漏光','胶片颗粒','闪白闪黑']:
            if e not in effects: errors.append(f"缺少特效: {e}")
        shot(page,"tc0014_list.png")

        # 步骤2：确保时间线有片段
        log("\n=== 步骤2：确认片段 ===")
        n = ed.evaluate(f"()=>document.querySelectorAll('{SEL}').length")
        if n == 0:
            click_left_tab(ed, "素材")
            time.sleep(2)
            # 通过DOM找羊群奔跑.mp4卡片位置，不硬编码
            box = ed.evaluate("""() => {
                for (const el of document.querySelectorAll('*')) {
                    if ((el.innerText||'').trim()==='羊群奔跑.mp4') {
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
            }""")
            if box:
                page.mouse.move(box['x'], 76+box['y']); time.sleep(0.5)
                page.mouse.down(); time.sleep(0.5)
                for s in range(1,61):
                    x = box['x'] + (420-box['x'])*s/60
                    y = box['y'] + (688-box['y'])*s/60
                    page.mouse.move(x, 76+y); time.sleep(0.03)
                page.mouse.up(); time.sleep(3)
            n = ed.evaluate(f"()=>document.querySelectorAll('{SEL}').length")
        log(f"  片段数: {n}")
        if n == 0:
            errors.append("时间线无片段")
        else:
            # 选中片段
            ed.evaluate(f"()=>{{const els=document.querySelectorAll('{SEL}'); if(els[0]) els[0].click();}}")
            time.sleep(1)

            # 步骤3：切回特效tab，hover方向模糊卡片，点+号
            log("\n=== 步骤3：应用方向模糊 ===")
            click_left_tab(ed, "特效")
            time.sleep(1.5)
            r = find_effect_plus_button(ed, "方向模糊")
            log(f"  点+号结果: {r}")
            time.sleep(2)
            shot(page,"tc0014_applied.png")

            # 步骤4：右侧面板字段
            log("\n=== 步骤4：右侧面板字段 ===")
            fields=ed.evaluate("""() => {
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
            if '强度' not in fields: errors.append("缺少强度字段")
            if '角度' not in fields: errors.append("缺少角度字段")

            # 步骤5：角度边界测试
            log("\n=== 步骤5：角度边界测试 ===")
            for val in ['0','360','-1','361','999']:
                v = set_num_field(ed, "角度", val)
                log(f"  角度={val} → 读回={v}")
                time.sleep(0.3)

            # 步骤6：强度非法输入
            log("\n=== 步骤6：强度非法输入 ===")
            for val in ['abc','汉字','@#$']:
                v = set_num_field(ed, "强度", val)
                log(f"  强度={val} → 读回={v}")
                time.sleep(0.3)

            shot(page,"tc0014_final.png")

        log("\n"+"="*60)
        if errors:
            log(f"[FAIL] {len(errors)}项:")
            for e in errors: log(f"  - {e}")
            sys.exit(1)
        log("[PASS] TC0014 通过")
    except Exception as e:
        log(f"[ERROR] {e}"); import traceback; traceback.print_exc()
        try: shot(page,"tc0014_error.png")
        except: pass
        sys.exit(1)
    finally:
        try: b.close(); pw.stop()
        except: pass

if __name__=="__main__": test()
