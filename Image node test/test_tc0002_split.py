"""
TC-0015 自动化测试：图片节点切分（2x2 和 4x4 网格）
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布中心 (600,400) → 新建图片节点1 → 上传 牛群.jpg
    2. 选中节点1 → 点「切分」→ 选 2×2 网格
    3. 拖动画布（平移），把节点移开，避免遮挡
    4. 双击画布另一处 → 新建图片节点2 → 上传 草原.jpg
    5. 选中节点2 → 点「切分」→ 选 4×4 网格
    6. 验证

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

_ABS_IMG2 = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\草原.jpg")
_REL_IMG2 = ROOT / "testdata" / "草原.jpg"
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


# ============ 诊断：打印节点位置 ============
def dump_node_positions(page, tag=""):
    print(f"\n  当前节点位置（{tag}）：")
    nodes = page.locator(".react-flow__node")
    cnt = nodes.count()
    if cnt == 0:
        print("    没有节点")
        return []
    result = []
    for i in range(cnt):
        b = nodes.nth(i).bounding_box()
        if b:
            print(f"    node[{i}] pos=({b['x']:.0f},{b['y']:.0f}) size=({b['width']:.0f}x{b['height']:.0f})")
            result.append({"idx": i, "x": b["x"], "y": b["y"], "w": b["width"], "h": b["height"]})
    return result


# ============ 诊断：检查位置是不是画布空白 ============
def check_point_is_canvas_blank(page, x, y):
    result = page.evaluate(f"""() => {{
        const el = document.elementFromPoint({x}, {y});
        if (!el) return {{ tag: 'none', cls: '' }};
        return {{
            tag: el.tagName,
            cls: String(el.className || '').slice(0, 120),
        }};
    }}""")
    print(f"  ({x},{y}) 处的元素: tag={result['tag']} class='{result['cls']}'")
    return result


# ============ 双击画布 ============
def dblclick_canvas(page, x, y):
    print(f"\n=== 双击画布 ({x},{y}) ===")
    check_point_is_canvas_blank(page, x, y)
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, f"tc0015_dblclick_{x}_{y}.png")


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


# ============ 拖动画布 ============
def pan_canvas(page, from_x, from_y, to_x, to_y):
    """在画布空白处按左键拖动，平移画布"""
    print(f"\n=== 拖动画布 ({from_x},{from_y}) → ({to_x},{to_y}) ===")

    # 先检查起点是不是画布空白
    result = check_point_is_canvas_blank(page, from_x, from_y)
    if "react-flow" not in result["cls"] and "canvas" not in result["cls"].lower():
        print(f"  [WARN] 起点 ({from_x},{from_y}) 可能不是画布空白，元素是 {result['tag']}.{result['cls'][:50]}")
        # 尝试往左上角移动起点
        for nx, ny in [(250, 200), (200, 150), (300, 250), (150, 200)]:
            r2 = check_point_is_canvas_blank(page, nx, ny)
            if "react-flow" in r2["cls"] or "canvas" in r2["cls"].lower():
                from_x, from_y = nx, ny
                print(f"  → 改用起点 ({nx},{ny})")
                break

    page.mouse.move(from_x, from_y)
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.3)
    steps = 20
    for i in range(1, steps + 1):
        x = from_x + (to_x - from_x) * i / steps
        y = from_y + (to_y - from_y) * i / steps
        page.mouse.move(x, y)
        time.sleep(0.02)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1.5)
    shot(page, "tc0015_after_pan.png")
    dump_node_positions(page, "拖动画布后")


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

    print("\n  [步骤1] Alt+D 地址栏 → 输目录 → 回车")
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
            print(f"  已粘贴目录: {file_dir}")
        else:
            send_keys(str(file_dir), with_spaces=True, pause=0.02)
            time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(2)
    except Exception as e:
        print(f"  步骤1失败: {e}")

    print("\n  [步骤2] Alt+N 文件名框 → 输文件名 → 回车")
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
            print(f"  已粘贴文件名: {file_name}")
        else:
            send_keys(str(file_name), with_spaces=True, pause=0.02)
            time.sleep(0.5)
        send_keys("{ENTER}")
        time.sleep(3)
    except Exception as e:
        print(f"  步骤2失败: {e}")

    return True


# ============ 新建图片节点 + 上传 ============
def create_image_node_and_upload(page, image_path, canvas_x, canvas_y, tag=""):
    print(f"\n\n########## 新建图片节点并上传：{image_path.name} {tag} ##########")

    node_before = page.locator(".react-flow__node").count()

    dblclick_canvas(page, canvas_x, canvas_y)
    click_menu_item(page, "图片节点")
    time.sleep(1.5)
    wait_for_new_node(page, node_before, timeout=15)
    shot(page, f"tc0015_after_add_node_{tag}.png")

    nodes = page.locator(".react-flow__node")
    node = nodes.nth(nodes.count() - 1)
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
        return False

    try:
        upload_btn.click(timeout=3000)
        print("  [OK] 点击「上传」按钮")
    except Exception as e:
        print(f"  点击失败: {e}")
        try:
            upload_btn.click(timeout=3000, force=True)
        except Exception as e2:
            print(f"  force 也失败: {e2}")
            return False

    time.sleep(3)
    shot(page, f"tc0015_after_click_upload_{tag}.png")

    ok = handle_system_dialog(image_path.parent, image_path.name)
    time.sleep(3)
    shot(page, f"tc0015_after_upload_{tag}.png")

    return ok


# ============ 选中节点 ============
def click_node(page, index_from_end=0):
    nodes = page.locator(".react-flow__node")
    cnt = nodes.count()
    if cnt == 0:
        raise RuntimeError("画布上没有节点")
    idx = cnt - 1 - index_from_end
    if idx < 0:
        raise RuntimeError(f"节点索引越界")
    node = nodes.nth(idx)
    box = node.bounding_box()
    if not box:
        raise RuntimeError("节点没有 bounding_box")
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    print(f"  点击节点 [{idx}] 中心 ({cx:.0f},{cy:.0f})")
    page.mouse.click(cx, cy)
    time.sleep(1.5)
    return node


# ============ 点击「切分」按钮 ============
def click_split_button(page):
    print("\n  点击「切分」按钮")
    for sel in [
        "button:text-is('切分')",
        "button:has-text('切分')",
    ]:
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
                        print(f"  找到「切分」按钮: {sel} [{i}] ({box['x']:.0f},{box['y']:.0f})")
                        el.click(timeout=3000)
                        time.sleep(1.5)
                        return True
        except Exception:
            pass

    try:
        el = page.get_by_text("切分", exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("  通过 get_by_text('切分') 点击")
            time.sleep(1.5)
            return True
    except Exception as e:
        print(f"  get_by_text 失败: {e}")

    print("  [FAIL] 找不到「切分」按钮")
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
    except Exception as e:
        print(f"  get_by_text 失败: {e}")

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
                    print(f"  [OK] 通过包含匹配点击 '{t}'")
                    time.sleep(3)
                    return True
        except Exception:
            pass

    print(f"  [FAIL] 找不到 '{grid_text}'")
    return False


# ============ 验证切分结果 ============
def check_split_result(page, tag=""):
    print(f"\n\n########## 验证切分结果 {tag} ##########")
    nodes = page.locator(".react-flow__node")
    imgs = page.locator(".react-flow__node img")
    print(f"  画布上节点总数: {nodes.count()}")
    print(f"  节点内 img 总数: {imgs.count()}")
    return {"node_count": nodes.count(), "img_count": imgs.count()}


# ============ 主流程 ============
def test_tc0015():
    print("=== TC-0015：图片节点切分 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        print(f"[INFO] 初始节点数: {page.locator('.react-flow__node').count()}")

        # ============ 1. 新建节点1，上传 牛群.jpg（画布中心） ============
        ok1 = create_image_node_and_upload(page, IMG1_PATH, 600, 400, tag="img1")
        dump_node_positions(page, "上传节点1后")

        # ============ 2. 切分节点1：2x2 ============
        print("\n\n########## 切分节点1（2x2）##########")
        click_node(page, index_from_end=0)
        time.sleep(1.5)
        shot(page, "tc0015_selected_node1.png")

        split_ok_1 = click_split_button(page)
        shot(page, "tc0015_after_click_split_1.png")

        grid_ok_1 = False
        if split_ok_1:
            grid_ok_1 = click_split_grid(page, "2×2 网格")
            if not grid_ok_1:
                grid_ok_1 = click_split_grid(page, "2x2 网格")
            shot(page, "tc0015_after_split_2x2.png")
        time.sleep(2)
        state_after_split1 = check_split_result(page, "切分 2x2 后")
        dump_node_positions(page, "切分2x2后")

        # ============ 3. 拖动画布 ============
        print("\n\n########## 拖动画布 ##########")
        # 起点改到画布空白处 (300, 200)，不要用 (200, 700)
        pan_canvas(page, 300, 200, 900, 250)
        time.sleep(1)

        # ============ 4. 新建节点2，上传 草原.jpg ============
        # 拖动后节点应该在别的位置，双击 (700, 400) 或另一处
        # 先看节点位置，再选落点
        positions = dump_node_positions(page, "拖动画布后")
        # 简单策略：双击画布中心 (600, 400)，如果那有节点就换 (350, 250)
        target_x, target_y = 600, 400
        for p in positions:
            if (p["x"] <= target_x <= p["x"] + p["w"] and
                p["y"] <= target_y <= p["y"] + p["h"]):
                print(f"  [WARN] ({target_x},{target_y}) 落在节点上，换点")
                target_x, target_y = 350, 250
                break

        ok2 = create_image_node_and_upload(page, IMG2_PATH, target_x, target_y, tag="img2")
        dump_node_positions(page, "上传节点2后")
        shot(page, "tc0015_after_upload_img2.png")

        # ============ 5. 切分节点2：4x4 ============
        print("\n\n########## 切分节点2（4x4）##########")
        click_node(page, index_from_end=0)
        time.sleep(1.5)
        shot(page, "tc0015_selected_node2.png")

        split_ok_2 = click_split_button(page)
        shot(page, "tc0015_after_click_split_2.png")

        grid_ok_2 = False
        if split_ok_2:
            grid_ok_2 = click_split_grid(page, "4×4 网格")
            if not grid_ok_2:
                grid_ok_2 = click_split_grid(page, "4x4 网格")
            shot(page, "tc0015_after_split_4x4.png")
        time.sleep(2)
        state_after_split2 = check_split_result(page, "切分 4x4 后")
        shot(page, "tc0015_final.png")

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  {'✅' if ok1 else '❌'} 上传节点1：牛群.jpg")
        print(f"  {'✅' if split_ok_1 else '❌'} 节点1点「切分」")
        print(f"  {'✅' if grid_ok_1 else '❌'} 节点1选 2×2 网格")
        print(f"  {'✅' if ok2 else '❌'} 上传节点2：草原.jpg")
        print(f"  {'✅' if split_ok_2 else '❌'} 节点2点「切分」")
        print(f"  {'✅' if grid_ok_2 else '❌'} 节点2选 4×4 网格")
        print(f"  切分2x2后节点数: {state_after_split1['node_count']}, img: {state_after_split1['img_count']}")
        print(f"  切分4x4后节点数: {state_after_split2['node_count']}, img: {state_after_split2['img_count']}")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        if not ok1:
            errors.append("节点1上传图片失败")
        if not split_ok_1:
            errors.append("节点1点击「切分」失败")
        if not grid_ok_1:
            errors.append("节点1未成功选 2×2 网格")
        if not ok2:
            errors.append("节点2上传图片失败")
        if not split_ok_2:
            errors.append("节点2点击「切分」失败")
        if not grid_ok_2:
            errors.append("节点2未成功选 4×4 网格")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0015，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0015 未通过")

        print("[PASS] TC-0015 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0015_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0015()