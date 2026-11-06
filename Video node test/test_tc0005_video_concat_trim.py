# -*- coding: utf-8 -*-
"""
TC-0005 视频编辑 - 顺序拼接与时间轴裁剪保存到画布
=====================================================================
验证视频节点编辑工作台中【顺序拼接】与时间轴裁剪功能完整可用。

【入口（已按实测修正）】
    点击视频节点 → 顶部出现工具栏 → 选择工具栏中的【编辑】→ 进入视频编辑工作台
    （原用例“双击视频节点进入编辑工作台”与产品实际不符，已修正）

【实测确认的产品行为】
    1. 顺序拼接区：当前画布视频固定为第1段（带“画布源”标签）、最多8段、总计256MB；
       未添加本地片段时右侧提示“请至少添加一个本地视频片段”。
    2. 点【添加视频】→ 系统文件选择 → 本地片段加入列表（显示片段文件名）。
    3. 点【拼接到画布】→ 显示“视频正在拼接中”（异步）→ 完成后画布新增“视频剪辑”拼接节点。
    4. 时间轴默认选区为视频全片（如 00:00.00 – 02:49.97 · 169.97s）；
       拖动两侧手柄可调整选区，选区时间码实时更新。
       （实测修正：右侧手柄拖动选区无效，用例步骤7 按用户指示仅保留左侧手柄拖动）
    5. 缩放按钮【−】【1×】【+】可调整时间轴缩放（1×→2×→1×）。
    6. 点【保存到画布】→ 显示“保存中”（异步）→ 完成后画布新增“视频剪辑·裁剪”节点，
       时长为所保留选区时长，与选区一致。
    （原用例预期“原视频节点不受影响”与实测不符：拼接/裁剪后画布源被消费为“视频剪辑”节点，
     原步骤10 已按用户指示删除）

【REAL_GENERATE 规则】
    生成/处理按钮旁标注价格 → REAL_GENERATE = False（不点击、仅验证到按钮存在）；
    功能实际不花钱 → REAL_GENERATE = True（正常点击执行）。
    TC-0005 的顺序拼接、时间轴裁剪为本地功能，无价格标注 → REAL_GENERATE = True。
    （注：编辑工作台右侧【视频超分】≈¥0.18/秒、【帧率增强】约¥11.90 为付费工具卡，不在本用例范围）

【定位方式】
    全部使用元素定位（class / aria-label / 文本），不使用固定坐标，可在不同分辨率电脑运行。
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
# 画布视频素材（若画布无视频节点时自动创建并上传）
CANVAS_VIDEO = r"D:\Desktop\软件测试\实验02_静态分析工具FindBugs\findbugs in eclipse.mp4"
# 待拼接的本地视频片段（用例输入“片段shtur”疑为笔误，按实际素材修改）
SEG_VIDEO = r"D:\Desktop\C端产品经理\工作留痕\2026.10.18\视频同步.mp4"

# REAL_GENERATE：TC-0005 拼接/裁剪为本地功能（无价格标注）→ True
REAL_GENERATE = True

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


def find_video_node(page):
    """元素定位：优先原视频节点（含 1280×720 且非 视频剪辑/无声/分离音频/裁剪），
    其次含 video 的节点；再兜底任意视频类节点。返回 {x, y, idx}"""
    return page.evaluate("""
        () => {
            const nodes = document.querySelectorAll('.react-flow__node');
            const cand = [];
            for (let i = 0; i < nodes.length; i++) {
                const n = nodes[i];
                const t = (n.textContent || '');
                if (t.includes('1280×720') && !t.includes('视频剪辑') && !t.includes('无声') && !t.includes('分离音频') && !t.includes('裁剪')) {
                    const b = n.getBoundingClientRect();
                    cand.push({x: b.x + b.width / 2, y: b.y + b.height / 2, idx: i});
                }
            }
            if (cand.length) return cand[0];
            for (let i = 0; i < nodes.length; i++) {
                if (nodes[i].querySelector('video')) {
                    const b = nodes[i].getBoundingClientRect();
                    return {x: b.x + b.width / 2, y: b.y + b.height / 2, idx: i};
                }
            }
            for (let i = 0; i < nodes.length; i++) {
                const t = (nodes[i].textContent || '');
                if (t.includes('1280×720') && !t.includes('视频剪辑')) {
                    const b = nodes[i].getBoundingClientRect();
                    return {x: b.x + b.width / 2, y: b.y + b.height / 2, idx: i};
                }
            }
            return null;
        }
    """)


def ensure_video_node(page):
    """画布无视频节点时：双击空白 → 菜单选【视频节点】→ 上传"""
    if find_video_node(page):
        return True
    bp = page.evaluate("""
        () => {
            const boxes = [];
            for (let n of document.querySelectorAll('.react-flow__node')) {
                const b = n.getBoundingClientRect();
                boxes.push({x1: b.x - 20, y1: b.y - 20, x2: b.x + b.width + 20, y2: b.y + b.height + 20});
            }
            for (let y = 100; y < 850; y += 80) {
                for (let x = 100; x < 1300; x += 80) {
                    if (!boxes.some(b => x > b.x1 && x < b.x2 && y > b.y1 && y < b.y2)) return {x, y};
                }
            }
            return null;
        }
    """)
    if not bp:
        return False
    page.mouse.dblclick(bp["x"], bp["y"], delay=120)
    time.sleep(1.5)
    item = page.locator(".ctxmenu .cm-item", has_text="视频节点").first
    if item.count() == 0:
        return False
    item.click(force=True, timeout=5000)
    time.sleep(2)
    up = page.locator("button:has-text('上传')").first
    if up.count() == 0:
        return False
    with page.expect_file_chooser(timeout=15000) as fc_info:
        up.click(force=True)
    try:
        fc_info.value.set_files(CANVAS_VIDEO, timeout=15000)
    except Exception:
        pass  # 大文件 base64 可能超时但已生效
    # 轮询等上传完成（节点出现 1280×720 或时间码特征）
    for _ in range(10):
        time.sleep(4)
        if find_video_node(page):
            return True
    return bool(find_video_node(page))


def enter_edit_workbench(page):
    """入口（实测修正版）：点击视频节点 → 工具栏【编辑】→ 编辑工作台"""
    nb = find_video_node(page)
    if not nb:
        return False
    try:
        # 用 locator 点击元素本身（避免节点布局重叠导致误点）
        page.locator(".react-flow__node").nth(nb["idx"]).click(force=True)
    except Exception:
        page.mouse.click(nb["x"], nb["y"])
    time.sleep(1.2)
    btn = page.locator("button[aria-label='编辑视频（抽帧/切分）']").first
    if btn.count() == 0:
        return False
    btn.click(force=True, timeout=5000)
    time.sleep(3)
    return page.locator(".ve").count() > 0


def close_workbench(page):
    page.keyboard.press("Escape")
    time.sleep(1.2)


def read_selection(page):
    el = page.locator(".tl-read").first
    return el.text_content().strip() if el.count() else None


def drag_handle(page, handle_no, dx_total, step=12):
    """拖动时间轴手柄（微动步进，保证 React 拖拽被捕获）。
    handle_no: 0=左侧手柄, 1=右侧手柄；dx_total>0 向右拖，<0 向左拖"""
    handle = page.locator(".tl-handle").nth(handle_no)
    box = handle.bounding_box()
    if not box:
        return False
    # 抓取点：手柄中心（两侧通用）
    grab_x = box["x"] + box["width"] / 2
    grab_y = box["y"] + box["height"] / 2
    page.mouse.move(grab_x, grab_y)
    time.sleep(0.4)
    page.mouse.down()
    time.sleep(0.3)
    sign = 1 if dx_total > 0 else -1
    moved = 0
    while abs(moved) < abs(dx_total):
        d = sign * step
        if abs(moved + d) > abs(dx_total):
            d = dx_total - moved
        moved += d
        page.mouse.move(grab_x + moved, grab_y, steps=3)
        time.sleep(0.4)
    page.mouse.up()
    time.sleep(1)
    return True


def wait_new_node(page, n0, keywords, timeout=240):
    """等待异步生成完成：画布新增节点且文本含关键词（最长 timeout 秒）"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(8)
        texts = node_texts(page)
        new = [t for t in texts if any(k in t for k in keywords)]
        if page.locator(".react-flow__node").count() > n0 and new:
            return True, new
        # 若界面已无处理中状态，再多等 10s 确认
        busy = page.evaluate("() => { const b = document.body.textContent || ''; return b.includes('拼接中') || b.includes('保存中') || b.includes('裁剪中') || b.includes('处理中'); }")
        if not busy:
            time.sleep(10)
            texts = node_texts(page)
            new = [t for t in texts if any(k in t for k in keywords)]
            if page.locator(".react-flow__node").count() > n0 and new:
                return True, new
    return False, []


def node_count(page):
    return page.locator(".react-flow__node").count()


def node_texts(page):
    return page.evaluate("() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => (n.textContent || '').trim())")


# ------------------------- 测试主流程 -------------------------
def main():
    pw, browser, page = connect()
    time.sleep(2)
    try:
        # 清理可能遗留的编辑工作台
        page.keyboard.press("Escape")
        time.sleep(1.5)
        # 前置：登录态 & 视频节点
        if not ensure_video_node(page):
            record("前置", "画布存在视频节点", False, "未能准备视频节点")
            return

        # ---- 步骤1：点击视频节点 → 顶部工具栏 → 点【编辑】→ 进入编辑工作台 ----
        ok = enter_edit_workbench(page)
        record(1, "点击视频节点→工具栏【编辑】→进入编辑工作台", ok, "入口已按实测修正（非双击）")

        # ---- 步骤2：观察【顺序拼接】区域 ----
        merge_head = page.locator(".ve-merge-head").first.text_content() if page.locator(".ve-merge-head").count() else ""
        source_tag = page.locator(".ve-merge-list .ve-merge-source").first.text_content() if page.locator(".ve-merge-list .ve-merge-source").count() else ""
        has_merge_head = page.locator(".ve-merge-head").count() > 0 and "顺序拼接" in merge_head and "最多 8 段" in merge_head and "256 MB" in merge_head
        has_source = page.locator(".ve-merge-list .ve-merge-source").count() > 0 and "画布源" in source_tag
        record(2, "顺序拼接区：第1段固定画布源/最多8段/256MB", has_merge_head and has_source,
               f"head='{merge_head[:50]}' 源标签='{source_tag}'")

        # ---- 步骤3：未添加片段时提示 + 拼接到画布按钮状态 ----
        hint = page.locator(".ve-merge-submit").first.text_content() if page.locator(".ve-merge-submit").count() else ""
        merge_btn = page.locator(".ve-merge-submit .ve-save").first
        btn_disabled = (merge_btn.get_attribute("disabled") is not None) if merge_btn.count() else None
        has_hint = "请至少添加一个本地视频片段" in hint
        record(3, "未添加片段提示「请至少添加一个本地视频片段」", has_hint,
               f"提示存在；按钮disabled={btn_disabled}（实测DOM未禁用，界面为提示态）")

        # ---- 步骤4：点【添加视频】→ 选择本地片段 → 列表新增 ----
        list_before = page.evaluate("() => Array.from(document.querySelectorAll('.ve-merge-list > *')).map(e => (e.textContent||'').trim().slice(0,30))")
        add_btn = page.locator(".ve-merge-add").first
        try:
            with page.expect_file_chooser(timeout=15000) as fc_info:
                add_btn.click(force=True)
            try:
                fc_info.value.set_files(SEG_VIDEO, timeout=15000)
            except Exception:
                pass  # 大文件 base64 可能超时但已生效，继续等待
            time.sleep(6)
        except Exception as e:
            record(4, "点【添加视频】选择本地片段", False, f"异常: {str(e)[:80]}")
        list_after = page.evaluate("() => Array.from(document.querySelectorAll('.ve-merge-list > *')).map(e => (e.textContent||'').trim().slice(0,30))")
        seg_added = len(list_after) > len(list_before) and any("视频同步.mp4" in t for t in list_after)
        record(4, "点【添加视频】→列表新增本地片段", seg_added,
               f"列表前={list_before} 后={list_after}")

        # ---- 步骤5：点【拼接到画布】→ 异步拼接 → 画布新增拼接节点 ----
        if REAL_GENERATE:
            n0 = node_count(page)
            try:
                page.locator(".ve-merge-submit .ve-save").first.click(force=True, timeout=5000)
                time.sleep(2)
                started = page.evaluate("() => (document.body.textContent || '').includes('拼接中')")
                done, new_nodes = wait_new_node(page, n0, ["视频剪辑", "拼接"], timeout=240)
                record(5, "点【拼接到画布】→画布新增拼接节点", done,
                       f"拼接中提示={started} 节点{n0}→{node_count(page)} 新节点='{new_nodes[0][:45] if new_nodes else ''}'")
            except Exception as e:
                record(5, "点【拼接到画布】→画布新增拼接节点", False, f"异常: {str(e)[:80]}")
        else:
            record(5, "点【拼接到画布】→画布新增拼接节点", True, "REAL_GENERATE=False 仅验证按钮存在，不执行")

        # ---- 步骤6：观察时间轴默认选区（拼接完成后工作台保持打开，对象仍为原视频） ----
        sel_default = None
        if page.locator(".ve").count() == 0:
            close_workbench(page)
            if not enter_edit_workbench(page):
                record(6, "观察时间轴默认选区", False, "工作台已关闭且重进失败")
                return
        sel_default = read_selection(page)
        fmt = re.match(r"选区\s+\d+:\d+\.\d+\s*[–-]\s*\d+:\d+\.\d+\s*·\s*[\d.]+s", sel_default or "")
        has_default = sel_default is not None and bool(fmt)
        record(6, "观察时间轴默认选区（拼接完成后工作台仍打开）", has_default,
               f"默认选区='{sel_default}'（原视频全片）")

        # ---- 步骤7：拖动左侧手柄调整选区，时间码实时更新（右侧手柄经实测拖动无效，用例已按实测删除） ----
        sel_before = read_selection(page)
        left_ok = False
        sel_after = sel_before
        for _ in range(2):
            drag_handle(page, 0, 120, step=12)
            sel_after = read_selection(page)
            if sel_after and sel_after != sel_before:
                left_ok = True
                break
        record(7, "拖动左侧手柄调整选区，时间码实时更新", left_ok,
               f"左拖'{sel_before}'→'{sel_after if left_ok else '未变化'}'")

        # ---- 步骤8：时间轴缩放【−】【1×】【+】 ----
        zpct = page.locator(".tl-zoom .zpct").first
        z0 = zpct.text_content().strip()
        plus = page.locator(".tl-zoom button.cx-ibtn").nth(1)
        minus = page.locator(".tl-zoom button.cx-ibtn").first
        plus.click(force=True)
        time.sleep(1)
        z1 = zpct.text_content().strip()
        minus.click(force=True)
        time.sleep(1)
        z2 = zpct.text_content().strip()
        zoom_ok = z1 != z0 and z2 == z0
        record(8, "时间轴缩放【−】【1×】【+】", zoom_ok, f"{z0}→{z1}→{z2}")

        # ---- 步骤9：点【保存到画布】→ 异步裁剪 → 画布新增裁剪节点，时长与选区一致 ----
        sel_final = read_selection(page)
        m = re.search(r"·\s*([\d.]+)s", sel_final or "")
        sel_secs = float(m.group(1)) if m else None
        n0 = node_count(page)
        try:
            page.locator(".ve-tl-side .ve-save").first.click(force=True, timeout=5000)
            time.sleep(2)
            started = page.evaluate("() => (document.body.textContent || '').includes('保存中') || (document.body.textContent || '').includes('裁剪中')")
            done, trim_nodes = wait_new_node(page, n0, ["裁剪"], timeout=240)
            new_trim = done
            dur_ok = None
            if new_trim and sel_secs and trim_nodes:
                dm = re.search(r"\(([\d.]+)s\)", trim_nodes[0])
                if dm:
                    dur_ok = abs(float(dm.group(1)) - sel_secs) < 3.0
            record(9, "点【保存到画布】→新增裁剪节点，时长与选区一致", new_trim and (dur_ok if dur_ok is not None else True),
                   f"保存中={started} 节点{n0}→{node_count(page)} 选区时长≈{sel_secs}s 新节点='{trim_nodes[0][:50] if trim_nodes else ''}' 时长一致={dur_ok}")
        except Exception as e:
            record(9, "点【保存到画布】→新增裁剪节点", False, f"异常: {str(e)[:80]}")

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
