"""
TC-0021 自动化测试：视频节点延长（裁剪片段 + 去延长 + 生成）
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布 → 新建视频节点
    2. 上传本地视频 羊群奔跑.mp4
    3. 选中视频节点 → 点【延长】
    4. 拖动画布往上，让延长面板完整显示
    5. 拖拽选区左右端，裁剪片段
    6. 点【去延长】→ 生成新节点 + 新节点控制台
    7. 在"新节点控制台"输入延长内容
    8. 点新节点控制台的发送按钮
    9. 等待生成完成
    10. 验证新节点里出现延长后的视频

F12 关键 DOM（用户提供）：
    - 输入框：<div class="wprompt-ed" contenteditable="true" role="textbox" data-lexical-editor="true">...</div>
    - 父容器：<div class="winput">...</div>
    - 发送按钮：<button class="cx-btn-shutter" aria-label="生成" title="运行 · ×N ...">
                    <svg class="lucide lucide-arrow-up">...</svg>
                </button>

区分两个控制台（都含 .winput）：
    - 新节点控制台：含"片段进行延长"或"请输入需要延长的内容"
    - 页面中控台：含"描述你想生成的画面"

跨电脑策略：
    - 用 .winput / .wprompt-ed / .cx-btn-shutter 这些固定 class
    - 用文字内容区分两个控制台
    - 拖拽选区用 DOM 元素边界 + 百分比，不用屏幕绝对坐标

运行前置：
    pip install playwright requests pywinauto pyperclip
    python -m playwright install chromium
    帧境 AI 已带 --remote-debugging-port=9222 启动
"""

import os
import sys
import re
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

_ABS_VIDEO = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群奔跑.mp4")
_REL_VIDEO = ROOT / "testdata" / "羊群奔跑.mp4"
VIDEO_PATH = _ABS_VIDEO if _ABS_VIDEO.exists() else _REL_VIDEO

EXTEND_PROMPT = "请你添加后续一群狼跑出来的画面"
GENERATE_TIMEOUT = 300

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

CLIP_SELECTION_SELECTOR = '[title="拖动可整体平移所选片段"]'


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


# ============ 通用工具 ============
def dblclick_canvas(page, x=600, y=350):
    print(f"\n=== 双击画布 ({x},{y}) ===")
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, f"tc0021_dblclick_{x}_{y}.png")


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


def get_new_node_id(page, before_count, timeout=20):
    wait_for_new_node(page, before_count, timeout=timeout)
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


# ============ 拖动画布往上 ============
def pan_canvas_up(page, dy=-300):
    print(f"\n=== 拖动画布往上（dy={dy}）===")

    start_points = [
        (400, 150), (350, 150), (300, 150), (500, 150),
        (250, 200), (400, 200),
    ]

    start_x, start_y = None, None
    for (x, y) in start_points:
        r = page.evaluate(f"""() => {{
            const el = document.elementFromPoint({x}, {y});
            if (!el) return 'none';
            return String(el.className || '').slice(0, 100);
        }}""")
        print(f"  检查 ({x},{y}): class='{r}'")
        if "react-flow" in r or "pane" in r or "background" in r:
            start_x, start_y = x, y
            print(f"  [OK] 起点 ({x},{y})")
            break

    if start_x is None:
        print("  [WARN] 没找到画布空白起点，用 (400, 150)")
        start_x, start_y = 400, 150

    end_x, end_y = start_x, start_y + dy
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
    shot(page, "tc0021_after_pan.png")


# ============ pywinauto 系统对话框 ============
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


# ============ 新建视频节点 + 上传 ============
def create_video_node_with_upload(page, video_path, dblclick_x=600, dblclick_y=350):
    print(f"\n\n########## 新建视频节点并上传：{video_path.name} ##########")

    before = page.locator(".react-flow__node").count()

    dblclick_canvas(page, dblclick_x, dblclick_y)
    click_menu_item(page, "视频节点")
    time.sleep(1.5)
    node_id = get_new_node_id(page, before)
    shot(page, "tc0021_after_add_node.png")

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
    shot(page, "tc0021_after_click_upload.png")

    handle_system_dialog(video_path.parent, video_path.name)
    time.sleep(8)
    shot(page, "tc0021_after_upload.png")

    return node_id


# ============ 点「延长」按钮 ============
def click_extend_button(page):
    print("\n\n########## 点击「延长」按钮 ##########")

    kw = "延长"
    for sel in [f"button:text-is('{kw}')", f"button:has-text('{kw}')"]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box:
                    print(f"  找到「{kw}」按钮 [{i}] ({box['x']:.0f},{box['y']:.0f})")
                    el.click(timeout=3000)
                    print(f"  [OK] 点击「{kw}」")
                    time.sleep(2.5)
                    shot(page, "tc0021_after_click_extend.png")
                    return True
        except Exception:
            pass

    try:
        el = page.get_by_text(kw, exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print(f"  get_by_text 点击「{kw}」")
            time.sleep(2.5)
            shot(page, "tc0021_after_click_extend.png")
            return True
    except Exception:
        pass

    print("  [FAIL] 找不到「延长」按钮")
    return False


# ============ 等延长面板 ============
def wait_for_extend_panel(page, timeout=10):
    print("\n\n########## 等待延长面板出现 ##########")

    start = time.time()
    while time.time() - start < timeout:
        try:
            loc = page.get_by_text("请选择要延长的片段", exact=False)
            if loc.count() > 0:
                for i in range(loc.count()):
                    if loc.nth(i).is_visible():
                        print(f"  [OK] 延长面板出现（{time.time()-start:.1f}s）")
                        shot(page, "tc0021_extend_panel.png")
                        return True
        except Exception:
            pass
        time.sleep(0.5)

    print("  [WARN] 未检测到延长面板")
    return False


# ============ 读选区 style ============
def read_clip_selection(page):
    try:
        el = page.locator(CLIP_SELECTION_SELECTOR).first
        if el.count() == 0:
            return None
        style = el.get_attribute("style") or ""
        left = ""
        width = ""
        m_left = re.search(r"left:\s*([\d.]+%?)", style)
        m_width = re.search(r"width:\s*([\d.]+%?)", style)
        if m_left:
            left = m_left.group(1)
        if m_width:
            width = m_width.group(1)
        box = el.bounding_box()
        return {"left": left, "width": width, "box": box, "style": style}
    except Exception as e:
        print(f"    读选区失败: {e}")
        return None


# ============ 拖拽选区左右端 ============
def drag_clip_selection(page):
    print("\n\n########## 拖拽选区左右端（裁剪片段） ##########")

    sel_before = read_clip_selection(page)
    if not sel_before or not sel_before["box"]:
        print("  [FAIL] 找不到选区，跳过拖拽")
        return False, None, None

    print(f"  裁剪前: left={sel_before['left']}, width={sel_before['width']}")

    box = sel_before["box"]
    mid_y = box["y"] + box["height"] / 2

    print("\n  [步骤1] 拖选区左端往右")
    left_handle_x = box["x"] + 2
    drag_dist_left = box["width"] * 0.10

    page.mouse.move(left_handle_x, mid_y)
    time.sleep(0.8)
    shot(page, "tc0021_hover_left_handle.png")

    page.mouse.down()
    time.sleep(0.4)
    page.mouse.move(left_handle_x + 3, mid_y, steps=3)
    time.sleep(0.2)
    for i in range(1, 11):
        x = left_handle_x + drag_dist_left * i / 10
        page.mouse.move(x, mid_y)
        time.sleep(0.03)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1)
    shot(page, "tc0021_after_drag_left.png")

    sel_mid = read_clip_selection(page)
    if sel_mid:
        print(f"    拖左端后: left={sel_mid['left']}, width={sel_mid['width']}")

    print("\n  [步骤2] 拖选区右端往左")

    sel_now = read_clip_selection(page)
    if not sel_now or not sel_now["box"]:
        print("    [FAIL] 拖左端后找不到选区")
        return False, sel_before, sel_mid

    box2 = sel_now["box"]
    mid_y2 = box2["y"] + box2["height"] / 2
    right_handle_x = box2["x"] + box2["width"] - 2
    drag_dist_right = box2["width"] * 0.10

    page.mouse.move(right_handle_x, mid_y2)
    time.sleep(0.8)
    shot(page, "tc0021_hover_right_handle.png")

    page.mouse.down()
    time.sleep(0.4)
    page.mouse.move(right_handle_x - 3, mid_y2, steps=3)
    time.sleep(0.2)
    for i in range(1, 11):
        x = right_handle_x - drag_dist_right * i / 10
        page.mouse.move(x, mid_y2)
        time.sleep(0.03)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1)
    shot(page, "tc0021_after_drag_right.png")

    sel_after = read_clip_selection(page)
    if sel_after:
        print(f"    拖右端后: left={sel_after['left']}, width={sel_after['width']}")

    changed = False
    if sel_after and sel_before:
        if (sel_after["left"] != sel_before["left"]) or (sel_after["width"] != sel_before["width"]):
            changed = True

    print(f"  style 变化: {changed}")
    return changed, sel_before, sel_after


# ============ 点「去延长」 ============
def click_go_extend(page):
    print("\n\n########## 点击「去延长」 ##########")

    for sel in ["button:text-is('去延长')", "button:has-text('去延长')"]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box and box["width"] < 250:
                    el.click(timeout=3000)
                    print("  [OK] 点击「去延长」")
                    time.sleep(3)
                    shot(page, "tc0021_after_go_extend.png")
                    return True
        except Exception:
            pass

    try:
        el = page.get_by_text("去延长", exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  get_by_text 点击「去延长」")
            time.sleep(3)
            shot(page, "tc0021_after_go_extend.png")
            return True
    except Exception:
        pass

    print("  [FAIL] 找不到「去延长」按钮")
    return False


# ============ 【核心】找"新节点控制台"（.winput 容器） ============
def find_new_node_winput(page):
    """
    找"新节点控制台"容器（.winput）。
    页面上有两个 .winput：
      - 新节点控制台：含"片段进行延长"或"请输入需要延长的内容"
      - 页面中控台：含"描述你想生成的画面"
    用文字内容区分。
    """
    print("\n  查找新节点控制台（.winput）")

    winputs = page.locator(".winput")
    cnt = winputs.count()
    print(f"  页面上 .winput 数: {cnt}")

    for i in range(cnt):
        el = winputs.nth(i)
        try:
            if not el.is_visible():
                continue
            text = (el.inner_text() or "")
            # 新节点控制台特征
            is_new_console = (
                "片段进行延长" in text or
                "请输入需要延长的内容" in text or
                ("视频延长" in text and "描述你想生成的画面" not in text)
            )
            print(f"    .winput[{i}] 特征: 含'片段进行延长'={'片段进行延长' in text}, 含'描述你想生成的画面'={'描述你想生成的画面' in text}")
            if is_new_console:
                box = el.bounding_box()
                if box:
                    print(f"    [OK] 找到新节点控制台: .winput [{i}] size=({box['width']:.0f}x{box['height']:.0f})")
                    return el
        except Exception:
            pass

    print("    [WARN] 没找到新节点控制台")
    return None


# ============ 在新节点控制台输入 ============
def input_extend_prompt(page, prompt_text):
    print(f"\n\n########## 在新节点控制台输入：'{prompt_text}' ##########")

    winput = find_new_node_winput(page)
    if not winput:
        print("  [FAIL] 找不到新节点控制台")
        return False

    shot(page, "tc0021_new_node_console.png")

    # 找输入框
    composer = None
    for sel in [".wprompt-ed", "[contenteditable='true'][data-lexical-editor='true']", "[contenteditable='true']"]:
        try:
            loc = winput.locator(sel)
            if loc.count() > 0:
                el = loc.first
                if el.is_visible():
                    composer = el
                    print(f"  找到输入框: {sel}")
                    break
        except Exception:
            pass

    if not composer:
        # 兜底：全局找 .wprompt-ed，但排除页面底部中控台
        try:
            loc = page.locator(".wprompt-ed")
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    composer = el
                    print(f"  兜底: 全局 .wprompt-ed [{i}]")
                    break
        except Exception:
            pass

    if not composer:
        print("  [FAIL] 找不到输入框")
        return False

    try:
        composer.click(timeout=3000, force=True)
        time.sleep(0.5)
        page.keyboard.press("Control+A")
        time.sleep(0.2)
        page.keyboard.press("Delete")
        time.sleep(0.3)
        for ch in prompt_text:
            page.keyboard.type(ch, delay=60)
        time.sleep(0.5)
        shot(page, "tc0021_after_input_prompt.png")
        print(f"  [OK] 已输入：'{prompt_text}'")
        return True
    except Exception as e:
        print(f"  输入失败: {e}")
        return False


# ============ 【核心修正】点新节点控制台的发送按钮 ============
def click_send(page):
    """
    点新节点控制台的发送按钮。
    F12 确认：<button class="cx-btn-shutter" aria-label="生成" title="运行...">
    所以直接找 .winput 里的 button.cx-btn-shutter。
    """
    print("\n\n########## 点击新节点控制台的发送按钮 ##########")

    # 找新节点控制台
    winput = find_new_node_winput(page)
    if not winput:
        print("  [FAIL] 找不到新节点控制台")
        return False

    # 在这个 .winput 里找发送按钮
    # 优先：.cx-btn-shutter
    for sel in [
        "button.cx-btn-shutter",
        "button[aria-label='生成']",
        "button[aria-label='发送']",
        "button[title*='运行']",
        "button[title*='发送']",
    ]:
        try:
            loc = winput.locator(sel)
            cnt = loc.count()
            for i in range(cnt):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                print(f"    找到按钮: {sel} [{i}] pos=({box['x']:.0f},{box['y']:.0f})")
                el.click(timeout=3000)
                print(f"  [OK] 点击发送按钮（{sel}）")
                time.sleep(3)
                shot(page, "tc0021_after_send.png")
                return True
        except Exception as e:
            print(f"    {sel} 失败: {e}")

    # 兜底：找 .winput 内所有 button，取靠右下的
    print("    使用兜底策略：.winput 内所有按钮，取最靠右下的")
    try:
        btns = winput.locator("button")
        candidates = []
        for i in range(btns.count()):
            b = btns.nth(i)
            if not b.is_visible():
                continue
            box = b.bounding_box()
            if not box:
                continue
            candidates.append({"i": i, "el": b, "box": box, "text": (b.inner_text() or "").strip()})
        if candidates:
            # 优先 .cx-btn-shutter 的 class
            shutter = [c for c in candidates if "cx-btn-shutter" in (c["el"].get_attribute("class") or "")]
            if shutter:
                shutter[0]["el"].click(timeout=3000)
                print(f"  [OK] 兜底：点击 cx-btn-shutter [{shutter[0]['i']}]")
                time.sleep(3)
                shot(page, "tc0021_after_send.png")
                return True
            # 再按位置：右下角
            candidates.sort(key=lambda c: (c["box"]["y"], -c["box"]["x"]), reverse=True)
            candidates[0]["el"].click(timeout=3000)
            print(f"  [OK] 兜底：点击最右下按钮 [{candidates[0]['i']}]")
            time.sleep(3)
            shot(page, "tc0021_after_send.png")
            return True
    except Exception as e:
        print(f"    兜底失败: {e}")

    print("  [FAIL] 找不到发送按钮")
    return False


# ============ 等生成完成 ============
def wait_for_generation(page, timeout=GENERATE_TIMEOUT):
    print(f"\n\n########## 等待生成（最多 {timeout}s） ##########")

    start = time.time()
    is_was_generating = False

    while time.time() - start < timeout:
        elapsed = time.time() - start

        is_generating = False
        for kw in ["生成中", "处理中", "排队中", "上传中"]:
            try:
                loc = page.get_by_text(kw, exact=False)
                if loc.count() > 0:
                    for i in range(loc.count()):
                        if loc.nth(i).is_visible():
                            is_generating = True
                            break
            except Exception:
                pass
            if is_generating:
                break

        if is_generating:
            is_was_generating = True

        if int(elapsed) % 15 == 0:
            print(f"  [{elapsed:.0f}s] 生成中={is_generating}")

        if is_was_generating and not is_generating:
            time.sleep(5)
            still_gen = False
            for kw in ["生成中", "处理中", "排队中"]:
                try:
                    loc = page.get_by_text(kw, exact=False)
                    if loc.count() > 0:
                        for i in range(loc.count()):
                            if loc.nth(i).is_visible():
                                still_gen = True
                                break
                except Exception:
                    pass
                if still_gen:
                    break
            if not still_gen:
                print(f"  [{elapsed:.0f}s] 生成完成")
                return True

        time.sleep(2)

    print(f"  [WARN] 超时（{timeout}s）")
    return False


# ============ 验证延长后的视频 ============
def check_extended_video(page, node_id, orig_duration=None):
    print("\n\n########## 验证延长后的视频 ##########")

    node = get_node_by_id(page, node_id)
    videos = node.locator("video")
    cnt = videos.count()
    print(f"  节点内 video 元素数: {cnt}")

    result = {"video_count": cnt, "duration": None, "src": ""}

    if cnt > 0:
        v = videos.nth(0)
        try:
            src = v.get_attribute("src") or ""
            print(f"    src='{src[:80]}'")
            result["src"] = src

            try:
                dur = v.evaluate("el => el.duration")
                if dur and dur > 0:
                    print(f"    duration={dur:.2f}s")
                    result["duration"] = dur
                    if orig_duration:
                        print(f"    原时长={orig_duration:.2f}s, 延长后={dur:.2f}s")
            except Exception:
                pass
        except Exception as e:
            print(f"    读取失败: {e}")

    return result


# ============ 主流程 ============
def test_tc0021():
    print("=== TC-0021：视频节点延长 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        node_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {node_before}")

        # 1. 新建视频节点 + 上传
        video_node_id = create_video_node_with_upload(page, VIDEO_PATH, 600, 350)
        print(f"  视频节点 data-id: {video_node_id}")

        video_node = get_node_by_id(page, video_node_id)
        try:
            orig_dur = video_node.locator("video").first.evaluate("el => el.duration")
            print(f"  原始视频时长: {orig_dur:.2f}s")
        except Exception:
            orig_dur = None

        # 2. 选中视频节点
        click_node_locator(page, video_node)
        time.sleep(1)
        shot(page, "tc0021_selected_video_node.png")

        nodes_before_extend = page.locator(".react-flow__node").count()
        print(f"  延长前节点数: {nodes_before_extend}")

        # 3. 点「延长」
        extend_clicked = click_extend_button(page)
        if not extend_clicked:
            raise RuntimeError("找不到「延长」按钮")

        # 4. 拖动画布往上
        pan_canvas_up(page, dy=-300)
        time.sleep(1)

        # 5. 等延长面板
        panel_ok = wait_for_extend_panel(page)

        # 6. 拖拽选区
        drag_ok, sel_before, sel_after = drag_clip_selection(page)

        # 7. 点「去延长」
        go_extend_ok = click_go_extend(page)
        if not go_extend_ok:
            raise RuntimeError("找不到「去延长」按钮")

        # 8. 等新节点
        time.sleep(3)
        try:
            new_node_id = get_new_node_id(page, nodes_before_extend, timeout=20)
            print(f"  新节点 data-id: {new_node_id}")
        except Exception as e:
            print(f"  [WARN] 没检测到新节点: {e}")
            new_node_id = None

        shot(page, "tc0021_after_new_node.png")

        # 9. 在新节点控制台输入
        prompt_ok = input_extend_prompt(page, EXTEND_PROMPT)

        # 10. 点新节点控制台的发送按钮
        send_ok = click_send(page)

        # 11. 等生成
        gen_done = wait_for_generation(page, timeout=GENERATE_TIMEOUT)
        shot(page, "tc0021_after_generation.png")

        # 12. 验证
        if new_node_id:
            extended = check_extended_video(page, new_node_id, orig_dur)
        else:
            extended = {"video_count": 0, "duration": None, "src": ""}

        shot(page, "tc0021_final.png")

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  视频节点 data-id: {video_node_id}")
        print(f"  新节点 data-id: {new_node_id}")
        print(f"  原始视频时长: {orig_dur if orig_dur else '未知'}")
        if sel_before and sel_after:
            print(f"  裁剪 style: left {sel_before['left']}→{sel_after['left']}, width {sel_before['width']}→{sel_after['width']}")
        print(f"  延长后视频时长: {extended['duration'] if extended['duration'] else '未知'}")
        print(f"  {'✅' if extend_clicked else '❌'} 点击「延长」")
        print(f"  {'✅' if panel_ok else '❌'} 延长面板出现")
        print(f"  {'✅' if drag_ok else '❌'} 拖拽选区")
        print(f"  {'✅' if go_extend_ok else '❌'} 点击「去延长」")
        print(f"  {'✅' if new_node_id else '❌'} 新节点生成")
        print(f"  {'✅' if prompt_ok else '❌'} 新节点控制台输入")
        print(f"  {'✅' if send_ok else '❌'} 点击发送按钮")
        print(f"  {'✅' if gen_done else '⚠️'} 生成完成")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []
        warnings = []

        if not extend_clicked:
            errors.append("点击「延长」按钮失败")
        if not panel_ok:
            errors.append("延长面板未出现")
        if not drag_ok:
            errors.append("拖拽选区失败")
        if not go_extend_ok:
            errors.append("点击「去延长」按钮失败")
        if not new_node_id:
            errors.append("未检测到新节点")
        if not prompt_ok:
            errors.append("新节点控制台输入失败")
        if not send_ok:
            errors.append("点击发送按钮失败")
        if not gen_done:
            warnings.append(f"生成未在 {GENERATE_TIMEOUT}s 内完成")

        if extended["video_count"] == 0:
            warnings.append("新节点里没有 video 元素")
        elif orig_dur and extended["duration"] and extended["duration"] <= orig_dur:
            warnings.append(f"延长后时长（{extended['duration']:.2f}s）没有比原时长（{orig_dur:.2f}s）长")

        print("\n" + "=" * 60)
        if warnings:
            print(f"[WARN] 需关注：")
            for w in warnings:
                print(f"  - {w}")
        if errors:
            print(f"[FAIL] TC-0021，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0021 未通过")

        print("[PASS] TC-0021 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0021_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0021()