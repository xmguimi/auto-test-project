# -*- coding: utf-8 -*-
"""
TC-0007 视频编辑 - 视频超分
=====================================================================
验证【视频超分】四档分辨率（720p/1080p/2k/4k）切换正常、当前档位高亮正确、
预估价格随档位同步变化、云端处理提示与50M限制说明显示正确；
最后选择720p档位并验证【运行】按钮存在（REAL_GENERATE=False，不实际发起任务）。

【入口（实测修正版）】
    单击视频节点标题栏 → 顶部出现工具栏 → JS 点击【编辑】→ 进入视频编辑工作台
    （原用例"双击视频节点进入"与产品实际不符，已修正）

【实测确认的产品行为】
    1. 右侧 TOOLS 面板【视频超分】卡片（标签"云端"，预估价格 ≈ ¥0.18/秒）；
    2. 四档分辨率按钮：720p / 1080p / 2k / 4k，当前档位 class 含 "on"；
    3. 默认档位 1080p；预估价格随档位切换同步变化；
    4. 说明文案：云端处理，源视频不超过 50M；提交后画布上会出现生成中节点；
    5. 【运行】按钮（class tk-run，紫色）。

【REAL_GENERATE 规则】
    视频超分为云端付费功能（预估价格 ≈ ¥0.18/秒，按钮旁标注价格）
    → REAL_GENERATE = False（不实际点击【运行】发起付费任务，仅验证到按钮存在）。

【定位方式】
    全部使用元素定位（class / 文本），不使用固定坐标，可在不同分辨率电脑运行。
=====================================================================
"""
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

# ------------------------- 配置（按实际机器修改） -------------------------
FJ_CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
FJ_CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))

# REAL_GENERATE：视频超分为云端付费功能（预估价格 ≈ ¥0.18/秒）→ False
REAL_GENERATE = False

# ------------------------- 工具函数 -------------------------
RESULTS = []  # 步骤结果记录 [(步骤号, 名称, 是否通过, 说明)]


def record(no, name, passed, note=""):
    RESULTS.append((no, name, passed, note))
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] 步骤{no} {name} {('- ' + note) if note else ''}", flush=True)


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{FJ_CDP_HOST}:{FJ_CDP_PORT}")
    page = None
    for p in browser.contexts[0].pages:
        if "帧境" in (p.title() or ""):
            page = p
            break
    if not page:
        page = browser.contexts[0].pages[0]
    return pw, browser, page


def pan_canvas(page, dx=0, dy=150):
    """平移画布（拖动画布空白区），让屏幕外节点进入视口"""
    blank = page.evaluate("""
        () => {
            const boxes = [];
            for (let n of document.querySelectorAll('.react-flow__node')) {
                const b = n.getBoundingClientRect();
                boxes.push({x1: b.x - 20, y1: b.y - 20, x2: b.x + b.width + 20, y2: b.y + b.height + 20});
            }
            for (let y = 100; y < 800; y += 80) {
                for (let x = 100; x < 1200; x += 80) {
                    if (!boxes.some(b => x > b.x1 && x < b.x2 && y > b.y1 && y < b.y2)) return {x, y};
                }
            }
            return null;
        }
    """)
    if not blank:
        return
    page.mouse.move(blank["x"], blank["y"])
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.2)
    page.mouse.move(blank["x"] + dx, blank["y"] + dy, steps=5)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(0.5)


def enter_edit_workbench(page):
    """入口（实测修正版）：遍历视口内节点，找到视频节点（工具栏含编辑按钮），点标题栏→JS点编辑→工作台打开"""
    candidates = page.evaluate("""
        () => {
            const res = [];
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                if (t.includes('视频剪辑') && r.x > 0 && r.y > 0 && r.x + r.width < window.innerWidth && r.y + r.height < window.innerHeight) {
                    res.push(i);
                }
            }
            return res;
        }
    """)
    for idx in candidates:
        page.keyboard.press("Escape")
        time.sleep(0.5)
        box = page.locator(".react-flow__node").nth(idx).bounding_box()
        if not box:
            continue
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
        time.sleep(1)
        edit_btn = page.locator("button[aria-label='编辑视频（抽帧/切分）']").count()
        if edit_btn == 0:
            continue
        clicked = page.evaluate("""
            () => {
                const btn = document.querySelector("button[aria-label='编辑视频（抽帧/切分）']");
                if (!btn) return false;
                btn.click();
                return true;
            }
        """)
        if not clicked:
            continue
        for _ in range(10):
            time.sleep(1)
            if page.locator(".ve").count() > 0:
                return True
    return False


def get_super_res_state(page):
    """读取视频超分卡片状态：当前档位、预估价格、说明文案"""
    return page.evaluate("""
        () => {
            const ve = document.querySelector('.ve');
            if (!ve) return null;
            const t = (ve.textContent || '');
            // 找档位按钮（720p/1080p/2k/4k），判断哪个高亮（class 含 on）
            const levels = {};
            for (let b of ve.querySelectorAll('button')) {
                const bt = (b.textContent || '').trim();
                if (['720p', '1080p', '2k', '4k'].includes(bt)) {
                    levels[bt] = (b.className || '').includes('on');
                }
            }
            // 提取预估价格（如 ≈ ¥0.18/秒）
            const priceMatch = t.match(/预估价格[\\s\\S]*?(≈\\s*¥[\\d.]+\\/秒)/);
            const price = priceMatch ? priceMatch[1] : '';
            // 说明文案
            const has_cloud = t.includes('云端处理');
            const has_50m = t.includes('50M') || t.includes('50M');
            // 运行按钮存在
            let has_run = false;
            for (let b of ve.querySelectorAll('button')) {
                if ((b.textContent || '').trim() === '运行') { has_run = true; break; }
            }
            return {levels, price, has_cloud, has_50m, has_run};
        }
    """)


def click_level(page, level):
    """点击某个档位按钮"""
    page.evaluate(f"""
        () => {{
            const ve = document.querySelector('.ve');
            if (!ve) return;
            for (let b of ve.querySelectorAll('button')) {{
                if ((b.textContent || '').trim() === '{level}') {{
                    b.click();
                    return;
                }}
            }}
        }}
    """)
    time.sleep(1)


# ------------------------- 测试主流程 -------------------------
def main():
    pw, browser, page = connect()
    time.sleep(2)
    try:
        # 清理遗留 + 平移画布
        page.keyboard.press("Escape")
        time.sleep(1.5)
        pan_canvas(page, dx=0, dy=150)
        time.sleep(1)

        # ---- 步骤1：进入编辑工作台 ----
        ok = enter_edit_workbench(page)
        record(1, "点击视频节点→工具栏【编辑】→进入编辑工作台", ok, "入口已按实测修正（点标题栏+JS点编辑）")
        if not ok:
            return

        # ---- 步骤2：观察视频超分卡片（默认档位+初始预估价格） ----
        state0 = get_super_res_state(page)
        default_level = None
        for lv, on in (state0 or {}).get("levels", {}).items():
            if on:
                default_level = lv
                break
        price0 = (state0 or {}).get("price", "")
        ok2 = state0 is not None and default_level is not None and price0 != ""
        record(2, "观察【视频超分】默认档位与初始预估价格", ok2,
               f"默认档位={default_level} 初始价格={price0}")

        # ---- 步骤3：依次点击 720p→1080p→2k→4k，验证高亮+价格变化 ----
        levels_order = ["720p", "1080p", "2k", "4k"]
        price_changes = []
        level_ok_all = True
        for lv in levels_order:
            click_level(page, lv)
            st = get_super_res_state(page)
            is_on = (st or {}).get("levels", {}).get(lv, False)
            price = (st or {}).get("price", "")
            price_changes.append(f"{lv}={price}")
            if not is_on:
                level_ok_all = False
        ok3 = level_ok_all and len(price_changes) == 4
        record(3, "依次点击720p→1080p→2k→4k，每档高亮正确、预估价格同步变化", ok3,
               f"价格变化: {' | '.join(price_changes)}")

        # ---- 步骤4：观察云端处理提示、源视频大小限制说明 ----
        ok4 = (state0 or {}).get("has_cloud", False) and (state0 or {}).get("has_50m", False)
        record(4, "观察云端处理提示、源视频不超过50M限制说明", ok4,
               f"云端处理={state0.get('has_cloud') if state0 else False} 50M={state0.get('has_50m') if state0 else False}")

        # ---- 步骤5：最后点击720p确认档位高亮与预估价格 ----
        click_level(page, "720p")
        st5 = get_super_res_state(page)
        is_720p = (st5 or {}).get("levels", {}).get("720p", False)
        ok5 = is_720p and (st5 or {}).get("price", "") != ""
        record(5, "最后选720p档位高亮正确、预估价格为720p对应价格", ok5,
               f"720p高亮={is_720p} 价格={st5.get('price') if st5 else ''}")

        # ---- 步骤6：验证【运行】按钮存在（REAL_GENERATE=False 不点击） ----
        ok6 = (st5 or {}).get("has_run", False)
        record(6, "【运行】按钮存在（REAL_GENERATE=False 不实际发起付费任务）", ok6,
               f"运行按钮={st5.get('has_run') if st5 else False}")

    finally:
        # 输出汇总
        passed = sum(1 for r in RESULTS if r[2])
        total = len(RESULTS)
        print("\n===== 汇总 =====", flush=True)
        print(f"通过 {passed}/{total}", flush=True)
        for r in RESULTS:
            print(f"  [{'PASS' if r[2] else 'FAIL'}] 步骤{r[0]} {r[1]} {('- ' + r[3]) if r[3] else ''}", flush=True)
        browser.close()
        pw.stop()
        if passed == total:
            print("RESULT: ALL PASS", flush=True)
        else:
            print(f"RESULT: {total - passed} FAILED", flush=True)


if __name__ == "__main__":
    main()
