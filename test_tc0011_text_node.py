"""
TC-0011 自动化测试：双击画布新建文本节点，双击节点编辑，检查工具栏
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布空白 → 弹出新建节点菜单
    2. 选择【文本节点】→ 新建文本节点
    3. 双击生成的节点 → 进入编辑状态
    4. 输入文字 "一个美丽的模特"
    5. 检查节点上方工具栏是否出现
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 9222
ROOT = Path(__file__).parent

TARGET_TEXT = "一个美丽的模特"

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


# ============ 步骤 1：双击画布 ============
def dblclick_canvas(page):
    print("\n=== 步骤 1：双击画布空白处 ===")
    page.mouse.dblclick(600, 400)
    time.sleep(1.5)
    shot(page, "tc0011_1_after_dblclick_canvas.png")


def wait_for_menu(page, timeout=5):
    print("\n=== 等待菜单弹出 ===")
    start = time.time()
    while time.time() - start < timeout:
        try:
            if page.locator(".cm-item").count() > 0:
                print("  [OK] 菜单出现")
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print("  [WARN] 菜单未出现")
    return False


# ============ 步骤 2：点「文本节点」 ============
def click_menu_item(page, text_keyword):
    print(f"\n=== 步骤 2：点击菜单项 '{text_keyword}' ===")
    try:
        loc = page.locator(".cm-item")
        for i in range(loc.count()):
            el = loc.nth(i)
            try:
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if text_keyword in t:
                    box = el.bounding_box()
                    if box and box["width"] < 300 and box["height"] < 60:
                        el.click(timeout=3000)
                        print(f"  [OK] 点击 [{i}] '{t[:30]}'")
                        return True
            except Exception:
                pass
    except Exception as e:
        print(f"  查找失败: {e}")
    raise RuntimeError(f"找不到菜单项 '{text_keyword}'")


def wait_for_new_node(page, before, timeout=15):
    print("\n=== 等待新节点 ===")
    start = time.time()
    while time.time() - start < timeout:
        cur = page.locator(".react-flow__node").count()
        if cur > before:
            print(f"  [OK] 节点数 {before} → {cur}")
            return cur
        time.sleep(1)
    raise RuntimeError("新节点未出现")


def get_last_node_box(page):
    node = page.locator(".react-flow__node").last
    box = node.bounding_box()
    if not box:
        raise RuntimeError("节点没有 bounding_box")
    return box


# ============ 步骤 3：双击节点进入编辑 ============
def dblclick_node(page):
    print("\n=== 步骤 3：双击节点进入编辑 ===")
    box = get_last_node_box(page)
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    print(f"  节点中心: ({cx:.0f},{cy:.0f})")

    page.mouse.dblclick(cx, cy)
    time.sleep(1.5)
    shot(page, "tc0011_2_after_dblclick_node.png")


# ============ 步骤 4：输入文字 ============
def input_text(page, text):
    print(f"\n=== 步骤 4：输入文字 '{text}' ===")

    edit_target = None
    for sel in [
        "[contenteditable='true']",
        "[class*='ProseMirror']",
        "[class*='editor']",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                try:
                    if el.is_visible():
                        edit_target = el
                        print(f"  编辑区: {sel} [{i}]")
                        break
                except Exception:
                    pass
            if edit_target:
                break
        except Exception:
            pass

    if edit_target:
        try:
            edit_target.click(timeout=3000)
            time.sleep(0.3)
        except Exception:
            pass
        page.keyboard.press("Control+A")
        time.sleep(0.2)
        page.keyboard.press("Delete")
        time.sleep(0.2)
    else:
        print("  [WARN] 没找到编辑区，直接键盘输入")

    for ch in text:
        page.keyboard.type(ch, delay=80)
    time.sleep(0.5)

    shot(page, "tc0011_3_after_input_text.png")


def read_node_text(page):
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    if n == 0:
        return ""
    try:
        return (nodes.nth(n - 1).inner_text() or "").strip()
    except Exception:
        return ""


# ============ 步骤 5：检查工具栏 ============
def check_node_toolbar(page):
    print("\n=== 步骤 5：检查节点上方工具栏 ===")

    box = get_last_node_box(page)
    print(f"  节点位置: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

    keywords = ["H1", "H2", "H3", "B", "I", "段落", "复制", "保存",
                "加粗", "斜体", "无序列表", "有序列表", "分割线"]

    print("\n  关键词命中：")
    hits = {}
    for kw in keywords:
        hits[kw] = 0
        try:
            loc = page.get_by_text(kw, exact=False)
            cnt = loc.count()
            visible = 0
            positions = []
            for i in range(cnt):
                el = loc.nth(i)
                try:
                    if el.is_visible():
                        b = el.bounding_box()
                        if b:
                            visible += 1
                            positions.append((b["x"], b["y"]))
                except Exception:
                    pass
            hits[kw] = visible
            status = "✅" if visible > 0 else "❌"
            print(f"    {status} '{kw}': {visible} 处")
            for px, py in positions[:3]:
                print(f"      位置: ({px:.0f},{py:.0f})")
        except Exception:
            pass

    print("\n  查找工具栏容器：")
    containers = []
    for sel in [
        "[role='toolbar']",
        "[class*='toolbar']",
        "[class*='Toolbar']",
        "[class*='tool-bar']",
        "[class*='editor-toolbar']",
        "[class*='rich-text']",
        "[class*='toolbox']",
    ]:
        try:
            loc = page.locator(sel)
            cnt = loc.count()
            for i in range(cnt):
                el = loc.nth(i)
                try:
                    if el.is_visible():
                        b = el.bounding_box()
                        if b:
                            t = (el.inner_text() or "").strip()[:80]
                            containers.append({"sel": sel, "idx": i, "box": b, "text": t})
                            print(f"    ✅ '{sel}' [{i}] pos=({b['x']:.0f},{b['y']:.0f}) size=({b['width']:.0f}x{b['height']:.0f})")
                            print(f"       text='{t}'")
                except Exception:
                    pass
        except Exception:
            pass

    print(f"\n  节点上方 300px 内的可见按钮：")
    try:
        btns = page.locator("button")
        cnt = btns.count()
        count_above = 0
        for i in range(cnt):
            el = btns.nth(i)
            try:
                if not el.is_visible():
                    continue
                b = el.bounding_box()
                if not b:
                    continue
                if box["y"] - 300 < b["y"] < box["y"]:
                    t = (el.inner_text() or "").strip()[:20]
                    title = el.get_attribute("title") or ""
                    aria = el.get_attribute("aria-label") or ""
                    label = t or title or aria
                    if label:
                        print(f"    [{i}] y={b['y']:.0f} '{label}'")
                        count_above += 1
            except Exception:
                pass
        print(f"  节点上方按钮数: {count_above}")
    except Exception:
        pass

    total_hits = sum(1 for v in hits.values() if v > 0)
    print(f"\n  命中关键词总数: {total_hits}")
    print(f"  工具栏容器数: {len(containers)}")
    return hits, total_hits, containers


# ============ 主流程 ============
def test_tc0011():
    print("=== TC-0011：双击画布新建文本节点 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪，请先启动帧境")

    pw = None
    browser = None
    try:
        pw, browser, page = connect()

        before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {before}")

        # 步骤 1
        dblclick_canvas(page)
        if not wait_for_menu(page):
            raise RuntimeError("双击画布后菜单未弹出")

        # 步骤 2
        click_menu_item(page, "文本节点")
        time.sleep(1.5)
        shot(page, "tc0011_2b_after_add_text_node.png")
        wait_for_new_node(page, before, timeout=15)

        # 步骤 3
        dblclick_node(page)

        # 步骤 4
        input_text(page, TARGET_TEXT)

        final_text = read_node_text(page)
        print(f"\n  节点最终文字: '{final_text}'")
        print(f"  期望文字:     '{TARGET_TEXT}'")

        # 步骤 5
        hits, total_hits, containers = check_node_toolbar(page)

        # 断言
        print("\n\n=== 断言 ===")
        errors = []

        if TARGET_TEXT not in final_text:
            errors.append(f"节点文字不匹配: 期望含 '{TARGET_TEXT}', 实际 '{final_text}'")

        if total_hits < 2 and len(containers) == 0:
            errors.append(f"工具栏未出现（关键词命中 {total_hits} 个，容器 {len(containers)} 个）")

        if errors:
            print(f"[FAIL] TC-0011，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            raise AssertionError("TC-0011 未通过")

        print("[PASS] TC-0011 通过")
        print(f"  ✅ 文本节点新建成功")
        print(f"  ✅ 文字输入成功: '{TARGET_TEXT}'")
        print(f"  ✅ 工具栏出现（关键词 {total_hits} 个，容器 {len(containers)} 个）")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            if browser:
                pages = browser.contexts[0].pages
                if pages:
                    pages[0].screenshot(path=str(SHOT_DIR / "tc0011_error.png"))
                    print("[SHOT] tc0011_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            if browser:
                browser.close()
            if pw:
                pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    test_tc0011()