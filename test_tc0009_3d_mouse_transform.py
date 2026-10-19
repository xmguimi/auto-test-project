"""
TC-0009 自动化测试（务实版）：3D 导演台 - 变换模式切换验证
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

可自动化覆盖：
    1. 进入 3D 导演台，点击角色01
    2. 点击底部「移动」「旋转」「缩放」三个模式按钮
    3. 验证按钮切换成功（class 变化 / 选中态）
    4. 读取右侧参数面板的值（位置/旋转/缩放 XYZ）
    5. 验证参数面板显示正常

不可自动化覆盖（本脚本不做，需人工验证）：
    ❌ 鼠标拖拽 3D gizmo 改变参数
    ❌ 拖拽时参数实时跟随

原因说明：
    帧境 3D 视口用 Three.js 渲染，gizmo 是 Canvas 里的图形，不是 DOM。
    Playwright 无法精确定位；3D 引擎拒绝 Playwright 的合成鼠标事件，
    只能用 pyautogui 发真实鼠标事件，但屏幕坐标依赖分辨率/窗口/相机
    视角，无法跨电脑稳定自动化。
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 9222
ROOT = Path(__file__).parent

MODE_BTN_X_RANGE = (450, 620)
MODE_BTN_Y_MIN = 780

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"[SHOT] {name}")
    except Exception:
        pass


def is_cdp_ready(port=PORT):
    try:
        return requests.get(f"http://localhost:{port}/json/version", timeout=1).status_code == 200
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
    return pw, browser, target or pages[0]


# ============ 进入 3D ============
def dblclick_canvas(page):
    page.mouse.dblclick(600, 400)
    time.sleep(1.5)


def click_menu_item(page, kw):
    for sel in [f".cm-item:has-text('{kw}')", f"li:has-text('{kw}')"]:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible() and el.bounding_box():
                    el.click(timeout=3000)
                    return True
        except Exception:
            pass
    raise RuntimeError(f"找不到 '{kw}'")


def wait_for_new_node(page, before, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if page.locator(".react-flow__node").count() > before:
            return
        time.sleep(1)
    raise RuntimeError("新节点未出现")


def dblclick_3d_node(page):
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    node = nodes.nth(n - 1)
    box = node.bounding_box()
    page.mouse.dblclick(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(3.5)


def click_role_01(page):
    for sel in ["li:has-text('角色01')", "div[class*='role']:has-text('角色01')"]:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if not box or box["width"] > 400 or box["height"] > 150:
                    continue
                el.click(timeout=3000)
                time.sleep(2)
                return True
        except Exception:
            pass
    raise RuntimeError("找不到角色01")


# ============ 模式按钮 ============
def find_mode_buttons(page):
    all_buttons = page.locator("button")
    n = all_buttons.count()
    x_min, x_max = MODE_BTN_X_RANGE
    candidates = []
    for i in range(n):
        try:
            btn = all_buttons.nth(i)
            if not btn.is_visible():
                continue
            box = btn.bounding_box()
            if not box:
                continue
            if not (x_min <= box["x"] <= x_max):
                continue
            if box["y"] < MODE_BTN_Y_MIN:
                continue
            if box["width"] > 60 or box["height"] > 60:
                continue
            candidates.append({"idx": i, "loc": btn, "box": box})
        except Exception:
            pass
    candidates.sort(key=lambda c: c["box"]["x"])
    print(f"模式按钮: {len(candidates)} 个")
    for k, c in enumerate(candidates):
        b = c["box"]
        print(f"  [{k}] pos=({b['x']:.0f},{b['y']:.0f})")
    if len(candidates) < 3:
        raise RuntimeError("按钮不足 3 个")
    return {
        "移动": candidates[0],
        "旋转": candidates[1],
        "缩放": candidates[2],
    }


def get_button_state(btn_info):
    """读取按钮的状态（class、是否选中）"""
    try:
        cls = btn_info["loc"].get_attribute("class") or ""
        return cls
    except Exception:
        return ""


def click_and_check(page, btn_info, label=""):
    """点击按钮，检查 class 变化"""
    cls_before = get_button_state(btn_info)
    print(f"\n  点击「{label}」")
    print(f"    点击前 class: {cls_before[:80]}")

    box = btn_info["box"]
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    try:
        btn_info["loc"].click(timeout=3000)
    except Exception:
        page.mouse.click(cx, cy)
    time.sleep(1)

    cls_after = get_button_state(btn_info)
    print(f"    点击后 class: {cls_after[:80]}")

    return cls_before, cls_after


# ============ 读参数面板 ============
def read_all_axis_inputs(page):
    loc = page.locator("input.inspector-axis-value")
    cnt = loc.count()
    items = []
    for i in range(cnt):
        el = loc.nth(i)
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box:
                continue
            items.append({"y": box["y"], "value": el.input_value() or ""})
        except Exception:
            pass
    items.sort(key=lambda d: d["y"])
    return {
        "position": [it["value"] for it in items[0:3]],
        "rotation": [it["value"] for it in items[3:6]],
        "scale":    [it["value"] for it in items[6:9]],
    }


# ============ 主流程 ============
def test_tc0009_mode_switch():
    print("=== TC-0009（务实版）：3D 导演台 - 变换模式切换验证 ===")
    print("说明：3D gizmo 拖拽因技术限制无法跨电脑自动化，本脚本只验证模式切换。\n")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪，请先启动帧境")

    pw, browser, page = connect()

    try:
        before = page.locator(".react-flow__node").count()
        dblclick_canvas(page)
        click_menu_item(page, "3D 导演台")
        wait_for_new_node(page, before, timeout=30)
        dblclick_3d_node(page)
        click_role_01(page)
        shot(page, "tc0009_role_panel.png")

        mode_btns = find_mode_buttons(page)

        print("\n=== 初始参数 ===")
        init_params = read_all_axis_inputs(page)
        print(f"  位置: {init_params['position']}")
        print(f"  旋转: {init_params['rotation']}")
        print(f"  缩放: {init_params['scale']}")

        # 记录每个按钮的初始 class
        print("\n=== 记录按钮初始状态 ===")
        states = {}
        for name in ["移动", "旋转", "缩放"]:
            cls = get_button_state(mode_btns[name])
            states[name] = cls
            print(f"  {name}: class = {cls[:80]}")

        # ============ 测试 1：点击「移动」 ============
        print("\n\n########## 测试 1：点击「移动」 ##########")
        before_cls, after_cls = click_and_check(page, mode_btns["移动"], "移动")
        shot(page, "tc0009_after_click_move.png")
        move_active = after_cls != before_cls
        print(f"  → class 变化: {move_active}")

        # 切到移动模式后读参数
        params_after_move = read_all_axis_inputs(page)
        print(f"  位置: {params_after_move['position']}")

        # ============ 测试 2：点击「旋转」 ============
        print("\n\n########## 测试 2：点击「旋转」 ##########")
        before_cls2, after_cls2 = click_and_check(page, mode_btns["旋转"], "旋转")
        shot(page, "tc0009_after_click_rotate.png")
        rotate_active = after_cls2 != before_cls2
        print(f"  → class 变化: {rotate_active}")

        # 切到旋转模式后读参数（应保留之前的值）
        params_after_rotate = read_all_axis_inputs(page)
        print(f"  位置: {params_after_rotate['position']}")
        print(f"  旋转: {params_after_rotate['rotation']}")

        pos_preserved_after_rotate = params_after_rotate["position"] == params_after_move["position"]
        print(f"  → 位置参数保留: {pos_preserved_after_rotate}")

        # ============ 测试 3：点击「缩放」 ============
        print("\n\n########## 测试 3：点击「缩放」 ##########")
        before_cls3, after_cls3 = click_and_check(page, mode_btns["缩放"], "缩放")
        shot(page, "tc0009_after_click_scale.png")
        scale_active = after_cls3 != before_cls3
        print(f"  → class 变化: {scale_active}")

        params_after_scale = read_all_axis_inputs(page)
        print(f"  位置: {params_after_scale['position']}")
        print(f"  旋转: {params_after_scale['rotation']}")
        print(f"  缩放: {params_after_scale['scale']}")

        pos_preserved_after_scale = params_after_scale["position"] == params_after_rotate["position"]
        rot_preserved_after_scale = params_after_scale["rotation"] == params_after_rotate["rotation"]
        print(f"  → 位置参数保留: {pos_preserved_after_scale}")
        print(f"  → 旋转参数保留: {rot_preserved_after_scale}")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        if not move_active:
            errors.append("点击「移动」按钮后，按钮状态没有变化")
        if not rotate_active:
            errors.append("点击「旋转」按钮后，按钮状态没有变化")
        if not scale_active:
            errors.append("点击「缩放」按钮后，按钮状态没有变化")
        if not pos_preserved_after_rotate:
            errors.append("切到旋转模式后，位置参数丢失")
        if not pos_preserved_after_scale:
            errors.append("切到缩放模式后，位置参数丢失")
        if not rot_preserved_after_scale:
            errors.append("切到缩放模式后，旋转参数丢失")

        print(f"  三个按钮都能切换: {move_active and rotate_active and scale_active}")
        print(f"  切旋转后位置保留: {pos_preserved_after_rotate}")
        print(f"  切缩放后位置保留: {pos_preserved_after_scale}")
        print(f"  切缩放后旋转保留: {rot_preserved_after_scale}")

        if errors:
            print(f"\n[FAIL] {len(errors)} 项失败:")
            for e in errors:
                print(f"  - {e}")
            raise AssertionError("TC-0009（自动化部分）未通过")

        print("\n[PASS] TC-0009（自动化部分）通过")

        print("\n" + "=" * 60)
        print("【重要】以下内容需人工验证：")
        print("  1. 鼠标按住 gizmo 轴拖拽，角色跟随移动")
        print("  2. 拖拽时右侧参数实时更新")
        print("  3. 三个模式分别拖拽后，对应参数正确改变")
        print("原因：3D 视口用 Three.js 渲染，gizmo 不是 DOM 元素，")
        print("      且 3D 引擎拒绝 Playwright 合成鼠标事件。")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0009_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0009_mode_switch()