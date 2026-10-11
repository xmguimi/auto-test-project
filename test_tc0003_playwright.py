
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

# 你的实际图片路径
IMAGE_PATH = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群.jpg")

# 帧境.exe 常见候选路径
EXE_CANDIDATES = [
    r"F:\zhenjing\framerealm-canvas\帧境.exe",
    r"C:\Program Files\帧境AI\帧境.exe",
    r"C:\Program Files (x86)\帧境AI\帧境.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\帧境AI\帧境.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\framerealm-canvas\帧境.exe"),
]

# 拖拽偏移量（相对像素）
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


def ensure_app_running(exe_path, port=PORT, timeout=30):
    """确保帧境AI已启动并开放调试端口"""
    if is_cdp_ready(port):
        print(f"[OK] 帧境AI 已在运行，CDP 端口 {port} 可用")
        return

    print(f"[..] 启动帧境AI: {exe_path}")
    subprocess.Popen([exe_path, f"--remote-debugging-port={port}"])

    for i in range(timeout):
        if is_cdp_ready(port):
            print(f"[OK] 帧境AI 启动成功，CDP 端口 {port} 就绪")
            return
        time.sleep(1)
        print(f"     等待中... {i + 1}s")

    raise RuntimeError(f"帧境AI 启动超时（{timeout}s），端口 {port} 未就绪")


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
    """
    上传本地图片，生成图片节点。
    优先用 input[type=file].set_input_files（最稳，跨电脑可用）。
    """
    print("\n=== 上传图片，生成图片节点 ===")

    file_inputs = page.locator("input[type='file']")
    count = file_inputs.count()
    print(f"页面上 input[type='file'] 数量: {count}")

    if count == 0:
        raise RuntimeError(
            "没找到 file input，上传可能走系统弹窗。"
            "请手动确认上传入口，或改用 pyautogui 方案。"
        )

    # 记录上传前节点数，作为等待新节点出现的基准
    nodes_before = page.locator(".react-flow__node").count()
    print(f"上传前 .react-flow__node 数量: {nodes_before}")

    # 选一个 accept 含 image 的 input
    target = None
    for i in range(count):
        el = file_inputs.nth(i)
        accept = el.get_attribute("accept") or ""
        print(f"  [{i}] accept={accept}")
        if "image" in accept:
            target = el
            break
    if target is None:
        target = file_inputs.first

    target.set_input_files(str(image_path))
    print(f"已通过 set_input_files 上传: {image_path}")

    # 等待新节点出现（最多 15 秒）
    print("等待新节点出现...")
    for _ in range(15):
        nodes_now = page.locator(".react-flow__node").count()
        if nodes_now > nodes_before:
            print(f"[OK] 新节点已出现，当前节点数: {nodes_now}")
            break
        time.sleep(1)
    else:
        print(f"[WARN] 15s 内节点数未增加（{nodes_before} -> {page.locator('.react-flow__node').count()}）")

    time.sleep(1)
    shot(page, "after_upload.png")


def find_image_node(page):
    """找到刚生成的图片节点（React Flow 节点）"""
    print("\n=== 查找图片节点 ===")

    for sel in [".react-flow__node", ".react-flow__node-UNIVERSAL", "[data-id]"]:
        loc = page.locator(sel)
        n = loc.count()
        if n > 0:
            print(f"[OK] 用选择器 '{sel}' 找到 {n} 个节点，取最后一个（最新上传的）")
            return loc.nth(n - 1)

    # 兜底
    print("[WARN] 没找到节点，安全打印所有 class 含 'node' 的元素：")
    nodes = page.query_selector_all("[class*='node']")
    for i, el in enumerate(nodes[:20]):
        try:
            cls = el.get_attribute("class") or ""
            tag = el.evaluate("el => el.tagName")
            print(f"  [{i}] tag={tag} class='{cls[:80]}'")
        except Exception as e:
            print(f"  [{i}] 读取失败: {e}")

    raise RuntimeError("没找到图片节点")


def drag_node(page, node):
    """选中节点并拖拽（React Flow 专用）"""
    print("\n=== 拖拽节点 ===")

    box_before = node.bounding_box()
    if not box_before:
        raise RuntimeError("节点没有 bounding_box，可能不可见")

    print(f"拖拽前位置: {box_before}")

    start_x = box_before["x"] + box_before["width"] / 2
    start_y = box_before["y"] + box_before["height"] / 2

    # 先点击选中
    page.mouse.click(start_x, start_y)
    time.sleep(0.5)
    shot(page, "after_select.png")

    selected_count = page.locator(".react-flow__node.selected").count()
    print(f"选中后 .react-flow__node.selected 数量: {selected_count}")

    # 按下鼠标
    page.mouse.move(start_x, start_y)
    time.sleep(0.2)
    page.mouse.down()
    time.sleep(0.3)

    # 小步移动触发拖拽阈值
    page.mouse.move(start_x + 5, start_y + 5, steps=3)
    time.sleep(0.2)
    page.mouse.move(start_x + 15, start_y + 15, steps=3)
    time.sleep(0.2)

    # 打印拖拽中的 transform，帮判断
    try:
        mid_tf = node.evaluate("el => el.style.transform")
        print(f"拖拽中 transform: {mid_tf}")
    except Exception as e:
        print(f"读取 transform 失败: {e}")

    # 大步移动到目标
    end_x = start_x + DRAG_OFFSET_X
    end_y = start_y + DRAG_OFFSET_Y
    page.mouse.move(end_x, end_y, steps=20)
    time.sleep(0.3)

    page.mouse.up()
    time.sleep(1)

    shot(page, "after_drag.png")

    box_after = node.bounding_box()
    print(f"拖拽后位置: {box_after}")

    return box_before, box_after

def assert_drag_result(box_before, box_after):
    """
    断言：
    1. 节点确实移动了
    2. 移动距离与预期偏移量接近（允许一定误差）
    3. 节点没有跑出画布
    """
    print("\n=== 断言拖拽结果 ===")

    dx = box_after["x"] - box_before["x"]
    dy = box_after["y"] - box_before["y"]
    print(f"实际位移: dx={dx:.1f}, dy={dy:.1f}（预期 dx={DRAG_OFFSET_X}, dy={DRAG_OFFSET_Y}）")

    assert abs(dx) > 50 or abs(dy) > 50, (
        f"节点未移动或移动过小：dx={dx}, dy={dy}"
    )

    tol_x = max(80, abs(DRAG_OFFSET_X) * 0.3)
    tol_y = max(80, abs(DRAG_OFFSET_Y) * 0.3)
    assert abs(dx - DRAG_OFFSET_X) < tol_x, (
        f"X 方向偏移异常：实际 dx={dx}, 预期 {DRAG_OFFSET_X}, 容差 {tol_x}"
    )
    assert abs(dy - DRAG_OFFSET_Y) < tol_y, (
        f"Y 方向偏移异常：实际 dy={dy}, 预期 {DRAG_OFFSET_Y}, 容差 {tol_y}"
    )

    assert box_after["x"] >= 0 and box_after["y"] >= 0, (
        f"节点跑到画布外：{box_after}"
    )

    print("[PASS] 拖拽位置断言通过")


# ============ 测试主流程 ============
def test_drag_node():
    """TC-0003：拖拽单个图片节点"""

    # 0. 检查图片资源
    if not IMAGE_PATH.exists():
        print(f"[ERROR] 找不到测试图片: {IMAGE_PATH}")
        print("请确认 testdata/羊群.jpg 存在")
        sys.exit(1)
    print(f"[OK] 测试图片: {IMAGE_PATH}")

    # 1. 确保帧境AI在跑
    exe = find_exe()
    print(f"[OK] 帧境AI 路径: {exe}")
    ensure_app_running(exe)

    # 2. 连接
    pw, browser, page = connect_to_frame_realm()

    try:
        print(f"\n页面 URL: {page.url}")
        shot(page, "connected.png")

        # 3. 上传图片 → 生成图片节点
        upload_image(page, IMAGE_PATH)

        # 4. 找到图片节点
        node = find_image_node(page)

        # 5. 拖拽节点
        box_before, box_after = drag_node(page, node)

        # 6. 断言结果
        assert_drag_result(box_before, box_after)

        print("\n=== TC-0003 测试通过 ===")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_drag_node()