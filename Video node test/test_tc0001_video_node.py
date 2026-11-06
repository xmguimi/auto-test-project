"""
TC-0001 自动化测试：新建视频节点 + 上传本地视频 + 播放
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布 → 弹出菜单
    2. 选择【视频节点】→ 新建视频节点
    3. 点击上传入口 → 弹 Windows 文件对话框
    4. pywinauto 操作对话框上传 羊群奔跑.mp4
    5. 验证视频节点显示视频封面
    6. 点击播放，验证视频能播放

定位策略（跨电脑可运行）：
    - 全部用 Playwright 语义定位
    - 节点用 data-id 标识
    - 上传走 pywinauto（Windows 通用）
    - 视频播放器用 <video> 元素

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

_ABS_VIDEO = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群奔跑.mp4")
_REL_VIDEO = ROOT / "testdata" / "羊群奔跑.mp4"
VIDEO_PATH = _ABS_VIDEO if _ABS_VIDEO.exists() else _REL_VIDEO
VIDEO_DIR = VIDEO_PATH.parent
VIDEO_NAME = VIDEO_PATH.name

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
def dblclick_canvas(page, x=600, y=400):
    print(f"\n=== 双击画布 ({x},{y}) ===")
    page.mouse.dblclick(x, y)
    time.sleep(1.5)
    shot(page, f"tc0018_dblclick_{x}_{y}.png")


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

    # 步骤 1：Alt+D 输目录
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
        print(f"  步骤1 OK: 目录 = {file_dir}")
    except Exception as e:
        print(f"  步骤1失败: {e}")

    # 步骤 2：Alt+N 输文件名
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
        print(f"  步骤2 OK: 文件名 = {file_name}")
    except Exception as e:
        print(f"  步骤2失败: {e}")

    return True


# ============ 新建视频节点 + 上传 ============
def create_video_node_with_upload(page, video_path, dblclick_x=600, dblclick_y=400):
    print(f"\n\n########## 新建视频节点并上传：{video_path.name} ##########")

    before = page.locator(".react-flow__node").count()

    # 1. 双击画布
    dblclick_canvas(page, dblclick_x, dblclick_y)

    # 2. 点「视频节点」
    click_menu_item(page, "视频节点")
    time.sleep(1.5)

    # 3. 等新节点
    node_id = get_new_node_id(page, before)
    shot(page, "tc0018_after_add_node.png")

    # 4. 点节点里的「上传」按钮
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
    shot(page, "tc0018_after_click_upload.png")

    # 5. pywinauto 上传
    handle_system_dialog(video_path.parent, video_path.name)
    time.sleep(8)   # 视频处理慢，多等
    shot(page, "tc0018_after_upload.png")

    return node_id


# ============ 验证视频节点显示 ============
def check_video_display(page, node_id):
    """
    检查视频节点：
      - 是否有 <video> 元素
      - video 的 src、duration、宽高
      - 封面（poster）
    """
    print("\n\n########## 验证视频显示 ##########")

    result = {
        "video_count": 0,
        "src": "",
        "duration": None,
        "size": None,
        "poster": "",
    }

    node = get_node_by_id(page, node_id)

    # 找 <video>
    videos = node.locator("video")
    cnt = videos.count()
    print(f"  节点内 video 元素数: {cnt}")
    result["video_count"] = cnt

    if cnt > 0:
        v = videos.nth(0)
        try:
            src = v.get_attribute("src") or ""
            poster = v.get_attribute("poster") or ""
            box = v.bounding_box()
            print(f"    src='{src[:80]}'")
            print(f"    poster='{poster[:80]}'")
            if box:
                print(f"    size=({box['width']:.0f}x{box['height']:.0f})")
                result["size"] = box
            result["src"] = src
            result["poster"] = poster

            # 读 duration（通过 JS）
            try:
                dur = v.evaluate("el => el.duration")
                if dur and dur > 0:
                    print(f"    duration={dur:.2f}s")
                    result["duration"] = dur
            except Exception:
                pass
        except Exception as e:
            print(f"    读取 video 属性失败: {e}")

    # 找 canvas（如果封面是 canvas 渲染）
    canvases = node.locator("canvas")
    print(f"  节点内 canvas 数: {canvases.count()}")

    return result


# ============ 点击播放，验证视频能播放 ============
def check_video_play(page, node_id):
    """
    点击视频播放按钮，验证：
      - 播放后 currentTime 增加
      - 没有 paused
    """
    print("\n\n########## 点击播放 ##########")

    result = {
        "play_clicked": False,
        "current_time_before": 0,
        "current_time_after": 0,
        "paused_before": True,
        "paused_after": True,
        "played": False,
    }

    node = get_node_by_id(page, node_id)
    videos = node.locator("video")
    if videos.count() == 0:
        print("  [FAIL] 节点内没有 video 元素")
        return result

    v = videos.nth(0)

    # 读初始状态
    try:
        result["current_time_before"] = v.evaluate("el => el.currentTime")
        result["paused_before"] = v.evaluate("el => el.paused")
        print(f"  点击前: currentTime={result['current_time_before']:.2f}, paused={result['paused_before']}")
    except Exception as e:
        print(f"  读初始状态失败: {e}")

    # 尝试 1：点视频元素本身（很多播放器点视频即播放）
    try:
        box = v.bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            print(f"  点击视频中心 ({cx:.0f},{cy:.0f})")
            page.mouse.click(cx, cy)
            result["play_clicked"] = True
            time.sleep(0.5)
    except Exception as e:
        print(f"  点击视频失败: {e}")

    # 尝试 2：找播放按钮（圆形按钮或 ▶ 图标）
    if not result["play_clicked"]:
        try:
            play_btn = node.locator("button[aria-label*='播放'], button[title*='播放']").first
            if play_btn.count() > 0 and play_btn.is_visible():
                play_btn.click(timeout=3000)
                result["play_clicked"] = True
                print("  点击播放按钮")
        except Exception:
            pass

    # 等待播放
    time.sleep(3)
    shot(page, "tc0018_after_play.png")

    # 读状态
    try:
        result["current_time_after"] = v.evaluate("el => el.currentTime")
        result["paused_after"] = v.evaluate("el => el.paused")
        print(f"  点击后: currentTime={result['current_time_after']:.2f}, paused={result['paused_after']}")

        # 判定是否播放：currentTime 增加 或 paused 变 false
        if result["current_time_after"] > result["current_time_before"] + 0.5:
            result["played"] = True
        elif not result["paused_after"]:
            result["played"] = True
    except Exception as e:
        print(f"  读状态失败: {e}")

    return result


# ============ 验证节点可选中、拖动 ============
def check_node_draggable(page, node_id):
    """检查节点能否选中、拖动"""
    print("\n\n########## 验证节点可选中、拖动 ##########")

    result = {"selected": False, "dragged": False}

    node = get_node_by_id(page, node_id)
    box_before = node.bounding_box()
    if not box_before:
        print("  [FAIL] 节点没有 bounding_box")
        return result

    cx = box_before["x"] + box_before["width"] / 2
    cy = box_before["y"] + box_before["height"] / 2

    # 选中
    page.mouse.click(cx, cy)
    time.sleep(0.8)
    selected_count = page.locator(".react-flow__node.selected").count()
    print(f"  选中后 .selected 数: {selected_count}")
    result["selected"] = selected_count > 0

    # 拖动
    page.mouse.move(cx, cy)
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.3)
    page.mouse.move(cx + 5, cy + 5, steps=3)
    time.sleep(0.2)
    page.mouse.move(cx + 100, cy + 50, steps=15)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(1)

    box_after = node.bounding_box()
    if box_after:
        dx = box_after["x"] - box_before["x"]
        dy = box_after["y"] - box_before["y"]
        print(f"  拖动位移: dx={dx:.0f}, dy={dy:.0f}")
        result["dragged"] = abs(dx) > 30 or abs(dy) > 20

    shot(page, "tc0018_after_drag.png")
    return result


# ============ 主流程 ============
def test_tc0018():
    print("=== TC-0018：新建视频节点 + 上传本地视频 + 播放 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        print(f"[INFO] 初始节点数: {page.locator('.react-flow__node').count()}")

        # 1. 新建视频节点 + 上传
        node_id = create_video_node_with_upload(page, VIDEO_PATH, 600, 400)
        print(f"  视频节点 data-id: {node_id}")

        # 2. 验证视频显示
        display = check_video_display(page, node_id)

        # 3. 验证视频播放
        play = check_video_play(page, node_id)

        # 4. 验证节点可选中、拖动
        drag = check_node_draggable(page, node_id)

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  node_id: {node_id}")
        print(f"  {'✅' if display['video_count'] > 0 else '❌'} 节点内有 video 元素: {display['video_count']}")
        if display["duration"]:
            print(f"  视频时长: {display['duration']:.2f}s")
        if display["size"]:
            print(f"  视频尺寸: {display['size']['width']:.0f}x{display['size']['height']:.0f}")
        print(f"  {'✅' if play['played'] else '❌'} 视频可播放")
        print(f"  {'✅' if drag['selected'] else '❌'} 节点可选中")
        print(f"  {'✅' if drag['dragged'] else '❌'} 节点可拖动")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        if display["video_count"] == 0:
            errors.append("节点内没有 <video> 元素")
        if not play["played"]:
            errors.append(f"视频未播放（currentTime {play['current_time_before']:.2f} → {play['current_time_after']:.2f}, paused {play['paused_before']} → {play['paused_after']}）")
        if not drag["selected"]:
            errors.append("节点无法选中")
        if not drag["dragged"]:
            errors.append("节点无法拖动")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0018，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0018 未通过")

        print("[PASS] TC-0018 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0018_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0018()