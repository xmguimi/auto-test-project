import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============ 配置区 ============
PORT = 9222
ROOT = Path(__file__).parent

# 测试素材：图片 + 视频
_ABS_IMG = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群.jpg")
_REL_IMG = ROOT / "testdata" / "羊群.jpg"
IMAGE_PATH = _ABS_IMG if _ABS_IMG.exists() else _REL_IMG

_ABS_VIDEO = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群奔跑.mp4")
_REL_VIDEO = ROOT / "testdata" / "羊群奔跑.mp4"
VIDEO_PATH = _ABS_VIDEO if _ABS_VIDEO.exists() else _REL_VIDEO

# 帧境.exe 常见候选路径
EXE_CANDIDATES = [
    r"F:\zhenjing\framerealm-canvas\帧境.exe",
    r"C:\Program Files\帧境AI\帧境.exe",
    r"C:\Program Files (x86)\帧境AI\帧境.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\帧境AI\帧境.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\framerealm-canvas\帧境.exe"),
]

# 整体拖拽的偏移量（相对像素）
DRAG_OFFSET_X = 300
DRAG_OFFSET_Y = 200

# 截图输出目录
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    """统一截图保存"""
    path = SHOT_DIR / name
    try:
        page.screenshot(path=str(path))
        print(f"[SHOT] {path}")
    except Exception as e:
        print(f"[SHOT-FAIL] {name}: {e}")
    return path


def print_selected_info(page, label=""):
    """诊断用：打印当前选中节点的数量和中心坐标"""
    sel = page.locator(".react-flow__node.selected")
    n = sel.count()
    print(f"  [诊断-{label}] 选中数: {n}")
    for i in range(n):
        box = sel.nth(i).bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            print(f"    [{i}] 中心: ({cx:.1f},{cy:.1f}) size=({box['width']:.1f}x{box['height']:.1f})")


# ============ 工具函数 ============
def find_exe():
    """查找帧境.exe 路径"""
    env_path = os.environ.get("FRAME_REALM_EXE")
    if env_path and os.path.exists(env_path):
        return env_path

    for p in EXE_CANDIDATES:
        if p and os.path.exists(p):
            return p

    raise FileNotFoundError(
        "找不到 帧境.exe。请设置环境变量 FRAME_REALM_EXE，"
        "或把路径加到 EXE_CANDIDATES 列表里。"
    )


def is_cdp_ready(port=PORT):
    """检查 CDP 端口是否已经开放"""
    try:
        r = requests.get(f"http://localhost:{port}/json/version", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def ensure_app_running(exe_path, port=PORT):
    """检查帧境AI是否已带调试端口启动；没启动就提示用户手动启动"""
    if is_cdp_ready(port):
        print(f"[OK] 帧境AI 已在运行，CDP 端口 {port} 可用")
        return

    raise RuntimeError(
        f"检测不到帧境AI 的 CDP 端口 {port}。\n"
        f"请先手动启动帧境AI：\n"
        f'  & "{exe_path}" --remote-debugging-port={port}\n'
        f"然后手动进入画布编辑页面，再重新运行本脚本。"
    )


def connect_to_frame_realm():
    """连接到已经通过 CDP 启动的帧境 AI"""
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


# ============ 核心动作 ============
def upload_image(page, image_path: Path):
    """上传图片，生成图片节点"""
    print("\n=== 上传图片 ===")

    file_inputs = page.locator("input[type='file']")
    count = file_inputs.count()
    print(f"input[type='file'] 数量: {count}")

    if count == 0:
        raise RuntimeError("没找到 file input")

    nodes_before = page.locator(".react-flow__node").count()
    print(f"上传前节点数: {nodes_before}")

    target = None
    for i in range(count):
        el = file_inputs.nth(i)
        accept = el.get_attribute("accept") or ""
        if "image" in accept:
            target = el
            break
    if target is None:
        target = file_inputs.first

    target.set_input_files(str(image_path))
    print(f"已上传: {image_path}")

    for _ in range(15):
        if page.locator(".react-flow__node").count() > nodes_before:
            print("[OK] 图片节点已生成")
            break
        time.sleep(1)
    time.sleep(1)
    shot(page, "tc0004_after_upload_image.png")


def upload_video(page, video_path: Path):
    """上传视频，生成视频节点"""
    print("\n=== 上传视频 ===")

    file_inputs = page.locator("input[type='file']")
    count = file_inputs.count()

    nodes_before = page.locator(".react-flow__node").count()
    print(f"上传前节点数: {nodes_before}")

    target = None
    for i in range(count):
        el = file_inputs.nth(i)
        accept = el.get_attribute("accept") or ""
        print(f"  [{i}] accept={accept}")
        if "video" in accept:
            target = el
            break
    if target is None:
        target = file_inputs.nth(2) if count > 2 else file_inputs.first

    target.set_input_files(str(video_path))
    print(f"已上传: {video_path}")

    for _ in range(20):
        if page.locator(".react-flow__node").count() > nodes_before:
            print("[OK] 视频节点已生成")
            break
        time.sleep(1)
    time.sleep(2)
    shot(page, "tc0004_after_upload_video.png")


def get_all_nodes(page):
    """获取所有节点的信息"""
    nodes = page.locator(".react-flow__node")
    count = nodes.count()
    print(f"\n=== 当前节点总数: {count} ===")

    result = []
    for i in range(count):
        node = nodes.nth(i)
        box = node.bounding_box()
        if box:
            result.append({
                "index": i,
                "locator": node,
                "box": box,
            })
            print(f"  [{i}] x={box['x']:.1f} y={box['y']:.1f} w={box['width']:.1f} h={box['height']:.1f}")
    return result


def ensure_two_nodes_non_overlap(page, nodes):
    """确保两个节点不重叠，如重叠则拖开"""
    print("\n=== 检查节点分布 ===")

    if len(nodes) < 2:
        raise RuntimeError(f"节点数不足 2 个，当前 {len(nodes)} 个")

    n1 = nodes[-2]
    n2 = nodes[-1]
    b1 = n1["box"]
    b2 = n2["box"]

    overlap_x = not (b1["x"] + b1["width"] < b2["x"] or b2["x"] + b2["width"] < b1["x"])
    overlap_y = not (b1["y"] + b1["height"] < b2["y"] or b2["y"] + b2["height"] < b1["y"])
    is_overlap = overlap_x and overlap_y

    if is_overlap:
        print("[WARN] 两个节点重叠，尝试拖开...")
        node = n2["locator"]
        cx = b2["x"] + b2["width"] / 2
        cy = b2["y"] + b2["height"] / 2
        page.mouse.move(cx, cy)
        time.sleep(0.2)
        page.mouse.down()
        time.sleep(0.3)
        page.mouse.move(cx + 5, cy + 5, steps=3)
        time.sleep(0.2)
        page.mouse.move(cx + 400, cy + 100, steps=20)
        time.sleep(0.2)
        page.mouse.up()
        time.sleep(1)
        shot(page, "tc0004_after_separate.png")
        print("[OK] 已拖开")
    else:
        print("[OK] 节点不重叠")

    return get_all_nodes(page)


def ctrl_select_two_nodes(page, nodes):
    """
    Ctrl 多选两个节点。
    每一步都有诊断打印，能看到「点完之后选中的是谁」。
    依次尝试 Ctrl / Shift / Alt 三种修饰键，以及 JS 强制派发、Ctrl+A 全选。
    """
    print("\n=== Ctrl 多选两个节点（含诊断） ===")

    if len(nodes) < 2:
        raise RuntimeError("节点数不足 2 个")

    n1 = nodes[-2]["locator"]
    n2 = nodes[-1]["locator"]

    b1 = n1.bounding_box()
    b2 = n2.bounding_box()
    if not b1 or not b2:
        raise RuntimeError("节点 bounding_box 获取失败")

    c1x = b1["x"] + b1["width"] / 2
    c1y = b1["y"] + b1["height"] / 2
    c2x = b2["x"] + b2["width"] / 2
    c2y = b2["y"] + b2["height"] / 2

    print(f"节点1 中心: ({c1x:.1f},{c1y:.1f})")
    print(f"节点2 中心: ({c2x:.1f},{c2y:.1f})")

    def clear_selection():
        page.mouse.click(50, 50)
        time.sleep(0.5)

    # ---------- 方案1：Ctrl，用 mouse 手动分步 ----------
    print("\n[方案1] Ctrl：mouse 手动分步")
    clear_selection()
    print_selected_info(page, "清空后")

    page.mouse.click(c1x, c1y)
    time.sleep(0.5)
    print_selected_info(page, "点节点1后")

    page.mouse.move(c2x, c2y)
    time.sleep(0.2)
    page.keyboard.down("Control")
    time.sleep(0.2)
    page.mouse.down()
    time.sleep(0.1)
    page.mouse.up()
    time.sleep(0.2)
    page.keyboard.up("Control")
    time.sleep(0.6)
    print_selected_info(page, "Ctrl 点节点2后")
    shot(page, "tc0004_after_ctrl_select.png")

    sel = page.locator(".react-flow__node.selected").count()
    if sel >= 2:
        print("[OK] 方案1成功")
        return sel

    # ---------- 方案2：Locator.click(modifiers=["Control"]) ----------
    print("\n[方案2] Locator.click(modifiers=[Control])")
    clear_selection()
    print_selected_info(page, "清空后")

    page.mouse.click(c1x, c1y)
    time.sleep(0.5)
    print_selected_info(page, "点节点1后")

    try:
        n2.click(modifiers=["Control"])
    except Exception as e:
        print(f"  n2.click 失败: {e}")
    time.sleep(0.6)
    print_selected_info(page, "Ctrl 点节点2后")
    shot(page, "tc0004_after_ctrl_select2.png")

    sel = page.locator(".react-flow__node.selected").count()
    if sel >= 2:
        print("[OK] 方案2成功")
        return sel

    # ---------- 方案3：JS 派发带 ctrlKey 的事件 ----------
    print("\n[方案3] JS 派发 ctrlKey 事件")
    clear_selection()
    print_selected_info(page, "清空后")

    page.mouse.click(c1x, c1y)
    time.sleep(0.5)
    print_selected_info(page, "点节点1后")

    result = page.evaluate(f"""
        () => {{
            const el = document.elementFromPoint({c2x}, {c2y});
            if (!el) return 'no element at point';
            const opts = {{
                bubbles: true, cancelable: true, ctrlKey: true,
                clientX: {c2x}, clientY: {c2y}, button: 0, buttons: 1
            }};
            el.dispatchEvent(new MouseEvent('mousedown', opts));
            el.dispatchEvent(new MouseEvent('mouseup', opts));
            el.dispatchEvent(new MouseEvent('click', opts));
            return 'dispatched on ' + el.tagName;
        }}
    """)
    print(f"  JS 返回: {result}")
    time.sleep(0.6)
    print_selected_info(page, "JS Ctrl 点节点2后")
    shot(page, "tc0004_after_js_ctrl.png")

    sel = page.locator(".react-flow__node.selected").count()
    if sel >= 2:
        print("[OK] 方案3成功")
        return sel

    # ---------- 方案4：Ctrl+A 全选 ----------
    print("\n[方案4] Ctrl+A 全选")
    clear_selection()
    print_selected_info(page, "清空后")

    page.keyboard.press("Control+A")
    time.sleep(0.6)
    print_selected_info(page, "Ctrl+A 后")
    shot(page, "tc0004_after_ctrl_a.png")

    sel = page.locator(".react-flow__node.selected").count()
    if sel >= 2:
        print("[OK] 方案4成功")
        return sel

    # ---------- 方案5：Shift 点击 ----------
    print("\n[方案5] Shift 点击节点2")
    clear_selection()
    print_selected_info(page, "清空后")

    page.mouse.click(c1x, c1y)
    time.sleep(0.5)
    print_selected_info(page, "点节点1后")

    page.mouse.move(c2x, c2y)
    time.sleep(0.2)
    page.keyboard.down("Shift")
    time.sleep(0.2)
    page.mouse.down()
    time.sleep(0.1)
    page.mouse.up()
    time.sleep(0.2)
    page.keyboard.up("Shift")
    time.sleep(0.6)
    print_selected_info(page, "Shift 点节点2后")
    shot(page, "tc0004_after_shift_select.png")

    sel = page.locator(".react-flow__node.selected").count()
    if sel >= 2:
        print("[OK] 方案5成功")
        return sel

    print("\n[WARN] 五种方案都没选中 2 个节点")
    return sel


def drag_group_by_click(page, nodes, offset_x, offset_y):
    """点击其中一个选中节点，整体拖拽"""
    print("\n=== 整体拖拽 ===")

    selected_nodes = page.locator(".react-flow__node.selected")
    selected_count = selected_nodes.count()
    print(f"选中的节点数: {selected_count}")

    if selected_count < 2:
        raise RuntimeError(
            f"选中节点数不足 2 个（实际 {selected_count}），无法整体拖拽"
        )

    before = []
    for i in range(selected_count):
        box = selected_nodes.nth(i).bounding_box()
        before.append(box)
        print(f"  拖拽前 [{i}] x={box['x']:.1f} y={box['y']:.1f}")

    first = before[0]
    start_x = first["x"] + first["width"] / 2
    start_y = first["y"] + first["height"] / 2
    print(f"拖拽起点: ({start_x:.1f},{start_y:.1f})")

    page.mouse.move(start_x, start_y)
    time.sleep(0.2)
    page.mouse.down()
    time.sleep(0.3)
    page.mouse.move(start_x + 5, start_y + 5, steps=3)
    time.sleep(0.2)
    page.mouse.move(start_x + 15, start_y + 15, steps=3)
    time.sleep(0.2)

    end_x = start_x + offset_x
    end_y = start_y + offset_y
    page.mouse.move(end_x, end_y, steps=25)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1)

    shot(page, "tc0004_after_drag.png")

    after = []
    for i in range(selected_count):
        box = selected_nodes.nth(i).bounding_box()
        after.append(box)
        print(f"  拖拽后 [{i}] x={box['x']:.1f} y={box['y']:.1f}")

    return before, after, selected_count


def assert_multi_drag(before, after, offset_x, offset_y,
                      selected_before, selected_after):
    """断言批量拖拽结果"""
    print("\n=== 断言批量拖拽结果 ===")

    for i, (b, a) in enumerate(zip(before, after)):
        dx = a["x"] - b["x"]
        dy = a["y"] - b["y"]
        print(f"  节点 [{i}] 位移: dx={dx:.1f}, dy={dy:.1f}")
        assert abs(dx) > 50 or abs(dy) > 50, (
            f"节点 [{i}] 未移动或移动过小：dx={dx}, dy={dy}"
        )

    tol = max(80, abs(offset_x) * 0.3)
    for i, (b, a) in enumerate(zip(before, after)):
        dx = a["x"] - b["x"]
        dy = a["y"] - b["y"]
        assert abs(dx - offset_x) < tol, (
            f"节点 [{i}] X 偏移异常: dx={dx}, 预期 {offset_x}"
        )
        assert abs(dy - offset_y) < tol, (
            f"节点 [{i}] Y 偏移异常: dy={dy}, 预期 {offset_y}"
        )

    if len(before) >= 2:
        print("\n  检查相对位置...")
        for i in range(1, len(before)):
            rel_bx = before[i]["x"] - before[0]["x"]
            rel_by = before[i]["y"] - before[0]["y"]
            rel_ax = after[i]["x"] - after[0]["x"]
            rel_ay = after[i]["y"] - after[0]["y"]
            diff_x = abs(rel_bx - rel_ax)
            diff_y = abs(rel_by - rel_ay)
            print(f"  节点 [{i}] 相对位置变化: ({diff_x:.1f},{diff_y:.1f})")
            assert diff_x < 5 and diff_y < 5, (
                f"节点 [{i}] 相对位置错乱"
            )

    print(f"\n  拖拽前选中数: {selected_before}，拖拽后选中数: {selected_after}")
    assert selected_after >= selected_before, (
        f"拖拽后选中状态丢失"
    )

    print("\n[PASS] 批量拖拽断言通过")


# ============ 测试主流程 ============
def test_drag_multi_nodes():
    """TC-0004"""

    if not IMAGE_PATH.exists():
        print(f"[ERROR] 找不到测试图片: {IMAGE_PATH}")
        sys.exit(1)
    if not VIDEO_PATH.exists():
        print(f"[ERROR] 找不到测试视频: {VIDEO_PATH}")
        sys.exit(1)
    print(f"[OK] 测试图片: {IMAGE_PATH}")
    print(f"[OK] 测试视频: {VIDEO_PATH}")

    exe = find_exe()
    print(f"[OK] 帧境AI 路径: {exe}")
    ensure_app_running(exe)

    pw, browser, page = connect_to_frame_realm()

    try:
        print(f"\n页面 URL: {page.url}")
        shot(page, "tc0004_connected.png")

        upload_image(page, IMAGE_PATH)
        upload_video(page, VIDEO_PATH)

        nodes = get_all_nodes(page)
        nodes = ensure_two_nodes_non_overlap(page, nodes)

        selected_count = ctrl_select_two_nodes(page, nodes)
        print(f"[INFO] 多选后选中节点数: {selected_count}")

        selected_before = page.locator(".react-flow__node.selected").count()
        print(f"拖拽前选中数: {selected_before}")

        before, after, dragged_count = drag_group_by_click(
            page, nodes, DRAG_OFFSET_X, DRAG_OFFSET_Y
        )

        selected_after = page.locator(".react-flow__node.selected").count()
        print(f"拖拽后选中数: {selected_after}")

        assert_multi_drag(
            before, after,
            DRAG_OFFSET_X, DRAG_OFFSET_Y,
            selected_before, selected_after
        )

        print("\n=== TC-0004 测试通过 ===")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0004_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_drag_multi_nodes()