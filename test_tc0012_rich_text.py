"""
TC-0012 自动化测试：文本节点富文本格式编辑
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow，编辑器基于 Lexical）

流程：
    1. 双击画布 → 新建文本节点
    2. 双击节点进入编辑
    3. 输入三行文字：一个美丽的模特 / 高 / 瘦
    4. 选中文字 → 点击格式按钮（H1/H2/H3/B/I/无序列表/有序列表/分隔线）
    5. 读 HTML 验证

已知缺陷（用例记录）：
    - 颜色退出编辑不显示
    - 点击分隔线按钮无反应

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


# ============ 新建文本节点 ============
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


def input_lines(page, lines):
    print(f"\n=== 输入 {len(lines)} 行文字 ===")
    editor, sel = find_editor(page)
    if not editor:
        print("  [WARN] 没找到编辑区")
    else:
        print(f"  编辑区: {sel}")
        try:
            editor.click(timeout=3000)
            time.sleep(0.3)
        except Exception:
            pass

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
    editor, _ = find_editor(page)
    if not editor:
        return ""
    try:
        return editor.inner_html()
    except Exception:
        return ""


# ============ 选中文字 ============
def select_text_js(page, text):
    print(f"  用 JS 选中: '{text}'")
    editor, _ = find_editor(page)
    if not editor:
        print("    [WARN] 没有编辑区")
        return False

    result = editor.evaluate("""(el, text) => {
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            const idx = node.textContent.indexOf(text);
            if (idx >= 0) {
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
        return false;
    }""", text)
    print(f"    结果: {result}")
    time.sleep(0.4)
    return result


# ============ 定位工具栏按钮 ============
def find_toolbar_button(page, title_keyword):
    """
    在编辑区上方工具栏里，按 title 精确匹配按钮。
    """
    editor, _ = find_editor(page)
    editor_y = 0
    if editor:
        box = editor.bounding_box()
        if box:
            editor_y = box["y"]

    btns = page.locator("button")
    for i in range(btns.count()):
        el = btns.nth(i)
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box:
                continue
            # 工具栏在编辑区上方 300px 内
            if not (editor_y - 300 < box["y"] < editor_y + 30):
                continue
            title = (el.get_attribute("title") or "").strip()
            if title == title_keyword:
                return el, title
        except Exception:
            pass
    return None, None


def click_format_button(page, title_kw, name=""):
    print(f"  点击 {name}: title='{title_kw}'")
    btn, title = find_toolbar_button(page, title_kw)
    if btn:
        try:
            btn.click(timeout=3000)
            print(f"    [OK] 点击 title='{title}'")
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"    点击失败: {e}")
            return False
    print(f"    [FAIL] 找不到 title='{title_kw}' 的按钮")
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

        # 新建
        dblclick_canvas(page)
        click_menu_item(page, "文本节点")
        time.sleep(1.5)
        wait_for_new_node(page, before, timeout=15)

        # 进入编辑
        dblclick_node(page)

        # 输入
        input_lines(page, [LINE1, LINE2, LINE3])

        results = {}

        # ============ H1 ============
        print("\n\n########## H1 ##########")
        if select_text_js(page, LINE1):
            click_format_button(page, "标题 1", "H1")
            time.sleep(0.5)
            html = read_editor_html(page)
            print(f"  HTML: {html[:400]}")
            results["H1"] = (
                "<h1" in html.lower()
                or "font-size:2em" in html.lower()
                or "font-size: 2em" in html.lower()
                or "font-size:xxx-large" in html.lower()
            )
            print(f"  H1 生效: {results['H1']}")
            shot(page, "tc0012_after_H1.png")

        # ============ H2 ============
        print("\n\n########## H2 ##########")
        if select_text_js(page, LINE1):
            click_format_button(page, "标题 2", "H2")
            time.sleep(0.5)
            html = read_editor_html(page)
            results["H2"] = ("<h2" in html.lower() or "1.5em" in html.lower())
            print(f"  H2 生效: {results['H2']}")
            shot(page, "tc0012_after_H2.png")

        # ============ H3 ============
        print("\n\n########## H3 ##########")
        if select_text_js(page, LINE1):
            click_format_button(page, "标题 3", "H3")
            time.sleep(0.5)
            html = read_editor_html(page)
            results["H3"] = ("<h3" in html.lower() or "1.17em" in html.lower())
            print(f"  H3 生效: {results['H3']}")
            shot(page, "tc0012_after_H3.png")

        # ============ 加粗 B ============
        print("\n\n########## 加粗 B ##########")
        if select_text_js(page, LINE2):
            click_format_button(page, "加粗", "加粗")
            time.sleep(0.5)
            html = read_editor_html(page)
            print(f"  HTML: {html[:600]}")
            # 宽松匹配
            html_lower = html.lower()
            results["B"] = (
                "<strong" in html_lower
                or "<b>" in html_lower
                or "<b " in html_lower
                or "font-weight" in html_lower
                or "bold" in html_lower
            )
            print(f"  B 生效: {results['B']}")
            shot(page, "tc0012_after_B.png")

        # ============ 斜体 I ============
        print("\n\n########## 斜体 I ##########")
        if select_text_js(page, LINE3):
            click_format_button(page, "斜体", "斜体")
            time.sleep(0.5)
            html = read_editor_html(page)
            print(f"  HTML: {html[:600]}")
            html_lower = html.lower()
            results["I"] = (
                "<em>" in html_lower
                or "<i>" in html_lower
                or "<i " in html_lower
                or "font-style" in html_lower
                or "italic" in html_lower
            )
            print(f"  I 生效: {results['I']}")
            shot(page, "tc0012_after_I.png")

        # ============ 无序列表 ============
        print("\n\n########## 无序列表 ##########")
        if select_text_js(page, LINE2):
            click_format_button(page, "无序列表", "无序列表")
            time.sleep(0.5)
            html = read_editor_html(page)
            print(f"  HTML: {html[:600]}")
            results["UL"] = ("<ul" in html.lower() or "list-style" in html.lower())
            print(f"  UL 生效: {results['UL']}")
            shot(page, "tc0012_after_UL.png")

        # ============ 有序列表 ============
        print("\n\n########## 有序列表 ##########")
        if select_text_js(page, LINE3):
            click_format_button(page, "有序列表", "有序列表")
            time.sleep(0.5)
            html = read_editor_html(page)
            print(f"  HTML: {html[:600]}")
            results["OL"] = ("<ol" in html.lower())
            print(f"  OL 生效: {results['OL']}")
            shot(page, "tc0012_after_OL.png")

        # ============ 分隔线 ============
        print("\n\n########## 分隔线 ##########")
        editor, _ = find_editor(page)
        if editor:
            try:
                editor.click()
                time.sleep(0.2)
                page.keyboard.press("Control+End")
                time.sleep(0.3)
            except Exception:
                pass
        click_format_button(page, "分隔线", "分隔线")
        time.sleep(0.5)
        html = read_editor_html(page)
        print(f"  HTML: {html[:600]}")
        results["HR"] = ("<hr" in html.lower())
        print(f"  HR 生效: {results['HR']}")

        shot(page, "tc0012_final.png")

        print("\n\n=== 最终 HTML ===")
        print(html[:2000])

        print("\n\n=== 结果汇总 ===")
        for k, v in results.items():
            status = "✅" if v else "❌"
            print(f"  {status} {k}: {v}")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []
        bug_hits = []

        if not results.get("H1"):
            errors.append("H1 未生效")
        if not results.get("H2"):
            errors.append("H2 未生效")
        if not results.get("H3"):
            errors.append("H3 未生效")
        if not results.get("B"):
            errors.append("加粗 B 未生效")
        if not results.get("I"):
            errors.append("斜体 I 未生效")
        if not results.get("UL"):
            errors.append("无序列表未生效")
        if not results.get("OL"):
            errors.append("有序列表未生效")

        if not results.get("HR"):
            bug_hits.append("点击分隔线按钮无反应（用例已记录）")

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