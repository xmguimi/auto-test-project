import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============ 配置区 ============
PORT = 9222
ROOT = Path(__file__).parent

_ABS_IMG1 = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群.jpg")
_REL_IMG1 = ROOT / "testdata" / "羊群.jpg"
IMAGE1_PATH = _ABS_IMG1 if _ABS_IMG1.exists() else _REL_IMG1

_ABS_IMG2 = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\牛群.jpg")
_REL_IMG2 = ROOT / "testdata" / "牛群.jpg"
IMAGE2_PATH = _ABS_IMG2 if _ABS_IMG2.exists() else _REL_IMG2

EXE_CANDIDATES = [
    r"F:\zhenjing\framerealm-canvas\帧境.exe",
    r"C:\Program Files\帧境AI\帧境.exe",
    r"C:\Program Files (x86)\帧境AI\帧境.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\帧境AI\帧境.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\framerealm-canvas\帧境.exe"),
]

# 节点2 横向右移的目标距离
SEPARATE_OFFSET_X = 700

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


# ============ 上传图片 ============
def upload_image(page, image_path: Path, label: str):
    print(f"\n=== 上传 {label}: {image_path.name} ===")
    file_inputs = page.locator("input[type='file']")
    count = file_inputs.count()
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
            print(f"[OK] {label} 节点已生成")
            break
        time.sleep(1)
    time.sleep(1)
    shot(page, f"tc0007_after_upload_{label}.png")


def get_all_nodes(page):
    nodes = page.locator(".react-flow__node")
    count = nodes.count()
    result = []
    for i in range(count):
        box = nodes.nth(i).bounding_box()
        if box:
            result.append({"index": i, "locator": nodes.nth(i), "box": box})
    print(f"\n=== 当前节点总数: {count} ===")
    for n in result:
        b = n["box"]
        print(f"  [{n['index']}] x={b['x']:.1f} y={b['y']:.1f} w={b['width']:.1f} h={b['height']:.1f}")
    return result


# ============ 横向分离（严格水平，y 不变） ============
def separate_nodes_horizontal(page, nodes):
    """
    把最后一个节点严格横向右移，y 保持不变。
    策略：按下节点右侧 1/4 处（不是中心），避免鼠标起点在中心时容易抖动。
    使用多段 mouse.move 保持 y 完全一致。
    """
    print("\n=== 横向分离节点（严格水平） ===")
    if len(nodes) < 2:
        raise RuntimeError(f"节点不足 2 个，当前 {len(nodes)}")

    n1 = nodes[-2]
    n2 = nodes[-1]
    b1, b2 = n1["box"], n2["box"]

    gap_x = b2["x"] - (b1["x"] + b1["width"])
    overlap_y = not (b1["y"] + b1["height"] < b2["y"] or b2["y"] + b2["height"] < b1["y"])
    too_close = gap_x < 100

    if not (overlap_y and too_close):
        print(f"[OK] 节点已分离（间距 {gap_x:.1f}）")
        return get_all_nodes(page)

    print(f"[WARN] 节点重叠，横向拖开第二个节点")

    # 用节点2 中心偏右 1/4 宽度的位置作为拖拽起点，避免正中心触发其他交互
    start_x = b2["x"] + b2["width"] * 0.75
    start_y = b2["y"] + b2["height"] / 2
    # 目标：同 y，x 往右推 SEPARATE_OFFSET_X
    end_x = start_x + SEPARATE_OFFSET_X
    end_y = start_y  # ★ y 完全不变

    print(f"  起点: ({start_x:.1f},{start_y:.1f})")
    print(f"  终点: ({end_x:.1f},{end_y:.1f})")

    page.mouse.move(start_x, start_y)
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.3)

    # 小步触发阈值（y 严格不变）
    page.mouse.move(start_x + 5, start_y, steps=3)
    time.sleep(0.2)
    page.mouse.move(start_x + 15, start_y, steps=3)
    time.sleep(0.2)

    # 分段横向移动（每段 y 都一样）
    step_count = 10
    for i in range(1, step_count + 1):
        sx = start_x + (end_x - start_x) * i / step_count
        page.mouse.move(sx, start_y, steps=3)
        time.sleep(0.08)

    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1)

    # 立刻把鼠标移开，避免触发 hover
    page.mouse.move(100, 100)
    time.sleep(0.5)

    shot(page, "tc0007_after_separate.png")

    return get_all_nodes(page)


# ============ Handle 定位 ============
def get_handle_center(page, node_locator, side):
    """返回节点内 handle 的中心坐标 (x, y)"""
    handle = node_locator.locator(f".react-flow__handle-{side}")
    cnt = handle.count()
    print(f"  节点内 .react-flow__handle-{side} 数量: {cnt}")
    if cnt == 0:
        raise RuntimeError(f"节点内没找到 handle-{side}")

    box = handle.first.bounding_box()
    if not box:
        raise RuntimeError(f"handle-{side} 没有 bounding_box")

    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    print(f"  handle-{side} 中心: ({cx:.1f},{cy:.1f})")

    top = page.evaluate(f"""
        () => {{
            const el = document.elementFromPoint({cx}, {cy});
            if (!el) return null;
            return {{ tag: el.tagName, cls: String(el.className).slice(0, 80) }};
        }}
    """)
    print(f"  该位置顶层元素: {top}")
    if top and "handle" not in str(top.get("cls", "")):
        print(f"  [WARN] handle 被遮挡！顶层是: {top}")
    return cx, cy


# ============ 只 hover，不点击 ============
def hover_only(page, node_locator, label=""):
    """
    只把鼠标移到节点中心（hover），不点击。
    这样能让 handle 显示，又不会触发底部工作台。
    """
    box = node_locator.bounding_box()
    if not box:
        raise RuntimeError("节点没有 bounding_box")
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    time.sleep(0.8)
    shot(page, f"tc0007_hover_{label}.png")


# ============ 拖拽连线 ============
def connect_nodes(page, node1, node2):
    print("\n=== 从节点1右侧 handle 拖到节点2左侧 handle ===")

    edge_before = page.locator(".react-flow__edge").count()
    print(f"连线前 .react-flow__edge 数量: {edge_before}")

    # 先 hover 节点1（不点击），显示 handle
    hover_only(page, node1["locator"], "node1_for_drag")
    src_x, src_y = get_handle_center(page, node1["locator"], "right")

    # 先 hover 节点2，再 hover 回节点1
    hover_only(page, node2["locator"], "node2_for_drag")
    hover_only(page, node1["locator"], "node1_again")
    dst_x, dst_y = get_handle_center(page, node2["locator"], "left")

    print(f"起点（node1 右 handle）: ({src_x:.1f},{src_y:.1f})")
    print(f"终点（node2 左 handle）: ({dst_x:.1f},{dst_y:.1f})")

    page.mouse.move(src_x, src_y)
    time.sleep(0.5)
    shot(page, "tc0007_before_drag.png")

    page.mouse.down()
    time.sleep(0.4)

    # 小步触发
    page.mouse.move(src_x + 10, src_y, steps=5)
    time.sleep(0.2)

    # 分段移动到目标
    mid_x = (src_x + dst_x) / 2
    mid_y = (src_y + dst_y) / 2
    page.mouse.move(mid_x, mid_y, steps=15)
    time.sleep(0.3)
    page.mouse.move(dst_x, dst_y, steps=15)
    time.sleep(0.5)

    shot(page, "tc0007_before_release.png")

    page.mouse.up()
    time.sleep(1.5)

    shot(page, "tc0007_after_connect.png")

    edge_after = page.locator(".react-flow__edge").count()
    print(f"连线后 .react-flow__edge 数量: {edge_after}")

    return edge_before, edge_after


# ============ 主流程 ============
def test_node_connect():
    if not IMAGE1_PATH.exists():
        print(f"[ERROR] 找不到图片1: {IMAGE1_PATH}")
        sys.exit(1)
    if not IMAGE2_PATH.exists():
        print(f"[ERROR] 找不到图片2: {IMAGE2_PATH}")
        sys.exit(1)
    print(f"[OK] 图片1: {IMAGE1_PATH}")
    print(f"[OK] 图片2: {IMAGE2_PATH}")

    exe = find_exe()
    print(f"[OK] 帧境AI 路径: {exe}")
    ensure_app_running(exe)

    pw, browser, page = connect_to_frame_realm()

    try:
        print(f"\n页面 URL: {page.url}")
        shot(page, "tc0007_connected.png")

        upload_image(page, IMAGE1_PATH, "img1")
        upload_image(page, IMAGE2_PATH, "img2")

        nodes = get_all_nodes(page)
        nodes = separate_nodes_horizontal(page, nodes)

        if len(nodes) < 2:
            raise RuntimeError(f"节点数不足 2 个，当前 {len(nodes)}")

        node1 = nodes[-2]
        node2 = nodes[-1]

        edge_before, edge_after = connect_nodes(page, node1, node2)

        print("\n=== 断言连线结果 ===")
        print(f"  edge 数量变化: {edge_before} -> {edge_after}")
        assert edge_after > edge_before, (
            f"未生成连线。edge 数量没增加：{edge_before} -> {edge_after}"
        )
        print("[PASS] 连线生成成功")

        print("\n=== TC-0007 测试通过 ===")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0007_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_node_connect()