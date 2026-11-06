"""
TC-0017 自动化测试：图片节点调色功能（光线/颜色/细节/效果 + 自动调色）
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布新建图片节点，上传 牛群.jpg
    2. 选中节点，点【调色】→ 打开调色面板
    3. 拖动画布（往上拖），让调色面板完整显示
    4. 在【光线】标签调滑块（每个 +20）
    5. 切到【颜色】标签调滑块
    6. 切到【细节】标签调滑块
    7. 切到【效果】标签调滑块
    8. 点【重置】按钮（一键恢复所有滑块到默认 0）
    9. 点【自动调色】按钮
    10. 点【应用】关闭面板

关键 UI（从截图确认）：
    - 调色面板：右上角有「自动调色」图标按钮 + × 关闭
    - 右下角有「重置」+「应用」两个按钮
    - 标签页：光线 | 颜色 | 细节 | 效果
    - 每个滑块默认值 0

滑块调整量：
    - ADJUST_STEPS = 20

运行前置：
    pip install playwright requests pywinauto pyperclip
    python -m playwright install chromium
    帧境 AI 已带 --remote-debugging-port=9222 启动
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

try:
    from pywinauto import Application
    from pywinauto.keyboard import send_keys
    PYWINAUTO_OK = True
except ImportError:
    PYWINAUTO_OK = False
    print("[WARN] pywinauto 未安装")

try:
    import pyperclip
    PYPERCLIP_OK = True
except ImportError:
    PYPERCLIP_OK = False
    print("[WARN] pyperclip 未安装")

PORT = 9222
ROOT = Path(__file__).parent

_ABS_IMG1 = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\牛群.jpg")
_REL_IMG1 = ROOT / "testdata" / "牛群.jpg"
IMG1_PATH = _ABS_IMG1 if _ABS_IMG1.exists() else _REL_IMG1

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

LIGHT_SLIDERS = ["光线", "曝光", "对比", "高光", "阴影", "白色", "黑色"]
COLOR_SLIDERS = ["自然饱和", "饱和度", "色温", "色调"]
DETAIL_SLIDERS = ["锐化", "清晰度", "颗粒"]
EFFECT_SLIDERS = ["晕影", "柔光", "辉光"]

ADJUST_STEPS = 20


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


def dblclick_canvas(page, x, y):
    print(f"\n=== 双击画布 ({x},{y}) ===")
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, f"tc0017_dblclick_{x}_{y}.png")


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


def get_new_node_id(page, before_count):
    wait_for_new_node(page, before_count, timeout=15)
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    new_node = nodes.nth(n - 1)
    try:
        node_id = new_node.get_attribute("data-id")
    except Exception:
        node_id = None
    print(f"  新节点 data-id: {node_id}")
    return node_id


def get_node_by_id(page, node_id):
    if not node_id:
        raise RuntimeError("node_id 为空")
    return page.locator(f'.react-flow__node[data-id="{node_id}"]').first


def handle_system_dialog(file_dir, file_name):
    print("\n  [pywinauto] 连接文件对话框")

    dlg = None
    for title in ["打开", "Open"]:
        try:
            app = Application(backend="win32").connect(title=title, timeout=5)
            dlg = app.window(title=title)
            print(f"  [OK] 连接成功，title='{title}'")
            break
        except Exception:
            continue

    if not dlg:
        try:
            app = Application(backend="win32").connect(title_re=".*(打开|Open|选择).*", timeout=5)
            dlg = app.window(title_re=".*(打开|Open|选择).*")
            print("  [OK] 正则匹配成功")
        except Exception as e:
            print(f"  [FAIL] 无法连接对话框: {e}")
            return False

    try:
        dlg.set_focus()
        time.sleep(0.5)
    except Exception:
        pass

    try:
        send_keys("%d")
        time.sleep(0.5)
        send_keys("^a")
        time.sleep(0.2)
        send_keys("{DELETE}")
        time.sleep(0.2)
        if PYPERCLIP_OK:
            pyperclip.copy(str(file_dir))
            time.sleep(0.3)
            send_keys("^v")
            time.sleep(0.5)
        else:
            send_keys(str(file_dir), with_spaces=True, pause=0.02)
            time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(2)
    except Exception as e:
        print(f"  步骤1失败: {e}")

    try:
        send_keys("%n")
        time.sleep(0.5)
        send_keys("^a")
        time.sleep(0.2)
        send_keys("{DELETE}")
        time.sleep(0.2)
        if PYPERCLIP_OK:
            pyperclip.copy(str(file_name))
            time.sleep(0.3)
            send_keys("^v")
            time.sleep(0.5)
        else:
            send_keys(str(file_name), with_spaces=True, pause=0.02)
            time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(3)
    except Exception as e:
        print(f"  步骤2失败: {e}")

    return True


def create_image_node_with_upload(page, image_path, dblclick_x, dblclick_y, tag=""):
    print(f"\n\n########## 新建图片节点并上传：{image_path.name} {tag} ##########")

    before = page.locator(".react-flow__node").count()

    dblclick_canvas(page, dblclick_x, dblclick_y)
    click_menu_item(page, "图片节点")
    time.sleep(1.5)
    node_id = get_new_node_id(page, before)
    shot(page, f"tc0017_after_add_node_{tag}.png")

    node = get_node_by_id(page, node_id)
    upload_btn = node.get_by_role("button", name="上传", exact=True).first
    if upload_btn.count() == 0:
        btns = node.locator("button")
        for i in range(btns.count()):
            b = btns.nth(i)
            if b.is_visible() and (b.inner_text() or "").strip() == "上传":
                upload_btn = b
                break

    if upload_btn.count() == 0:
        print(f"  [FAIL] 找不到「上传」按钮")
        return node_id

    try:
        upload_btn.click(timeout=3000)
        print("  [OK] 点击「上传」按钮")
    except Exception as e:
        print(f"  点击失败: {e}")
        try:
            upload_btn.click(timeout=3000, force=True)
        except Exception as e2:
            print(f"  force 也失败: {e2}")
            return node_id

    time.sleep(3)
    shot(page, f"tc0017_after_click_upload_{tag}.png")

    handle_system_dialog(image_path.parent, image_path.name)
    time.sleep(3)
    shot(page, f"tc0017_after_upload_{tag}.png")

    return node_id


def click_node_locator(page, node_locator):
    try:
        box = node_locator.bounding_box()
        if not box:
            return False
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        print(f"  点击节点中心 ({cx:.0f},{cy:.0f})")
        page.mouse.click(cx, cy)
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False


def pan_canvas_up(page, dx=0, dy=-300):
    print(f"\n=== 拖动画布（往上 {abs(dy)}px）===")

    start_points = [
        (400, 200), (350, 250), (300, 200), (500, 200),
        (250, 300), (400, 250),
    ]

    start_x, start_y = None, None
    for (x, y) in start_points:
        r = page.evaluate(f"""() => {{
            const el = document.elementFromPoint({x}, {y});
            if (!el) return 'none';
            return String(el.className || '').slice(0, 100);
        }}""")
        if "react-flow" in r or "pane" in r or "background" in r:
            start_x, start_y = x, y
            print(f"  起点 ({x},{y}) class='{r}'")
            break

    if start_x is None:
        print("  [WARN] 没找到画布空白起点，用 (400, 200)")
        start_x, start_y = 400, 200

    end_x, end_y = start_x + dx, start_y + dy
    print(f"  拖拽 ({start_x},{start_y}) → ({end_x},{end_y})")

    page.mouse.move(start_x, start_y)
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.3)
    steps = 25
    for i in range(1, steps + 1):
        x = start_x + (end_x - start_x) * i / steps
        y = start_y + (end_y - start_y) * i / steps
        page.mouse.move(x, y)
        time.sleep(0.02)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1.5)
    shot(page, "tc0017_after_pan.png")


def click_color_button(page):
    print("\n\n########## 点击「调色」按钮 ##########")

    try:
        loc = page.locator("button:has-text('调色')")
        for i in range(loc.count()):
            el = loc.nth(i)
            if not el.is_visible():
                continue
            t = (el.inner_text() or "").strip()
            if t == "调色":
                box = el.bounding_box()
                if box:
                    print(f"  找到「调色」按钮 [{i}] ({box['x']:.0f},{box['y']:.0f})")
                    el.click(timeout=3000)
                    print("  [OK] 点击「调色」")
                    time.sleep(2.5)
                    shot(page, "tc0017_after_click_color.png")
                    return True
    except Exception:
        pass

    try:
        el = page.get_by_text("调色", exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  get_by_text 点击「调色」")
            time.sleep(2.5)
            shot(page, "tc0017_after_click_color.png")
            return True
    except Exception:
        pass

    print("  [FAIL] 找不到「调色」按钮")
    return False


def find_color_panel(page):
    print("\n  查找调色面板")
    for sel in [
        "[role='dialog']",
        "[class*='modal-panel']",
        "[class*='drawer']",
        "[class*='panel']",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if "调色" in t and ("光线" in t or "颜色" in t) and ("细节" in t or "效果" in t):
                    box = el.bounding_box()
                    if box:
                        print(f"  找到调色面板: {sel} [{i}] size=({box['width']:.0f}x{box['height']:.0f})")
                        return el
        except Exception:
            pass

    print("  [WARN] 没找到调色面板")
    return None


def switch_tab(page, tab_name, panel=None):
    print(f"\n  切换到标签：{tab_name}")
    search_root = panel if panel else page

    for sel in [
        f"button:text-is('{tab_name}')",
        f"[role='tab']:has-text('{tab_name}')",
    ]:
        try:
            loc = search_root.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                el.click(timeout=3000)
                print(f"  [OK] 点击「{tab_name}」（{sel}）")
                time.sleep(1.5)
                shot(page, f"tc0017_tab_{tab_name}.png")
                return True
        except Exception:
            pass

    try:
        el = search_root.get_by_text(tab_name, exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print(f"  [OK] get_by_text 点击「{tab_name}」")
            time.sleep(1.5)
            shot(page, f"tc0017_tab_{tab_name}.png")
            return True
    except Exception:
        pass

    print(f"  [FAIL] 找不到标签「{tab_name}」")
    return False


def find_slider_by_label(page, panel, label):
    search_root = panel if panel else page
    try:
        label_loc = search_root.get_by_text(label, exact=True)
        cnt = label_loc.count()
        for i in range(cnt):
            el = label_loc.nth(i)
            if not el.is_visible():
                continue
            for level in range(1, 6):
                try:
                    parent = el.locator("xpath=" + "/".join([".."] * level))
                    if parent.count() == 0:
                        continue
                    slider = parent.first.locator("input[type='range']")
                    if slider.count() > 0:
                        return slider.first
                except Exception:
                    continue
    except Exception:
        pass
    return None


def adjust_slider_keyboard(page, slider_loc, direction="right", times=ADJUST_STEPS):
    try:
        slider_loc.scroll_into_view_if_needed()
        time.sleep(0.2)
        slider_loc.click()
        time.sleep(0.3)

        key = "ArrowRight" if direction == "right" else "ArrowLeft"
        for _ in range(times):
            page.keyboard.press(key)
            time.sleep(0.02)
        time.sleep(0.3)

        new_val = slider_loc.input_value()
        print(f"      → value={new_val}")
        return True
    except Exception as e:
        print(f"      调整失败: {e}")
        return False


def process_tab(page, panel, tab_name, slider_labels):
    print(f"\n\n########## 处理标签：{tab_name} ##########")

    tab_ok = switch_tab(page, tab_name, panel)
    if not tab_ok:
        return {"results": {}, "sliders": []}, False

    time.sleep(1)
    results = {}
    sliders_found = []

    for label in slider_labels:
        slider = find_slider_by_label(page, panel, label)
        if slider:
            print(f"  找到滑块「{label}」")
            adjust_slider_keyboard(page, slider, direction="right", times=ADJUST_STEPS)
            results[label] = True
            sliders_found.append((label, slider))
        else:
            print(f"  [WARN] 找不到滑块「{label}」")
            results[label] = False

    shot(page, f"tc0017_{tab_name}_adjusted.png")
    return {"results": results, "sliders": sliders_found}, True


# ============ 【修正】点「重置」按钮（一键复位） ============
def click_reset_button(page, panel):
    """
    点击调色面板右下角的「重置」按钮。
    一键把所有滑块恢复到默认值 0。
    """
    print("\n\n########## 点击「重置」按钮 ##########")

    if not panel:
        panel = page

    # 优先在面板内找精确匹配"重置"的按钮
    for sel in [
        "button:text-is('重置')",
        "button:has-text('重置')",
    ]:
        try:
            loc = panel.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box:
                    print(f"  找到「重置」按钮 [{i}] ({box['x']:.0f},{box['y']:.0f})")
                    el.click(timeout=3000)
                    print("  [OK] 点击「重置」")
                    time.sleep(2)
                    shot(page, "tc0017_after_reset.png")
                    return True
        except Exception:
            pass

    # 兜底：全局找"重置"
    try:
        el = page.get_by_text("重置", exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  get_by_text 点击「重置」")
            time.sleep(2)
            shot(page, "tc0017_after_reset.png")
            return True
    except Exception:
        pass

    print("  [FAIL] 找不到「重置」按钮")
    return False


def click_auto_color_button(page, panel):
    print("\n\n########## 点击「自动调色」按钮 ##########")

    if not panel:
        print("  [WARN] 没有面板，尝试全局找")
        panel = page

    for sel in [
        "[aria-label*='自动调色']",
        "[title*='自动调色']",
        "[aria-label*='自动']",
        "[title*='自动']",
        "[aria-label*='一键']",
        "[title*='一键']",
    ]:
        try:
            loc = panel.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box:
                    print(f"  找到按钮: {sel} [{i}] ({box['x']:.0f},{box['y']:.0f})")
                    el.click(timeout=3000)
                    print(f"  [OK] 点击「自动调色」")
                    time.sleep(3)
                    shot(page, "tc0017_after_auto_color.png")
                    return True
        except Exception:
            pass

    try:
        close_btn = panel.locator("button:has-text('×'), button:has-text('✕')").first
        if close_btn.count() == 0:
            close_btn = panel.locator("button[aria-label='关闭']").first

        if close_btn.count() > 0 and close_btn.is_visible():
            close_box = close_btn.bounding_box()
            if close_box:
                all_btns = panel.locator("button")
                for i in range(all_btns.count()):
                    b = all_btns.nth(i)
                    if not b.is_visible():
                        continue
                    b_box = b.bounding_box()
                    if not b_box:
                        continue
                    if (abs(b_box["y"] - close_box["y"]) < 20 and
                        0 < close_box["x"] - b_box["x"] < 80):
                        print(f"  找到 × 左边的按钮 ({b_box['x']:.0f},{b_box['y']:.0f})")
                        b.click(timeout=3000)
                        print(f"  [OK] 点击「自动调色」")
                        time.sleep(3)
                        shot(page, "tc0017_after_auto_color.png")
                        return True
    except Exception as e:
        print(f"  策略2失败: {e}")

    try:
        all_btns = panel.locator("button")
        for i in range(all_btns.count()):
            b = all_btns.nth(i)
            if not b.is_visible():
                continue
            t = (b.inner_text() or "").strip()
            title = b.get_attribute("title") or ""
            aria = b.get_attribute("aria-label") or ""
            if not t and not title and not aria:
                box = b.bounding_box()
                if box and box["x"] > 800:
                    print(f"  找到候选图标按钮 [{i}] ({box['x']:.0f},{box['y']:.0f})")
                    b.click(timeout=3000)
                    print(f"  [OK] 点击「自动调色」")
                    time.sleep(3)
                    shot(page, "tc0017_after_auto_color.png")
                    return True
    except Exception:
        pass

    print("  [FAIL] 找不到「自动调色」按钮")
    return False


def close_color_panel(page, panel):
    print("\n\n########## 关闭调色面板 ##########")

    # 优先点"应用"（用户描述里点应用后关闭）
    for kw in ["应用", "完成", "确定"]:
        try:
            search_root = panel if panel else page
            loc = search_root.get_by_text(kw, exact=True)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box and box["width"] < 150:
                    el.click(timeout=3000)
                    print(f"  [OK] 点击「{kw}」")
                    time.sleep(2)
                    shot(page, "tc0017_after_close.png")
                    return True
        except Exception:
            pass

    # 兜底：× 按钮
    if panel:
        for sel in ["button[aria-label='关闭']", "button:has-text('×')", "button:has-text('✕')"]:
            try:
                btn = panel.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=3000)
                    print(f"  [OK] 点击关闭按钮（{sel}）")
                    time.sleep(2)
                    shot(page, "tc0017_after_close.png")
                    return True
            except Exception:
                pass

    # 兜底：Escape
    try:
        page.keyboard.press("Escape")
        time.sleep(2)
        print("  [OK] 按 Escape")
        shot(page, "tc0017_after_close.png")
        return True
    except Exception:
        pass

    print("  [FAIL] 找不到关闭方式")
    return False


def test_tc0017():
    print("=== TC-0017：图片节点调色功能 ===")
    print(f"[INFO] 滑块调整量 ADJUST_STEPS = {ADJUST_STEPS}")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        print(f"[INFO] 初始节点数: {page.locator('.react-flow__node').count()}")

        # 1. 上传节点
        node_id = create_image_node_with_upload(page, IMG1_PATH, 600, 400, tag="niunqun")
        print(f"  节点 data-id: {node_id}")

        # 2. 选中节点
        node = get_node_by_id(page, node_id)
        click_node_locator(page, node)
        time.sleep(1)
        shot(page, "tc0017_selected_node.png")

        # 3. 点调色
        color_ok = click_color_button(page)
        if not color_ok:
            raise RuntimeError("无法打开调色面板")

        # 4. 拖动画布
        pan_canvas_up(page, dx=0, dy=-300)
        time.sleep(1)

        panel = find_color_panel(page)
        shot(page, "tc0017_panel_visible.png")

        # 5. 处理 4 个标签
        results_all = {}

        r1, ok1 = process_tab(page, panel, "光线", LIGHT_SLIDERS)
        results_all["光线"] = {"tab_ok": ok1, "sliders": r1}

        r2, ok2 = process_tab(page, panel, "颜色", COLOR_SLIDERS)
        results_all["颜色"] = {"tab_ok": ok2, "sliders": r2}

        r3, ok3 = process_tab(page, panel, "细节", DETAIL_SLIDERS)
        results_all["细节"] = {"tab_ok": ok3, "sliders": r3}

        r4, ok4 = process_tab(page, panel, "效果", EFFECT_SLIDERS)
        results_all["效果"] = {"tab_ok": ok4, "sliders": r4}

        # 6. 【修正】点「重置」按钮（一键复位）
        reset_ok = click_reset_button(page, panel)

        # 7. 点自动调色
        auto_color_ok = click_auto_color_button(page, panel)

        # 8. 点「应用」关闭面板
        close_ok = close_color_panel(page, panel)

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  node_id: {node_id}")
        print(f"  {'✅' if color_ok else '❌'} 打开调色面板")
        print(f"  {'✅' if reset_ok else '❌'} 点击「重置」按钮")
        print(f"  {'✅' if auto_color_ok else '❌'} 点击「自动调色」")
        print(f"  {'✅' if close_ok else '❌'} 关闭调色面板")

        for tab_name, data in results_all.items():
            tab_ok = data.get("tab_ok", False)
            sliders = data.get("sliders", {}).get("results", {})
            found = sum(1 for v in sliders.values() if v)
            total = len(sliders)
            print(f"  {'✅' if tab_ok else '❌'} 标签「{tab_name}」：滑块 {found}/{total} 找到")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        if not color_ok:
            errors.append("打开调色面板失败")
        if not reset_ok:
            errors.append("点击「重置」按钮失败")
        if not auto_color_ok:
            errors.append("点击「自动调色」失败")
        if not close_ok:
            errors.append("关闭调色面板失败")

        for tab_name, data in results_all.items():
            if not data.get("tab_ok"):
                errors.append(f"切换到「{tab_name}」标签失败")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0017，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0017 未通过")

        print("[PASS] TC-0017 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0017_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0017()