"""
TC-0016 自动化测试：切分图片后替换小图并合成
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 上传节点1：牛群.jpg（画布中间）
    2. 在画布右下角空白处创建节点2：羊群.jpg（避免提示词控制台遮挡节点1）
    3. 点节点1 → 切分 → 2×2 网格
    4. 点其中一个小格（选中一个小图）
    5. 弹出工具栏 → 点「替换」
    6. 点节点2（作为替换目标）
    7. 替换完成
    8. 点「合成」

关键 UI（从截图确认）：
    - 切分后点小格 → 工具栏出现：已选1个宫格 | 替换 | 添加到画布 | 下载
    - 节点下方有：还原 | 合成

定位策略（跨电脑可运行）：
    - 所有节点用 data-id 标识，不用屏幕坐标
    - 节点2创建位置动态找"远离节点1的右下角空白点"
    - 切分后的小格用节点内 img 的顺序定位
    - 替换弹窗里的图片用文字或排除法定位

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

_ABS_IMG2 = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群.jpg")
_REL_IMG2 = ROOT / "testdata" / "羊群.jpg"
IMG2_PATH = _ABS_IMG2 if _ABS_IMG2.exists() else _REL_IMG2

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


# ============ 通用工具 ============
def dblclick_canvas(page, x, y):
    print(f"\n=== 双击画布 ({x},{y}) ===")
    r = page.evaluate(f"""() => {{
        const el = document.elementFromPoint({x}, {y});
        if (!el) return 'none';
        return {{tag: el.tagName, cls: String(el.className || '').slice(0, 100)}};
    }}""")
    print(f"  落点元素: {r}")
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, f"tc0016_dblclick_{x}_{y}.png")


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


# ============ 【修改】动态找空白点（优先右下角） ============
def find_blank_canvas_point(page):
    """找一个远离所有已有节点的空白点（偏右下角，避免提示词控制台遮挡）"""
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    boxes = []
    for i in range(n):
        b = nodes.nth(i).bounding_box()
        if b:
            boxes.append(b)

    # 候选位置：优先右下角
    candidates = [
        (1150, 620), (1200, 650), (1100, 600), (1250, 620),
        (1150, 550), (1200, 550),
        # 兜底：其它角
        (300, 200), (1100, 200), (300, 600),
    ]

    for (x, y) in candidates:
        # 检查离所有节点是否 > 250px
        ok = True
        for b in boxes:
            if (b["x"] - 250 <= x <= b["x"] + b["width"] + 250 and
                b["y"] - 250 <= y <= b["y"] + b["height"] + 250):
                ok = False
                break
        if not ok:
            continue

        # 检查落点是不是画布
        r = page.evaluate(f"""() => {{
            const el = document.elementFromPoint({x}, {y});
            if (!el) return 'none';
            return String(el.className || '').slice(0, 100);
        }}""")
        print(f"  检查 ({x},{y}): class='{r}'")
        if "react-flow" in r or "pane" in r or "background" in r:
            print(f"  [OK] 找到空白点 ({x},{y})")
            return x, y

    print("  [WARN] 没找到理想空白点，用 (1150, 620)")
    return 1150, 620


# ============ 节点引用管理 ============
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
        print(f"  步骤1 OK: {file_dir}")
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
        print(f"  步骤2 OK: {file_name}")
    except Exception as e:
        print(f"  步骤2失败: {e}")

    return True


# ============ 新建图片节点 + 上传 ============
def create_image_node_with_upload(page, image_path, dblclick_x, dblclick_y, tag=""):
    print(f"\n\n########## 新建图片节点并上传：{image_path.name} {tag} ##########")

    before = page.locator(".react-flow__node").count()

    dblclick_canvas(page, dblclick_x, dblclick_y)

    try:
        click_menu_item(page, "图片节点")
    except RuntimeError:
        print("  [WARN] 菜单没弹出，换位置重试")
        x2, y2 = find_blank_canvas_point(page)
        dblclick_canvas(page, x2, y2)
        click_menu_item(page, "图片节点")

    time.sleep(1.5)
    node_id = get_new_node_id(page, before)
    shot(page, f"tc0016_after_add_node_{tag}.png")

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
    shot(page, f"tc0016_after_click_upload_{tag}.png")

    handle_system_dialog(image_path.parent, image_path.name)
    time.sleep(3)
    shot(page, f"tc0016_after_upload_{tag}.png")

    return node_id


# ============ 点击节点 ============
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


# ============ 切分 ============
def click_split_button(page):
    print("\n  点击「切分」按钮")
    for sel in ["button:text-is('切分')", "button:has-text('切分')"]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if "切分" in t:
                    box = el.bounding_box()
                    if box:
                        print(f"  找到「切分」按钮 [{i}] ({box['x']:.0f},{box['y']:.0f})")
                        el.click(timeout=3000)
                        time.sleep(1.5)
                        return True
        except Exception:
            pass
    try:
        el = page.get_by_text("切分", exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  get_by_text 点击")
            time.sleep(1.5)
            return True
    except Exception:
        pass
    print("  [FAIL]")
    return False


def click_split_grid(page, grid_text):
    print(f"\n  选切分网格：{grid_text}")
    try:
        el = page.get_by_text(grid_text, exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print(f"  [OK] 点击 '{grid_text}'")
            time.sleep(3)
            return True
    except Exception:
        pass
    for kw in [grid_text, grid_text.replace(" ", ""), grid_text.replace("×", "x")]:
        try:
            loc = page.get_by_text(kw, exact=False)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if "网格" in t:
                    el.click(timeout=3000)
                    print(f"  [OK] 点击 '{t}'")
                    time.sleep(3)
                    return True
        except Exception:
            pass
    print(f"  [FAIL] 找不到 '{grid_text}'")
    return False


# ============ 选中小格 ============
def select_grid_cell(page, node_locator):
    print("\n  在切分节点里点一个小格")

    imgs = node_locator.locator("img")
    cnt = imgs.count()
    print(f"    节点内 img 数: {cnt}")

    if cnt > 0:
        img = imgs.nth(0)
        box = img.bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            print(f"    点击 img[0] 中心 ({cx:.0f},{cy:.0f})")
            page.mouse.click(cx, cy)
            time.sleep(1.5)
            shot(page, "tc0016_selected_cell.png")
            return True

    for sel in ["[class*='cell']", "[class*='grid-item']", "[class*='sub-img']", "[class*='tile']"]:
        try:
            loc = node_locator.locator(sel)
            if loc.count() > 0:
                el = loc.nth(0)
                box = el.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    print(f"    [OK] 点击 {sel}")
                    time.sleep(1.5)
                    shot(page, "tc0016_selected_cell.png")
                    return True
        except Exception:
            pass

    print("    [FAIL] 找不到小格")
    return False


# ============ 点工具栏「替换」 ============
def click_replace_button(page):
    print("\n\n########## 点击工具栏「替换」 ##########")

    for kw in ["替换"]:
        try:
            loc = page.get_by_text(kw, exact=True)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box:
                    print(f"  找到「{kw}」({box['x']:.0f},{box['y']:.0f})")
                    el.click(timeout=3000)
                    print(f"  [OK] 点击「{kw}」")
                    time.sleep(2)
                    shot(page, "tc0016_after_click_replace.png")
                    return True
        except Exception:
            pass

    for kw in ["用图片替换", "替换"]:
        try:
            loc = page.get_by_text(kw, exact=False)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box and box["width"] < 150:
                    print(f"  兜底找到「{kw}」")
                    el.click(timeout=3000)
                    time.sleep(2)
                    shot(page, "tc0016_after_click_replace.png")
                    return True
        except Exception:
            pass

    print("  [FAIL] 找不到「替换」")
    return False


# ============ 点第二个节点完成替换 ============
def click_target_node(page, target_node_locator):
    print("\n\n########## 点目标节点完成替换 ##########")

    try:
        box = target_node_locator.bounding_box()
        if not box:
            print("  [FAIL] 目标节点没有 bounding_box")
            return False
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        print(f"  点击目标节点中心 ({cx:.0f},{cy:.0f})")
        page.mouse.click(cx, cy)
        print("  [OK] 已点击目标节点")
        time.sleep(3)
        shot(page, "tc0016_after_click_target.png")
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False


# ============ 点「合成」 ============
def click_merge_button(page):
    print("\n\n########## 点击「合成」 ##########")

    try:
        el = page.get_by_text("合成", exact=True).first
        if el.count() > 0 and el.is_visible():
            box = el.bounding_box()
            if box:
                print(f"  找到「合成」({box['x']:.0f},{box['y']:.0f})")
                el.click(timeout=3000)
                print("  [OK] 点击「合成」")
                time.sleep(3)
                shot(page, "tc0016_after_merge.png")
                return True
    except Exception:
        pass

    for kw in ["合成", "合并", "应用"]:
        try:
            loc = page.get_by_text(kw, exact=False)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box and box["width"] < 150:
                    el.click(timeout=3000)
                    print(f"  [OK] 兜底点击「{kw}」")
                    time.sleep(3)
                    shot(page, "tc0016_after_merge.png")
                    return True
        except Exception:
            pass

    print("  [FAIL] 找不到「合成」")
    return False


# ============ 验证 ============
def check_result(page, tag=""):
    print(f"\n\n########## 验证结果 {tag} ##########")
    nodes = page.locator(".react-flow__node")
    imgs = page.locator(".react-flow__node img")
    print(f"  节点总数: {nodes.count()}")
    print(f"  img 总数: {imgs.count()}")
    return {"node_count": nodes.count(), "img_count": imgs.count()}


# ============ 主流程 ============
def test_tc0016():
    print("=== TC-0016：切分后替换小图并合成 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        print(f"[INFO] 初始节点数: {page.locator('.react-flow__node').count()}")

        # ============ 1. 上传节点1：牛群.jpg（画布中间） ============
        node1_id = create_image_node_with_upload(page, IMG1_PATH, 600, 400, tag="niunqun")
        print(f"  节点1 data-id: {node1_id}")

        # ============ 2. 找右下角空白点，上传节点2：羊群.jpg ============
        print("\n\n########## 找右下角空白点，准备创建节点2 ##########")
        blank_x, blank_y = find_blank_canvas_point(page)
        node2_id = create_image_node_with_upload(page, IMG2_PATH, blank_x, blank_y, tag="yangqun")
        print(f"  节点2 data-id: {node2_id}")

        shot(page, "tc0016_after_upload_both.png")

        # ============ 3. 点节点1，切分 2×2 ============
        print("\n\n########## 切分节点1（2×2）##########")
        node1 = get_node_by_id(page, node1_id)
        click_node_locator(page, node1)
        time.sleep(1)
        shot(page, "tc0016_selected_node1.png")

        split_ok = click_split_button(page)
        shot(page, "tc0016_after_click_split.png")

        grid_ok = False
        if split_ok:
            grid_ok = click_split_grid(page, "2×2 网格")
            if not grid_ok:
                grid_ok = click_split_grid(page, "2x2 网格")
            shot(page, "tc0016_after_split.png")
        time.sleep(2)

        # ============ 4. 点小格 ============
        print("\n\n########## 选中小格 ##########")
        node1 = get_node_by_id(page, node1_id)
        cell_ok = select_grid_cell(page, node1)

        # ============ 5. 点工具栏「替换」 ============
        replace_ok = click_replace_button(page)

        # ============ 6. 点节点2完成替换 ============
        click_ok = False
        if replace_ok:
            node2 = get_node_by_id(page, node2_id)
            click_ok = click_target_node(page, node2)

        # ============ 7. 点「合成」 ============
        time.sleep(2)
        node1 = get_node_by_id(page, node1_id)
        click_node_locator(page, node1)
        time.sleep(1)

        merge_ok = click_merge_button(page)

        time.sleep(3)
        check_result(page, "合成后")
        shot(page, "tc0016_final.png")

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  node1_id: {node1_id}")
        print(f"  node2_id: {node2_id}")
        print(f"  {'✅' if split_ok else '❌'} 点「切分」")
        print(f"  {'✅' if grid_ok else '❌'} 选 2×2 网格")
        print(f"  {'✅' if cell_ok else '❌'} 选中小格")
        print(f"  {'✅' if replace_ok else '❌'} 点「替换」")
        print(f"  {'✅' if click_ok else '❌'} 点节点2完成替换")
        print(f"  {'✅' if merge_ok else '❌'} 点「合成」")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        if not node1_id:
            errors.append("节点1 data-id 为空")
        if not node2_id:
            errors.append("节点2 data-id 为空")
        if not split_ok:
            errors.append("点击「切分」失败")
        if not grid_ok:
            errors.append("未成功选 2×2 网格")
        if not cell_ok:
            errors.append("未选中小格")
        if not replace_ok:
            errors.append("未点击「替换」")
        if not click_ok:
            errors.append("未点击节点2完成替换")
        if not merge_ok:
            errors.append("未点击「合成」")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0016，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0016 未通过")

        print("[PASS] TC-0016 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0016_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0016()