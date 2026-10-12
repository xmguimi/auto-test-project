import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============ 配置区 ============
PORT = 9222
ROOT = Path(__file__).parent

EXE_CANDIDATES = [
    r"F:\zhenjing\framerealm-canvas\帧境.exe",
    r"C:\Program Files\帧境AI\帧境.exe",
    r"C:\Program Files (x86)\帧境AI\帧境.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\帧境AI\帧境.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\framerealm-canvas\帧境.exe"),
]

# 期望参数（用例中定义）
TARGET_POSITION = {"X": "5", "Y": "-5"}   # Z 保持不变
TARGET_ROTATION = {"X": "0.5", "Y": "1.5", "Z": "-0.5"}
TARGET_SCALE    = {"X": "0.8", "Y": "0.9", "Z": "1.1"}

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    path = SHOT_DIR / name
    try:
        page.screenshot(path=str(path))
        print(f"[SHOT] {path}")
    except Exception as e:
        print(f"[SHOT-FAIL] {name}: {e}")
    return path


# ============ 工具函数 ============
def find_exe():
    env_path = os.environ.get("FRAME_REALM_EXE")
    if env_path and os.path.exists(env_path):
        return env_path
    for p in EXE_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise FileNotFoundError("找不到 帧境.exe")


def is_cdp_ready(port=PORT):
    try:
        r = requests.get(f"http://localhost:{port}/json/version", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def ensure_app_running(exe_path, port=PORT):
    if is_cdp_ready(port):
        print(f"[OK] 帧境AI 已在运行，CDP 端口 {port} 可用")
        return
    raise RuntimeError(
        f"检测不到帧境AI 的 CDP 端口 {port}。\n"
        f"请先手动启动：\n"
        f'  & "{exe_path}" --remote-debugging-port={port}\n'
        f"然后手动进入画布编辑页面，再重新运行本脚本。"
    )


def connect_to_frame_realm():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")
    context = browser.contexts[0]
    pages = context.pages

    print(f"\n找到 {len(pages)} 个页面：")
    for i, page in enumerate(pages):
        print(f"  [{i}] 标题: {page.title()}")

    canvas_page = None
    for page in pages:
        title = page.title() or ""
        if "帧境" in title or "Frame" in title or "画布" in title:
            canvas_page = page
            break
    if not canvas_page:
        canvas_page = pages[0]

    print(f"\n当前操作页面：{canvas_page.title()}")
    return pw, browser, canvas_page


# ============ 添加 3D 导演台节点 ============
def dblclick_canvas(page, x=600, y=400):
    print(f"\n=== 双击画布 ({x},{y}) ===")
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, "tc0008_after_dblclick_canvas.png")


def click_menu_item(page, text_keyword):
    print(f"\n=== 点击菜单项：'{text_keyword}' ===")
    candidates = [
        f".cm-item:has-text('{text_keyword}')",
        f"[role='menuitem']:has-text('{text_keyword}')",
        f"[class*='menu-item']:has-text('{text_keyword}')",
        f"li:has-text('{text_keyword}')",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            for i in range(loc.count()):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                    if not el.bounding_box():
                        continue
                    el.click(timeout=3000)
                    print(f"  [OK] 已点击 '{text_keyword}'")
                    return True
                except Exception:
                    pass
        except Exception:
            pass
    raise RuntimeError(f"找不到菜单项 '{text_keyword}'")


def wait_for_new_node(page, nodes_before, timeout=30):
    print(f"\n=== 等待新节点 ===")
    start = time.time()
    while time.time() - start < timeout:
        cur = page.locator(".react-flow__node").count()
        if cur > nodes_before:
            print(f"[OK] 节点数 {nodes_before} -> {cur}")
            return cur
        time.sleep(1)
    raise RuntimeError("新节点未出现")


def dblclick_3d_node(page):
    print("\n=== 双击 3D 节点 ===")
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    if n == 0:
        raise RuntimeError("没有节点")
    node = nodes.nth(n - 1)
    box = node.bounding_box()
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    print(f"3D 节点中心: ({cx:.1f},{cy:.1f})")
    page.mouse.dblclick(cx, cy)
    time.sleep(3.5)
    shot(page, "tc0008_after_dblclick_3d.png")


# ============ 点击左侧「角色01」 ============
def click_role_01(page):
    print("\n=== 点击左侧「角色01」 ===")
    candidates = [
        "li:has-text('角色01')",
        "div[class*='role']:has-text('角色01')",
        "div[class*='item']:has-text('角色01')",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            for i in range(loc.count()):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                    box = el.bounding_box()
                    if not box or box["width"] > 400 or box["height"] > 150:
                        continue
                    el.click(timeout=3000)
                    print(f"  [OK] 已点击「角色01」")
                    time.sleep(2)
                    shot(page, "tc0008_after_click_role01.png")
                    return True
                except Exception:
                    pass
        except Exception:
            pass
    raise RuntimeError("找不到「角色01」")


# ============ 输入框定位 ============
def get_all_axis_inputs(page):
    print("\n=== 获取所有 inspector-axis-value 输入框 ===")
    loc = page.locator("input.inspector-axis-value")
    cnt = loc.count()
    print(f"总数: {cnt}")

    result = []
    for i in range(cnt):
        el = loc.nth(i)
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box:
                continue
            result.append({
                "locator": el,
                "x": box["x"],
                "y": box["y"],
                "value": el.input_value() or "",
            })
        except Exception:
            pass

    result.sort(key=lambda d: d["y"])
    for i, r in enumerate(result):
        print(f"  [{i}] y={r['y']:.0f} value='{r['value']}'")
    return result


def scroll_to_element(page, locator):
    """把元素滚到视口中心"""
    try:
        locator.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        locator.evaluate("""(el) => {
            el.scrollIntoView({ block: 'center', behavior: 'instant' });
        }""")
    except Exception:
        pass
    time.sleep(0.3)


# ============ 模拟真人键盘输入 ============
def set_input_via_keyboard(page, input_locator, new_value: str):
    """
    完全模拟真人：点击 → Ctrl+A 全选 → Delete 删除 → 逐字符键盘输入。
    不用 JS 赋值，确保能复现用户遇到的 bug。
    """
    try:
        scroll_to_element(page, input_locator)
        time.sleep(0.2)

        # 点击输入框（光标落入）
        input_locator.click()
        time.sleep(0.3)

        # 打印点击后输入框的值，观察光标情况
        before_val = input_locator.input_value()
        print(f"    点击后当前值: '{before_val}'")

        # 全选 + 删除
        page.keyboard.press("Control+A")
        time.sleep(0.15)
        page.keyboard.press("Delete")
        time.sleep(0.15)

        after_delete = input_locator.input_value()
        print(f"    删除后当前值: '{after_delete}'")

        # 逐字符输入
        for ch in new_value:
            page.keyboard.type(ch, delay=60)

        time.sleep(0.3)
        final_val = input_locator.input_value()
        print(f"    输入 '{new_value}' 后实际值: '{final_val}'")
        return final_val

    except Exception as e:
        print(f"    输入失败: {e}")
        return None


def read_input_value(input_locator):
    try:
        return (input_locator.input_value() or "").strip()
    except Exception:
        return ""


# ============ 主流程 ============
def test_3d_director_params():
    print("=== TC-0008：3D 导演台参数输入（模拟真人键盘）===")

    exe = find_exe()
    print(f"[OK] 帧境AI 路径: {exe}")
    ensure_app_running(exe)

    pw, browser, page = connect_to_frame_realm()

    try:
        print(f"\n页面 URL: {page.url}")
        shot(page, "tc0008_connected.png")

        nodes_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {nodes_before}")

        # 1. 双击画布 → 3D 导演台
        dblclick_canvas(page, 600, 400)
        click_menu_item(page, "3D 导演台")
        wait_for_new_node(page, nodes_before, timeout=30)
        shot(page, "tc0008_after_add_3d_node.png")

        # 2. 双击 3D 节点
        dblclick_3d_node(page)

        # 3. 点击「角色01」
        click_role_01(page)

        # 4. 取输入框
        inputs = get_all_axis_inputs(page)
        if len(inputs) < 9:
            raise RuntimeError(f"输入框不足 9 个，实际 {len(inputs)}")

        position_inputs = inputs[0:3]
        rotation_inputs = inputs[3:6]
        scale_inputs    = inputs[6:9]

        # 5. 键盘输入
        print(f"\n--- 输入位置 ---")
        set_input_via_keyboard(page, position_inputs[0]["locator"], TARGET_POSITION["X"])
        print(f"  位置 X 期望: {TARGET_POSITION['X']}")
        shot(page, "tc0008_pos_x_set.png")

        set_input_via_keyboard(page, position_inputs[1]["locator"], TARGET_POSITION["Y"])
        print(f"  位置 Y 期望: {TARGET_POSITION['Y']}")
        shot(page, "tc0008_pos_y_set.png")

        print(f"  位置 Z 保持不变（跳过）")

        print(f"\n--- 输入旋转 ---")
        set_input_via_keyboard(page, rotation_inputs[0]["locator"], TARGET_ROTATION["X"])
        set_input_via_keyboard(page, rotation_inputs[1]["locator"], TARGET_ROTATION["Y"])
        set_input_via_keyboard(page, rotation_inputs[2]["locator"], TARGET_ROTATION["Z"])
        shot(page, "tc0008_rotation_set.png")

        print(f"\n--- 输入缩放 ---")
        set_input_via_keyboard(page, scale_inputs[0]["locator"], TARGET_SCALE["X"])
        set_input_via_keyboard(page, scale_inputs[1]["locator"], TARGET_SCALE["Y"])
        set_input_via_keyboard(page, scale_inputs[2]["locator"], TARGET_SCALE["Z"])
        shot(page, "tc0008_scale_set.png")

        time.sleep(1)
        shot(page, "tc0008_after_all_input.png")

        # 6. 断言
        print("\n=== 断言输入结果（用户键盘输入后，值应与期望一致）===")

        actual = {
            "位置 X": read_input_value(position_inputs[0]["locator"]),
            "位置 Y": read_input_value(position_inputs[1]["locator"]),
            "旋转 X": read_input_value(rotation_inputs[0]["locator"]),
            "旋转 Y": read_input_value(rotation_inputs[1]["locator"]),
            "旋转 Z": read_input_value(rotation_inputs[2]["locator"]),
            "缩放 X": read_input_value(scale_inputs[0]["locator"]),
            "缩放 Y": read_input_value(scale_inputs[1]["locator"]),
            "缩放 Z": read_input_value(scale_inputs[2]["locator"]),
        }
        expected = {
            "位置 X": TARGET_POSITION["X"],
            "位置 Y": TARGET_POSITION["Y"],
            "旋转 X": TARGET_ROTATION["X"],
            "旋转 Y": TARGET_ROTATION["Y"],
            "旋转 Z": TARGET_ROTATION["Z"],
            "缩放 X": TARGET_SCALE["X"],
            "缩放 Y": TARGET_SCALE["Y"],
            "缩放 Z": TARGET_SCALE["Z"],
        }

        errors = []
        bug_reproduced = []
        for k in expected:
            exp = expected[k]
            act = actual[k]
            if act == exp:
                print(f"  ✓ {k}: 期望={exp}, 实际={act}")
            else:
                print(f"  ✗ {k}: 期望={exp}, 实际={act}  ← 失败")
                errors.append(f"{k}: 期望 {exp}, 实际 {act}")
                # 判断是否是 0 顶不掉的 bug
                if act.endswith(exp) or (exp.startswith("-") and act == "0" + exp.lstrip("-")):
                    bug_reproduced.append(f"{k}: {exp} → {act}")

        print("\n=== 结果汇总 ===")
        if bug_reproduced:
            print(f"\n[BUG 复现] 共 {len(bug_reproduced)} 项失败，原因疑似「0 顶不掉 / 负号输不进」：")
            for b in bug_reproduced:
                print(f"  - {b}")

        if errors:
            print(f"\n[FAIL] TC-0008 失败，共 {len(errors)} 项参数未正确写入：")
            for e in errors:
                print(f"  - {e}")
            raise AssertionError("参数校验未通过")

        print("\n[PASS] 所有参数键盘输入正确")
        print("\n=== TC-0008 测试通过 ===")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0008_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_3d_director_params()