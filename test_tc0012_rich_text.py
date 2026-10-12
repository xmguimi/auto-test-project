"""
TC-0012 自动化测试：文本节点富文本格式编辑
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布 → 新建文本节点
    2. 双击节点进入编辑
    3. 输入三行文字：
        一个美丽的模特
        高
        瘦
    4. 选中第一行 → 点 H1/H2/H3 → 观察
    5. 选中"高" → 点 B（加粗）
    6. 选中"瘦" → 点 I（斜体）
    7. "高"所在行 → 点无序列表
    8. "瘦"所在行 → 点有序列表
    9. 文字末尾 → 点分割线
    10. 读取节点 innerHTML 验证格式

已知缺陷（用例记录）：
    - 颜色退出编辑不显示
    - 分割线按钮无反应

运行前置：
    pip install playwright requests
    python -m playwright install chromium
    帧境 AI 已带 --remote-debugging-port=9222 启动
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 9222
ROOT = Path(__file__).parent

LINE1 = "一个美丽的模特"
LINE2 = "高"
LINE3 = "瘦"

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"[SHOT] {name}")
    except Exception as e:
        print(f"[SHOT-FAIL] {name}: {e}")


def is_cdp_ready(port=PORT):
    try:
        r = requests.get(f"http://localhost:{port}/json/version", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")
    pages = browser.contexts[0].pages
    target = None
    for p in pages:
        if "帧境" in (p.title() or ""):
            target = p
            break
    if not target:
        target = pages[0]
    return pw, browser, target


# ============ 进入 3D 文本编辑 ============
def dblclick_canvas(page):
    print("\n=== 双击画布 ===")
    page.mouse.dblclick(600, 400)
    time.sleep(1.5)
    shot(page, "tc0012_after_dblclick_canvas.png")


def click_menu_item(page, text_keyword):
    print(f"\n=== 点菜单 '{text_keyword}' ===")
    try:
        loc = page.locator(".cm-item")
        for i in range(loc.count()):
            el = loc.nth(i)
            try:
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if text_keyword in t:
                    el.click(timeout=3000)
                    print(f"  [OK] 点击 [{i}] '{t[:30]}'")
                    return True
            except Exception:
                pass
    except Exception as e:
        print(f"  失败: {e}")
    raise RuntimeError(f"找不到菜单项 '{text_keyword}'")


def wait_for_new_node(page, before, timeout=15):
    print("\n=== 等待新节点 ===")
    start = time.time()
    while time.time() - start < timeout:
        cur = page.locator(".react-flow__node").count()
        if cur > before:
            print(f"  [OK] {before} → {cur}")
            return cur
        time.sleep(1)
    raise RuntimeError("新节点未出现")


def dblclick_node(page):
    print("\n=== 双击节点进入编辑 ===")
    node = page.locator(".react-flow__node").last
    box = node.bounding_box()
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.dblclick(cx, cy)
    time.sleep(1.5)
    shot(page, "tc0012_after_dblclick_node.png")


def find_editor(page):
    """找可编辑区域"""
    for sel in [
        "[contenteditable='true']",
        "[class*='ProseMirror']",
        "[class*='editor']",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    return el, sel
        except Exception:
            pass
    return None, None


# ============ 输入文字 ============
def input_lines(page, lines):
    print(f"\n=== 输入 {len(lines)} 行文字 ===")
    editor, sel = find_editor(page)
    if not editor:
        print("  [WARN] 没找到编辑区，直接 keyboard.type")
    else:
        print(f"  编辑区: {sel}")
        try:
            editor.click(timeout=3000)
            time.sleep(0.3)
        except Exception:
            pass

    # 清空
    page.keyboard.press("Control+A")
    time.sleep(0.2)
    page.keyboard.press("Delete")
    time.sleep(0.2)

    for i, line in enumerate(lines):
        for ch in line:
            page.keyboard.type(ch, delay=60)
        if i < len(lines) - 1:
            page.keyboard.press("Enter")
            time.sleep(0.2)
    time.sleep(0.5)
    shot(page, "tc0012_after_input.png")


def read_editor_html(page):
    """读取编辑区 HTML"""
    editor, _ = find_editor(page)
    if not editor:
        return ""
    try:
        return editor.inner_html()
    except Exception:
        return ""


# ============ 定位工具栏按钮 ============
def get_toolbar_buttons(page):
    """
    从节点上方的工具栏里，找所有按钮。
    工具栏一般在编辑区上方，y 小于编辑区 y。
    """
    print("\n=== 定位工具栏按钮 ===")
    editor, _ = find_editor(page)
    editor_y = 0
    if editor:
        box = editor.bounding_box()
        if box:
            editor_y = box["y"]
    print(f"  编辑区 y = {editor_y:.0f}")

    btns = page.locator("button")
    cnt = btns.count()
    toolbar = []
    for i in range(cnt):
        el = btns.nth(i)
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box:
                continue
            # 工具栏在编辑区上方 200px 内
            if editor_y - 200 < box["y"] < editor_y:
                text = (el.inner_text() or "").strip()
                title = el.get_attribute("title") or ""
                aria = el.get_attribute("aria-label") or ""
                label = text or title or aria
                toolbar.append({
                    "idx": i, "loc": el, "box": box,
                    "text": text, "title": title, "aria": aria,
                    "label": label,
                })
        except Exception:
            pass

    print(f"  编辑区上方按钮: {len(toolbar)} 个")
    for t in toolbar:
        b = t["box"]
        print(f"    [{t['idx']}] y={b['y']:.0f} x={b['x']:.0f} text='{t['text'][:15]}' title='{t['title'][:15]}' aria='{t['aria'][:15]}'")
    return toolbar


def find_button_by_keywords(page, keywords):
    """在工具栏里找 label 含关键词的按钮"""
    btns = page.locator("button")
    for i in range(btns.count()):
        el = btns.nth(i)
        try:
            if not el.is_visible():
                continue
            text = (el.inner_text() or "").strip()
            title = el.get_attribute("title") or ""
            aria = el.get_attribute("aria-label") or ""
            label = (text + " " + title + " " + aria).strip()
            for kw in keywords:
                if kw in label:
                    return el, label
        except Exception:
            pass
    return None, None


# ============ 选中文字 ============
def select_text(page, text, occurrence=1):
    """
    在编辑区里选中指定文字。
    策略：用 JS Range 精确选中。
    """
    print(f"  选中文字: '{text}' (第 {occurrence} 次出现)")
    editor, _ = find_editor(page)
    if not editor:
        print("    [WARN] 没有编辑区")
        return False

    result = editor.evaluate("""(el, args) => {
        const [text, occurrence] = args;
        // 遍历所有文本节点，找目标文字
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        let count = 0;
        let node;
        while (node = walker.nextNode()) {
            const idx = node.textContent.indexOf(text);
            if (idx >= 0) {
                count++;
                if (count === occurrence) {
                    const range = document.createRange();
                    range.setStart(node, idx);
                    range.setEnd(node, idx + text.length);
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                    el.focus();
                    return true;
                }
            }
        }
        return false;
    }""", [text, occurrence])

    print(f"    结果: {result}")
    time.sleep(0.4)
    return result


# ============ 点击工具栏按钮 ============
def click_format_button(page, keywords, label=""):
    """找并点击工具栏里的按钮"""
    print(f"\n  点击按钮 {label} (关键词 {keywords})")
    btn, found_label = find_button_by_keywords(page, keywords)
    if btn:
        try:
            btn.scroll_into_view_if_needed()
            time.sleep(0.2)
            btn.click(timeout=3000)
            print(f"    [OK] 点击了 '{found_label}'")
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"    点击失败: {e}")
            return False
    else:
        print(f"    [FAIL] 找不到含 {keywords} 的按钮")
        return False


# ============ 主流程 ============
def test_tc0012():
    print("=== TC-0012：文本节点富文本编辑 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {before}")

        # 1. 新建文本节点
        dblclick_canvas(page)
        click_menu_item(page, "文本节点")
        time.sleep(1.5)
        wait_for_new_node(page, before, timeout=15)

        # 2. 双击节点进入编辑
        dblclick_node(page)

        # 3. 输入三行文字
        input_lines(page, [LINE1, LINE2, LINE3])

        # 4. dump 工具栏按钮（第一次跑看结构）
        toolbar = get_toolbar_buttons(page)
        shot(page, "tc0012_after_toolbar_dump.png")

        results = {}

        # ============ 测试 H1 ============
        print("\n\n########## 测试 H1 ##########")
        if select_text(page, LINE1):
            ok = click_format_button(page, ["H1", "h1", "标题1"], "H1")
            results["H1"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            results["H1_applied"] = ("<h1" in html.lower())
            print(f"  HTML 含 <h1>: {results['H1_applied']}")
            shot(page, "tc0012_after_H1.png")

        # ============ 测试 H2 ============
        print("\n\n########## 测试 H2 ##########")
        if select_text(page, LINE1):
            ok = click_format_button(page, ["H2", "h2", "标题2"], "H2")
            results["H2"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            results["H2_applied"] = ("<h2" in html.lower())
            shot(page, "tc0012_after_H2.png")

        # ============ 测试 H3 ============
        print("\n\n########## 测试 H3 ##########")
        if select_text(page, LINE1):
            ok = click_format_button(page, ["H3", "h3", "标题3"], "H3")
            results["H3"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            results["H3_applied"] = ("<h3" in html.lower())
            shot(page, "tc0012_after_H3.png")

        # ============ 测试 加粗 B ============
        print("\n\n########## 测试 加粗 B ##########")
        if select_text(page, LINE2):
            ok = click_format_button(page, ["B", "加粗", "Bold", "bold"], "加粗")
            results["B"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            # 加粗一般是 <strong> 或 <b>
            results["B_applied"] = ("<strong>" in html.lower() or "<b>" in html.lower())
            print(f"  HTML 含 strong/b: {results['B_applied']}")
            shot(page, "tc0012_after_B.png")

        # ============ 测试 斜体 I ============
        print("\n\n########## 测试 斜体 I ##########")
        if select_text(page, LINE3):
            ok = click_format_button(page, ["I", "斜体", "Italic", "italic"], "斜体")
            results["I"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            results["I_applied"] = ("<em>" in html.lower() or "<i>" in html.lower())
            print(f"  HTML 含 em/i: {results['I_applied']}")
            shot(page, "tc0012_after_I.png")

        # ============ 测试 无序列表 ============
        print("\n\n########## 测试 无序列表 ##########")
        if select_text(page, LINE2):
            ok = click_format_button(page, ["无序列表", "无序", "•", "bullet", "ul"], "无序列表")
            results["UL"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            results["UL_applied"] = ("<ul" in html.lower())
            shot(page, "tc0012_after_UL.png")

        # ============ 测试 有序列表 ============
        print("\n\n########## 测试 有序列表 ##########")
        if select_text(page, LINE3):
            ok = click_format_button(page, ["有序列表", "有序", "1.", "ordered", "ol"], "有序列表")
            results["OL"] = ok
            time.sleep(0.5)
            html = read_editor_html(page)
            results["OL_applied"] = ("<ol" in html.lower())
            shot(page, "tc0012_after_OL.png")

        # ============ 测试 分割线 ============
        print("\n\n########## 测试 分割线 ##########")
        # 光标移到末尾
        editor, _ = find_editor(page)
        if editor:
            try:
                editor.click()
                time.sleep(0.2)
                page.keyboard.press("Control+End")  # 移到末尾
                time.sleep(0.3)
            except Exception:
                pass
        ok = click_format_button(page, ["分割线", "—", "分隔线", "hr", "divider"], "分割线")
        results["HR"] = ok
        time.sleep(0.5)
        html = read_editor_html(page)
        results["HR_applied"] = ("<hr" in html.lower())
        print(f"  HTML 含 <hr>: {results['HR_applied']}")

        # ============ 最终读 HTML ============
        print("\n\n=== 最终 HTML ===")
        final_html = read_editor_html(page)
        print(final_html[:1000])

        # 保存截图
        shot(page, "tc0012_final.png")

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        for k, v in results.items():
            status = "✅" if v else "❌"
            print(f"  {status} {k}: {v}")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []
        bug_hits = []

        if not results.get("H1_applied"):
            errors.append("H1 未生效")
        if not results.get("H2_applied"):
            errors.append("H2 未生效")
        if not results.get("H3_applied"):
            errors.append("H3 未生效")
        if not results.get("B_applied"):
            errors.append("加粗 B 未生效")
        if not results.get("I_applied"):
            errors.append("斜体 I 未生效")
        if not results.get("UL_applied"):
            errors.append("无序列表未生效")
        if not results.get("OL_applied"):
            errors.append("有序列表未生效")

        # 分割线：用例里已经记录"点击分割线没反应"，是已知缺陷
        if not results.get("HR_applied"):
            bug_hits.append("点击分割线按钮无反应（用例已记录）")

        # 输出
        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0012，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
        if bug_hits:
            print(f"\n【已知缺陷复现】：")
            for b in bug_hits:
                print(f"  - {b}")

        if errors:
            print("=" * 60)
            raise AssertionError("TC-0012 未通过")

        print("[PASS] TC-0012 通过（含已知缺陷记录）")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0012_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0012()