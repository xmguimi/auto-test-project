"""
TC-0010 自动化测试：3D 场景

⚠️  上传全景图：
    1. 点击「导入全景图」→ 弹文件对话框
    2. pygetwindow 拿到对话框窗口位置
    3. pyautogui 按窗口内比例点击文件图标
    4. 点击「打开」按钮
"""

import os
import sys
import time
import requests
import pyautogui
import pygetwindow as gw
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 9222
ROOT = Path(__file__).parent

_ABS_PANO = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\风景全景图.jpg")
_REL_PANO = ROOT / "testdata" / "风景全景图.jpg"
PANO_PATH = _ABS_PANO if _ABS_PANO.exists() else _REL_PANO

TARGET_POSITION = {"X": "5", "Y": "-5", "Z": "5"}
TARGET_ROTATION = {"X": "1", "Y": "-1", "Z": "3"}
TARGET_COLOR_HEX = "#87CEEB"

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

pyautogui.FAILSAFE = False


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


# ============ 进入 3D 导演台 ============
def dblclick_canvas(page):
    print("\n=== 双击画布 ===")
    page.mouse.dblclick(600, 400)
    time.sleep(1.5)


def click_menu_item(page, kw):
    print(f"\n=== 点击菜单 '{kw}' ===")
    for sel in [f".cm-item:has-text('{kw}')", f"li:has-text('{kw}')"]:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible() and el.bounding_box():
                    el.click(timeout=3000)
                    print("  [OK]")
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
    print("\n=== 双击 3D 节点 ===")
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    node = nodes.nth(n - 1)
    box = node.bounding_box()
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.dblclick(cx, cy)
    time.sleep(3.5)
    shot(page, "tc0010_in_director.png")


# ============ 上传全景图 ============
def upload_panorama(page):
    print("\n\n########## 上传全景图 ##########")
    print(f"  目标: {PANO_PATH}")

    if not PANO_PATH.exists():
        print(f"  [ERROR] 文件不存在")
        return False

    # 定位「导入全景图」按钮
    btn = None
    for locator in [
        page.get_by_role("button", name="导入全景图"),
        page.get_by_text("导入全景图", exact=True),
    ]:
        try:
            if locator.count() > 0 and locator.first.is_visible():
                btn = locator.first
                print("  通过 Playwright 定位器找到按钮")
                break
        except Exception:
            pass

    if not btn:
        try:
            btns = page.locator("button")
            for i in range(btns.count()):
                b = btns.nth(i)
                if not b.is_visible():
                    continue
                t = (b.inner_text() or "").strip()
                if "导入全景图" in t:
                    btn = b
                    print("  兜底找到按钮")
                    break
        except Exception:
            pass

    if not btn:
        print("  [FAIL] 找不到按钮")
        return False

    # 激活帧境窗口
    try:
        wins = gw.getWindowsWithTitle("帧境")
        if wins:
            wins[0].activate()
            time.sleep(0.5)
    except Exception:
        pass

    # 点击按钮，弹文件对话框
    try:
        btn.click(timeout=3000)
        print("  [OK] 已点击「导入全景图」")
    except Exception as e:
        print(f"  点击失败: {e}")
        return False

    time.sleep(3)
    shot(page, "tc0010_after_click_pano_btn.png")

    # ★ 找到文件对话框窗口
    print("\n  [pyautogui] 查找文件对话框窗口")
    dialog = None
    for title_kw in ["打开", "Open", "选择", "浏览"]:
        try:
            wins = gw.getWindowsWithTitle(title_kw)
            for w in wins:
                if w.width > 400 and w.height > 300:
                    dialog = w
                    print(f"  找到窗口: title='{w.title}' rect=({w.left},{w.top},{w.width}x{w.height})")
                    break
            if dialog:
                break
        except Exception:
            pass

    if not dialog:
        # 列出所有窗口，帮助调试
        print("  [WARN] 没找到标题含「打开」的窗口，列出所有窗口：")
        try:
            for w in gw.getAllWindows():
                if w.visible and w.width > 300 and w.height > 200:
                    print(f"    '{w.title}' rect=({w.left},{w.top},{w.width}x{w.height})")
        except Exception:
            pass
        print("  [FAIL] 找不到文件对话框")
        return False

    try:
        dialog.activate()
    except Exception:
        pass
    time.sleep(1)

    # ★ 点击文件图标
    # 从截图看，文件图标在对话框的左上区域
    # 设图标网格第 1 行第 2 个（风景全景图.jpg 是第 2 个）
    # 相对对话框：x ≈ 490, y ≈ 200（对话框约 1127x723）
    # 用比例：x_ratio ≈ 0.435, y_ratio ≈ 0.28
    file_x = dialog.left + int(dialog.width * 0.435)
    file_y = dialog.top + int(dialog.height * 0.28)

    print(f"  [点击文件图标] ({file_x},{file_y})")
    pyautogui.click(file_x, file_y)
    time.sleep(0.8)
    shot(page, "tc0010_after_click_file.png")

    # ★ 点击「打开」按钮（右下角）
    # 相对对话框：右下角附近
    # x ≈ 850, y ≈ 680（对话框约 1127x723）
    # 比例：x_ratio ≈ 0.755, y_ratio ≈ 0.94
    open_x = dialog.left + int(dialog.width * 0.755)
    open_y = dialog.top + int(dialog.height * 0.94)

    print(f"  [点击「打开」] ({open_x},{open_y})")
    pyautogui.click(open_x, open_y)
    time.sleep(3)
    shot(page, "tc0010_after_upload_pano.png")

    # 验证
    cnt = page.get_by_text("未连接全景图", exact=False).count()
    print(f"  上传后「未连接全景图」出现次数: {cnt}")
    if cnt == 0:
        print("  [OK] 全景图上传成功")
        return True
    else:
        print("  [WARN] 「未连接全景图」仍存在")
        return False


# ============ 场景输入框 ============
def get_scene_inputs(page):
    inputs = page.locator("input.inspector-axis-value")
    cnt = inputs.count()
    print(f"  inspector-axis-value 总数: {cnt}")
    if cnt < 6:
        raise RuntimeError("输入框不足 6 个")
    position = [inputs.nth(i) for i in range(3)]
    rotation = [inputs.nth(i) for i in range(3, 6)]
    for i in range(6):
        try:
            print(f"    [{i}] value='{inputs.nth(i).input_value()}'")
        except Exception:
            pass
    return {"position": position, "rotation": rotation}


def set_input_via_keyboard(page, input_locator, new_value):
    try:
        input_locator.scroll_into_view_if_needed()
        time.sleep(0.2)
        input_locator.click()
        time.sleep(0.3)
        print(f"    点击后当前值: '{input_locator.input_value()}'")
        page.keyboard.press("Control+A")
        time.sleep(0.15)
        page.keyboard.press("Delete")
        time.sleep(0.15)
        print(f"    删除后当前值: '{input_locator.input_value()}'")
        for ch in new_value:
            page.keyboard.type(ch, delay=60)
        time.sleep(0.3)
        final_val = input_locator.input_value()
        print(f"    输入 '{new_value}' 后: '{final_val}'")
        return final_val
    except Exception as e:
        print(f"    输入失败: {e}")
        return None


def get_all_sliders(page):
    sliders = page.locator("input[type='range'].inspector-range")
    cnt = sliders.count()
    print(f"  滑杆总数: {cnt}")
    result = []
    for i in range(cnt):
        el = sliders.nth(i)
        try:
            if not el.is_visible():
                continue
            print(f"    slider[{i}] value='{el.input_value()}'")
            result.append(el)
        except Exception:
            pass
    return result


def set_slider_via_keyboard(page, slider, times=5):
    try:
        slider.scroll_into_view_if_needed()
        time.sleep(0.2)
        slider.click()
        time.sleep(0.2)
        for _ in range(times):
            page.keyboard.press("ArrowRight")
            time.sleep(0.05)
        time.sleep(0.2)
        return slider.input_value()
    except Exception as e:
        print(f"    滑杆失败: {e}")
        return None


# ============ 网格吸附 ============
def toggle_grid_snap(page):
    print("\n\n########## 打开网格吸附 ##########")
    try:
        cb = page.get_by_role("checkbox", name="网格吸附")
        if cb.count() > 0:
            el = cb.first
            if el.is_visible():
                state_before = el.is_checked()
                print(f"  当前: {state_before}")
                if not state_before:
                    el.click(timeout=3000)
                    time.sleep(0.5)
                state_after = el.is_checked()
                print(f"  点击后: {state_after}")
                return state_after
    except Exception as e:
        print(f"  role 失败: {e}")

    try:
        cb = page.locator("label:has-text('网格吸附') input[type='checkbox']")
        if cb.count() > 0:
            el = cb.first
            state_before = el.is_checked()
            if not state_before:
                el.click(timeout=3000)
                time.sleep(0.5)
            return el.is_checked()
    except Exception:
        pass
    return False


# ============ 天空颜色 ============
def get_color_hex_input(page):
    try:
        loc = page.locator("input.inspector-color-hex")
        if loc.count() > 0:
            return loc.first
    except Exception:
        pass
    return None


def set_hex_via_keyboard(page, hex_input, hex_value):
    try:
        hex_input.scroll_into_view_if_needed()
        time.sleep(0.2)
        hex_input.click()
        time.sleep(0.3)
        page.keyboard.press("Control+A")
        time.sleep(0.15)
        page.keyboard.press("Delete")
        time.sleep(0.15)
        for ch in hex_value:
            page.keyboard.type(ch, delay=40)
        time.sleep(0.4)
        return True
    except Exception as e:
        print(f"    颜色失败: {e}")
        return False


# ============ 主流程 ============
def test_tc0010():
    print("=== TC-0010：3D 场景 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        before = page.locator(".react-flow__node").count()
        dblclick_canvas(page)
        click_menu_item(page, "3D 导演台")
        wait_for_new_node(page, before, timeout=30)

        dblclick_3d_node(page)

        pano_ok = upload_panorama(page)

        print("\n=== 初始参数 ===")
        scene_inputs = get_scene_inputs(page)

        print("\n\n########## 场景平移 XYZ ##########")
        for i, axis in enumerate(["X", "Y", "Z"]):
            v = TARGET_POSITION[axis]
            print(f"\n  位置 {axis} = {v}")
            set_input_via_keyboard(page, scene_inputs["position"][i], v)
        shot(page, "tc0010_after_position.png")

        print("\n\n########## 场景旋转 XYZ ##########")
        for i, axis in enumerate(["X", "Y", "Z"]):
            v = TARGET_ROTATION[axis]
            print(f"\n  旋转 {axis} = {v}")
            set_input_via_keyboard(page, scene_inputs["rotation"][i], v)
        shot(page, "tc0010_after_rotation.png")

        print("\n\n########## 天空颜色 ##########")
        hex_input = get_color_hex_input(page)
        if hex_input:
            try:
                print(f"  当前: {hex_input.input_value()}")
            except Exception:
                pass
            set_hex_via_keyboard(page, hex_input, TARGET_COLOR_HEX)
            try:
                print(f"  设置后: {hex_input.input_value()}")
            except Exception:
                pass
        shot(page, "tc0010_after_color.png")

        print("\n\n########## 滑杆操作 ##########")
        sliders = get_all_sliders(page)
        slider_results = []
        for i, slider in enumerate(sliders):
            try:
                v_before = slider.input_value()
                print(f"\n  滑杆[{i}] 当前: {v_before}")
                v_after = set_slider_via_keyboard(page, slider, times=10)
                print(f"    调整后: {v_after}")
                slider_results.append((i, v_before, v_after))
            except Exception as e:
                print(f"    失败: {e}")
        shot(page, "tc0010_after_sliders.png")

        grid_ok = toggle_grid_snap(page)
        shot(page, "tc0010_after_grid.png")

        print("\n\n=== 最终参数 ===")
        final_inputs = page.locator("input.inspector-axis-value")
        final_pos = [final_inputs.nth(i).input_value() for i in range(3)]
        final_rot = [final_inputs.nth(i).input_value() for i in range(3, 6)]
        print(f"  场景位置: {final_pos}")
        print(f"  场景旋转: {final_rot}")

        print("\n\n=== 断言 ===")
        errors = []
        bug_hits = []

        if not pano_ok:
            errors.append("全景图上传失败")
        if not grid_ok:
            errors.append("网格吸附未打开")

        exp_pos = [TARGET_POSITION["X"], TARGET_POSITION["Y"], TARGET_POSITION["Z"]]
        exp_rot = [TARGET_ROTATION["X"], TARGET_ROTATION["Y"], TARGET_ROTATION["Z"]]

        print(f"  场景位置: 期望 {exp_pos}, 实际 {final_pos}")
        print(f"  场景旋转: 期望 {exp_rot}, 实际 {final_rot}")

        if final_pos != exp_pos:
            errors.append(f"场景位置错误")
            bug_hits.append("输入框 0 顶不掉 / 负数输不进")
        if final_rot != exp_rot:
            errors.append(f"场景旋转错误")

        print(f"  滑杆未变: {[i for i, b, a in slider_results if b == a]}")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0010，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            if bug_hits:
                print("\n【BUG 复现】：")
                for b in set(bug_hits):
                    print(f"  - {b}")
            print("=" * 60)
            raise AssertionError("TC-0010 未通过")
        else:
            print("[PASS] TC-0010 通过")
            print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0010_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0010()