"""
TC-0004 自动化测试：视频节点反推（电商复刻 + 分析BGM + 生成提示词/参考图）
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布 → 新建视频节点（偏上 y=280）
    2. 上传本地视频 四季更迭.mp4（有声音）
    3. 【新顺序】先拖动画布往上一点，让视频节点上移，给反推工作台留空间
    4. 选中视频节点
    5. 点工具栏【反推】
    6. 弹出"提示词反推"工作台（不会被中控台遮挡）
    7. 选择【电商复刻】方向
    8. 打开【分析 BGM】开关
    9. 点【开始反推】
    10. 等待生成完成
    11. 验证：提示词文本节点 + 3 张参考图 + 连线

F12 关键 DOM：
    - 工作台：<div class="cx-popover" data-popover-group="prompt-reverse-options">
    - 反推方向：<div data-testid="pr-scene">
    - 分析 BGM：<div data-testid="pr-bgm">
    - 开始反推：<button data-testid="pr-start">

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

_ABS_VIDEO = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\四季更迭.mp4")
_REL_VIDEO = ROOT / "testdata" / "四季更迭.mp4"
VIDEO_PATH = _ABS_VIDEO if _ABS_VIDEO.exists() else _REL_VIDEO

REVERSE_TIMEOUT = 300

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

PANEL_SELECTOR = '.cx-popover[data-popover-group="prompt-reverse-options"]'
PR_SCENE_SELECTOR = '[data-testid="pr-scene"]'
PR_BGM_SELECTOR = '[data-testid="pr-bgm"]'
PR_START_SELECTOR = '[data-testid="pr-start"]'


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
def dblclick_canvas(page, x=600, y=280):
    """双击画布，位置偏上 y=280（比之前的 y=350 更靠上）"""
    print(f"\n=== 双击画布 ({x},{y}) ===")
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, f"tc0022_dblclick_{x}_{y}.png")


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
def pan_canvas_up(page, dy=-200):
    """
    在画布左侧空白处按住往上拖，让画布内容上移。
    dy=-200：适度上移，不会把节点拖到看不见。
    """
    print(f"\n=== 拖动画布往上（dy={dy}）===")

    start_points = [
        (300, 500), (300, 450), (300, 400),
        (350, 500), (350, 450),
        (250, 500), (250, 450),
        (400, 500),
    ]

    start_x, start_y = None, None
    for (x, y) in start_points:
        try:
            r = page.evaluate(f"""() => {{
                const el = document.elementFromPoint({x}, {y});
                if (!el) return 'none';
                return String(el.className || '').slice(0, 120);
            }}""")
            print(f"  检查 ({x},{y}): class='{r}'")
            if "react-flow" in r or "pane" in r or "background" in r:
                start_x, start_y = x, y
                print(f"  [OK] 起点 ({x},{y})")
                break
        except Exception:
            pass

    if start_x is None:
        print("  [WARN] 没找到画布空白起点，用 (300, 500)")
        start_x, start_y = 300, 500

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
    shot(page, "tc0022_after_pan.png")


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
def create_video_node_with_upload(page, video_path, dblclick_x=600, dblclick_y=280):
    print(f"\n\n########## 新建视频节点并上传：{video_path.name} ##########")

    before = page.locator(".react-flow__node").count()

    dblclick_canvas(page, dblclick_x, dblclick_y)
    click_menu_item(page, "视频节点")
    time.sleep(1.5)
    node_id = get_new_node_id(page, before)
    shot(page, "tc0022_after_add_node.png")

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
    shot(page, "tc0022_after_click_upload.png")

    handle_system_dialog(video_path.parent, video_path.name)
    time.sleep(8)
    shot(page, "tc0022_after_upload.png")

    return node_id


# ============ 点工具栏「反推」 ============
def click_toolbar_reverse(page):
    print("\n\n########## 点击工具栏「反推」 ##########")

    kw = "反推"

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
                    shot(page, "tc0022_after_click_reverse.png")
                    return True
        except Exception:
            pass

    try:
        el = page.get_by_text(kw, exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print(f"  get_by_text 点击「{kw}」")
            time.sleep(2.5)
            shot(page, "tc0022_after_click_reverse.png")
            return True
    except Exception:
        pass

    print("  [FAIL] 找不到工具栏「反推」按钮")
    return False


# ============ 等反推工作台 ============
def wait_for_reverse_panel(page, timeout=10):
    print("\n\n########## 等待反推工作台出现 ##########")

    start = time.time()
    while time.time() - start < timeout:
        try:
            panel = page.locator(PANEL_SELECTOR)
            if panel.count() > 0:
                for i in range(panel.count()):
                    if panel.nth(i).is_visible():
                        print(f"  [OK] 反推工作台出现（{time.time()-start:.1f}s）")
                        shot(page, "tc0022_reverse_panel.png")
                        return True
        except Exception:
            pass
        time.sleep(0.5)

    print("  [WARN] 未检测到反推工作台")
    return False


# ============ 选「电商复刻」 ============
def select_dianshang_direction(page):
    print("\n\n########## 选择「电商复刻」方向 ##########")

    scene = page.locator(PR_SCENE_SELECTOR).first
    if scene.count() == 0:
        print("  [FAIL] 找不到反推方向区域 pr-scene")
        return False

    box = scene.bounding_box()
    if box:
        print(f"  反推方向区域: pos=({box['x']:.0f},{box['y']:.0f}) size=({box['width']:.0f}x{box['height']:.0f})")

    try:
        btns = scene.locator("button")
        print(f"  区域内 button 数: {btns.count()}")
        for i in range(btns.count()):
            b = btns.nth(i)
            t = (b.inner_text() or "").strip()
            print(f"    button[{i}] text='{t}'")
    except Exception:
        pass

    # 方法 1：pr-scene 内找"电商复刻"
    try:
        el = scene.locator("button:has-text('电商复刻')").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  [OK] 点击「电商复刻」（pr-scene 内 button）")
            time.sleep(1.5)
            shot(page, "tc0022_after_select_dianshang.png")
            return True
    except Exception as e:
        print(f"  pr-scene 内 button 失败: {e}")

    # 方法 2：工作台内 text
    try:
        panel = page.locator(PANEL_SELECTOR).first
        el = panel.locator("text=电商复刻").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  [OK] 点击「电商复刻」（工作台内 text）")
            time.sleep(1.5)
            shot(page, "tc0022_after_select_dianshang.png")
            return True
    except Exception as e:
        print(f"  工作台内 text 失败: {e}")

    print("  [FAIL] 找不到「电商复刻」")
    return False


# ============ 打开「分析 BGM」 ============
def toggle_analyze_bgm(page):
    print("\n\n########## 打开「分析 BGM」开关 ##########")

    bgm_row = page.locator(PR_BGM_SELECTOR).first
    if bgm_row.count() == 0:
        print("  [FAIL] 找不到分析 BGM 区域 pr-bgm")
        return False

    box = bgm_row.bounding_box()
    if box:
        print(f"  分析 BGM 区域: pos=({box['x']:.0f},{box['y']:.0f}) size=({box['width']:.0f}x{box['height']:.0f})")

    try:
        html = bgm_row.inner_html()
        print(f"  pr-bgm inner HTML: {html[:300]}")
    except Exception:
        pass

    # 方法 1：内部 checkbox/switch/button
    for sel in [
        "input[type='checkbox']",
        "button[role='switch']",
        "[role='switch']",
        "button",
    ]:
        try:
            el = bgm_row.locator(sel).first
            if el.count() > 0 and el.is_visible():
                is_checked = False
                try:
                    if "checkbox" in sel:
                        is_checked = el.is_checked()
                    else:
                        aria = el.get_attribute("aria-checked") or ""
                        is_checked = (aria == "true")
                except Exception:
                    pass
                print(f"  找到 {sel}，当前 is_checked={is_checked}")

                if not is_checked:
                    el.click(timeout=3000)
                    print(f"  [OK] 点击 {sel} 打开开关")
                    time.sleep(1)
                else:
                    print(f"  已经是打开状态")
                shot(page, "tc0022_after_toggle_bgm.png")
                return True
        except Exception as e:
            print(f"    {sel} 失败: {e}")

    # 方法 2：点 pr-bgm 行右侧
    try:
        page.mouse.click(box["x"] + box["width"] - 30, box["y"] + box["height"] / 2)
        print("  [OK] 点击 pr-bgm 行右侧")
        time.sleep(1)
        shot(page, "tc0022_after_toggle_bgm.png")
        return True
    except Exception as e:
        print(f"  点击 pr-bgm 行失败: {e}")

    print("  [FAIL] 无法打开分析 BGM 开关")
    return False


# ============ 点「开始反推」 ============
def click_start_reverse(page):
    print("\n\n########## 点击「开始反推」 ##########")

    el = page.locator(PR_START_SELECTOR).first
    if el.count() == 0:
        print("  [FAIL] 找不到开始反推按钮 pr-start")
        return False

    box = el.bounding_box()
    if box:
        print(f"  找到按钮: pos=({box['x']:.0f},{box['y']:.0f}) size=({box['width']:.0f}x{box['height']:.0f})")

    try:
        el.click(timeout=3000)
        print("  [OK] 点击「开始反推」")
        time.sleep(2.5)
        shot(page, "tc0022_after_start_reverse.png")
        return True
    except Exception as e:
        print(f"  点击失败: {e}")
        try:
            el.click(timeout=3000, force=True)
            print("  [OK] force 点击成功")
            time.sleep(2.5)
            shot(page, "tc0022_after_start_reverse.png")
            return True
        except Exception as e2:
            print(f"  force 也失败: {e2}")
            return False


# ============ 等反推完成 ============
def wait_for_reverse_done(page, nodes_before, timeout=REVERSE_TIMEOUT):
    print(f"\n\n########## 等待反推完成（最多 {timeout}s） ##########")
    print(f"  反推前节点数: {nodes_before}")

    start = time.time()
    last_count = nodes_before

    while time.time() - start < timeout:
        elapsed = time.time() - start
        cur = page.locator(".react-flow__node").count()

        if cur != last_count:
            print(f"  [{elapsed:.0f}s] 节点数: {last_count} → {cur}")
            last_count = cur

        if cur - nodes_before >= 4:
            time.sleep(5)
            final = page.locator(".react-flow__node").count()
            print(f"  [{elapsed:.0f}s] 稳定后节点数: {final}")
            if final - nodes_before >= 4:
                print(f"  [OK] 反推完成，新增 {final - nodes_before} 个节点")
                return True

        if int(elapsed) % 10 == 0:
            print(f"  [{elapsed:.0f}s] 等待中... 当前节点数={cur}")

        time.sleep(2)

    print(f"  [WARN] 超时（{timeout}s）")
    return False


# ============ 检查反推结果 ============
def check_reverse_result(page, nodes_before):
    print("\n\n########## 检查反推结果 ##########")

    result = {
        "total_new_nodes": 0,
        "text_nodes": [],
        "image_nodes": [],
        "edge_count": 0,
        "prompt_content": "",
        "reference_images": [],
    }

    nodes = page.locator(".react-flow__node")
    total = nodes.count()
    print(f"  画布上节点总数: {total}（反推前 {nodes_before}）")

    result["total_new_nodes"] = total - nodes_before

    for i in range(nodes_before, total):
        try:
            node = nodes.nth(i)
            data_id = node.get_attribute("data-id") or ""
            text = (node.inner_text() or "").strip()

            imgs = node.locator("img")
            img_count = imgs.count()

            info = {
                "index": i,
                "data_id": data_id,
                "text": text[:200],
                "img_count": img_count,
            }

            print(f"    新增节点 [{i}] data_id={data_id}")
            print(f"      text='{text[:80]}'")
            print(f"      img_count={img_count}")

            if img_count > 0:
                srcs = []
                for j in range(img_count):
                    try:
                        src = imgs.nth(j).get_attribute("src") or ""
                        srcs.append(src[:80])
                    except Exception:
                        pass
                info["img_srcs"] = srcs
                result["image_nodes"].append(info)
                result["reference_images"].extend(srcs)
            elif text:
                result["text_nodes"].append(info)
        except Exception as e:
            print(f"    读取节点 [{i}] 失败: {e}")

    try:
        edges = page.locator(".react-flow__edge")
        result["edge_count"] = edges.count()
        print(f"  连线数: {result['edge_count']}")
    except Exception as e:
        print(f"  读取连线失败: {e}")

    if result["text_nodes"]:
        all_text = "\n".join([n["text"] for n in result["text_nodes"]])
        result["prompt_content"] = all_text
        print(f"\n  提示词内容（前 500 字）:")
        print(f"    {all_text[:500]}")

    return result


# ============ 主流程 ============
def test_tc0022():
    print("=== TC-0022：视频节点反推（电商复刻 + 分析BGM）===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        node_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {node_before}")

        # ============ 1. 新建视频节点（偏上 y=280） ============
        video_node_id = create_video_node_with_upload(page, VIDEO_PATH, 600, 280)
        print(f"  视频节点 data-id: {video_node_id}")

        # ============ 2. 【关键】上传完后立即拖动画布往上 ============
        # 让视频节点上移，给下方反推工作台留空间
        pan_canvas_up(page, dy=-100)
        time.sleep(1)
        shot(page, "tc0022_after_pan_before_reverse.png")

        # ============ 3. 选中视频节点 ============
        video_node = get_node_by_id(page, video_node_id)
        click_node_locator(page, video_node)
        time.sleep(1)
        shot(page, "tc0022_selected_video_node.png")

        nodes_before_reverse = page.locator(".react-flow__node").count()
        print(f"  反推前节点数: {nodes_before_reverse}")

        # ============ 4. 点工具栏「反推」 ============
        reverse_clicked = click_toolbar_reverse(page)
        if not reverse_clicked:
            raise RuntimeError("找不到工具栏「反推」按钮")

        # ============ 5. 等反推工作台出现 ============
        panel_ok = wait_for_reverse_panel(page)

        # ============ 6. 选「电商复刻」 ============
        dianshang_ok = select_dianshang_direction(page)

        # ============ 7. 打开「分析 BGM」 ============
        bgm_ok = toggle_analyze_bgm(page)

        # ============ 8. 点「开始反推」 ============
        start_ok = click_start_reverse(page)

        # ============ 9. 等反推完成 ============
        reverse_done = wait_for_reverse_done(page, nodes_before_reverse, timeout=REVERSE_TIMEOUT)
        shot(page, "tc0022_after_reverse.png")

        # ============ 10. 检查结果 ============
        result = check_reverse_result(page, nodes_before_reverse)
        shot(page, "tc0022_result_detail.png")

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  视频节点 data-id: {video_node_id}")
        print(f"  {'✅' if reverse_clicked else '❌'} 点击工具栏「反推」")
        print(f"  {'✅' if panel_ok else '❌'} 反推工作台出现")
        print(f"  {'✅' if dianshang_ok else '❌'} 选择「电商复刻」")
        print(f"  {'✅' if bgm_ok else '❌'} 打开「分析 BGM」")
        print(f"  {'✅' if start_ok else '❌'} 点击「开始反推」")
        print(f"  {'✅' if reverse_done else '⚠️'} 反推完成")
        print(f"  新增节点数: {result['total_new_nodes']}")
        print(f"  文本节点数: {len(result['text_nodes'])}")
        print(f"  图片节点数: {len(result['image_nodes'])}")
        print(f"  参考图总数: {len(result['reference_images'])}")
        print(f"  连线数: {result['edge_count']}")

        if result["prompt_content"]:
            print(f"\n  提示词内容（前 300 字）:")
            print(f"    {result['prompt_content'][:300]}")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []
        warnings = []

        if not reverse_clicked:
            errors.append("点击工具栏「反推」失败")
        if not panel_ok:
            errors.append("反推工作台未出现")
        if not dianshang_ok:
            errors.append("选择「电商复刻」失败")
        if not bgm_ok:
            errors.append("打开「分析 BGM」失败")
        if not start_ok:
            errors.append("点击「开始反推」失败")
        if not reverse_done:
            warnings.append(f"反推未在 {REVERSE_TIMEOUT}s 内完成")

        if len(result["text_nodes"]) < 1:
            errors.append(f"未生成提示词文本节点（实际 {len(result['text_nodes'])} 个）")
        if len(result["reference_images"]) < 3:
            errors.append(f"未生成 3 张参考图（实际 {len(result['reference_images'])} 张）")

        if result["prompt_content"]:
            keywords = ["规格", "比例", "分镜", "时长", "景别", "运镜", "镜头"]
            found = [k for k in keywords if k in result["prompt_content"]]
            print(f"  提示词含关键词: {found}")
            if not found:
                warnings.append("提示词未包含预期关键词（规格/比例/分镜/时长/景别/运镜/镜头）")

        if result["edge_count"] == 0:
            warnings.append("未检测到连线（提示词节点与参考图应该有关联）")

        print("\n" + "=" * 60)
        if warnings:
            print(f"[WARN] 需关注：")
            for w in warnings:
                print(f"  - {w}")
        if errors:
            print(f"[FAIL] TC-0022，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0022 未通过")

        print("[PASS] TC-0022 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0022_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0022()