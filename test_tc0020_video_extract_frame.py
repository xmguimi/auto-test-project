"""
TC-0020 自动化测试：视频节点抽帧（首帧/尾帧/当前帧）
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布 → 新建视频节点
    2. 上传本地视频 羊群奔跑.mp4
    3. 选中视频节点
    4. 点【抽帧】→ 选【截取首帧】→ 生成图片节点1
    5. 再点【抽帧】→ 选【截取尾帧】→ 生成图片节点2
    6. 再点【抽帧】→ 选【截取当前帧】→ 生成图片节点3
    7. 验证 3 次抽帧都成功

关键 UI（从截图确认）：
    - 点「抽帧」后弹出下拉菜单：截取首帧 | 截取尾帧 | 截取当前帧 | 自由抽帧
    - 每次抽帧生成一个新图片节点

定位策略（跨电脑可运行）：
    - 全部用 Playwright 语义定位
    - 节点用 data-id 标识
    - 上传走 pywinauto（Windows 通用）
    - 抽帧菜单项用文字精确匹配

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
    shot(page, f"tc0020_dblclick_{x}_{y}.png")


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
def create_video_node_with_upload(page, video_path, dblclick_x=600, dblclick_y=400):
    print(f"\n\n########## 新建视频节点并上传：{video_path.name} ##########")

    before = page.locator(".react-flow__node").count()

    dblclick_canvas(page, dblclick_x, dblclick_y)
    click_menu_item(page, "视频节点")
    time.sleep(1.5)
    node_id = get_new_node_id(page, before)
    shot(page, "tc0020_after_add_node.png")

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
    shot(page, "tc0020_after_click_upload.png")

    handle_system_dialog(video_path.parent, video_path.name)
    time.sleep(8)
    shot(page, "tc0020_after_upload.png")

    return node_id


# ============ 点「抽帧」并选子项 ============
def click_extract_frame(page, submenu_text):
    """
    点「抽帧」按钮，再在弹出的菜单里选 submenu_text。
    submenu_text 例如："截取首帧"、"截取尾帧"、"截取当前帧"
    """
    print(f"\n\n########## 点击「抽帧」→「{submenu_text}」 ##########")

    # 1. 点「抽帧」按钮
    extract_btn = None
    try:
        loc = page.locator("button:text-is('抽帧')")
        for i in range(loc.count()):
            el = loc.nth(i)
            if el.is_visible():
                extract_btn = el
                box = el.bounding_box()
                if box:
                    print(f"  找到「抽帧」按钮 ({box['x']:.0f},{box['y']:.0f})")
                break
    except Exception:
        pass

    if not extract_btn:
        # 兜底
        try:
            loc = page.locator("button:has-text('抽帧')")
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    extract_btn = el
                    break
        except Exception:
            pass

    if not extract_btn:
        print("  [FAIL] 找不到「抽帧」按钮")
        return False

    try:
        extract_btn.click(timeout=3000)
        print("  [OK] 点击「抽帧」")
        time.sleep(1.5)
        shot(page, f"tc0020_menu_{submenu_text}.png")
    except Exception as e:
        print(f"  点击「抽帧」失败: {e}")
        return False

    # 2. 等菜单出现，选子项
    submenu_clicked = False
    for sel in [
        f"button:text-is('{submenu_text}')",
        f"[role='menuitem']:has-text('{submenu_text}')",
        f".cm-item:has-text('{submenu_text}')",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                box = el.bounding_box()
                if box and box["width"] < 400:
                    el.click(timeout=3000)
                    print(f"  [OK] 点击「{submenu_text}」（{sel}）")
                    submenu_clicked = True
                    time.sleep(5)   # 抽帧处理时间
                    break
            if submenu_clicked:
                break
        except Exception:
            pass

    if not submenu_clicked:
        # 兜底：get_by_text
        try:
            el = page.get_by_text(submenu_text, exact=True).first
            if el.count() > 0 and el.is_visible():
                el.click(timeout=3000)
                print(f"  [OK] get_by_text 点击「{submenu_text}」")
                submenu_clicked = True
                time.sleep(5)
        except Exception:
            pass

    if not submenu_clicked:
        print(f"  [FAIL] 找不到子菜单「{submenu_text}」")
        return False

    shot(page, f"tc0020_after_{submenu_text}.png")
    return True


# ============ 验证生成新节点 ============
def check_new_nodes(page, before_count, label=""):
    """验证生成了新节点"""
    print(f"\n  验证生成新节点（{label}）")
    time.sleep(2)
    cur = page.locator(".react-flow__node").count()
    print(f"    节点数: {before_count} → {cur}")
    new_count = cur - before_count

    if new_count > 0:
        nodes = page.locator(".react-flow__node")
        for i in range(before_count, cur):
            try:
                node = nodes.nth(i)
                imgs = node.locator("img")
                if imgs.count() > 0:
                    src = imgs.nth(0).get_attribute("src") or ""
                    print(f"      新节点[{i}] img src='{src[:60]}'")
            except Exception:
                pass

    return {"before": before_count, "after": cur, "new_nodes": new_count}


# ============ 主流程 ============
def test_tc0020():
    print("=== TC-0020：视频节点抽帧（首帧/尾帧/当前帧）===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        node_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {node_before}")

        # 1. 新建视频节点 + 上传
        video_node_id = create_video_node_with_upload(page, VIDEO_PATH, 600, 400)
        print(f"  视频节点 data-id: {video_node_id}")

        # 2. 选中视频节点
        video_node = get_node_by_id(page, video_node_id)
        click_node_locator(page, video_node)
        time.sleep(1)
        shot(page, "tc0020_selected_video_node.png")

        results = {}

        # ============ 第 1 次：截取首帧 ============
        before1 = page.locator(".react-flow__node").count()
        ok1 = click_extract_frame(page, "截取首帧")
        r1 = check_new_nodes(page, before1, "首帧")
        results["截取首帧"] = {"click_ok": ok1, "new_nodes": r1["new_nodes"]}

        # ============ 第 2 次：截取尾帧 ============
        # 重新选中视频节点（因为可能有新节点生成，也可能焦点变了）
        video_node = get_node_by_id(page, video_node_id)
        click_node_locator(page, video_node)
        time.sleep(1)

        before2 = page.locator(".react-flow__node").count()
        ok2 = click_extract_frame(page, "截取尾帧")
        r2 = check_new_nodes(page, before2, "尾帧")
        results["截取尾帧"] = {"click_ok": ok2, "new_nodes": r2["new_nodes"]}

        # ============ 第 3 次：截取当前帧 ============
        video_node = get_node_by_id(page, video_node_id)
        click_node_locator(page, video_node)
        time.sleep(1)

        before3 = page.locator(".react-flow__node").count()
        ok3 = click_extract_frame(page, "截取当前帧")
        r3 = check_new_nodes(page, before3, "当前帧")
        results["截取当前帧"] = {"click_ok": ok3, "new_nodes": r3["new_nodes"]}

        # 最终截图
        shot(page, "tc0020_final.png")

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  视频节点 data-id: {video_node_id}")
        for k, v in results.items():
            print(f"  {'✅' if v['click_ok'] else '❌'} {k}：点击{'成功' if v['click_ok'] else '失败'}，新增节点 {v['new_nodes']}")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        for k, v in results.items():
            if not v["click_ok"]:
                errors.append(f"{k}：点击失败")
            if v["new_nodes"] <= 0:
                errors.append(f"{k}：没有生成新节点")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0020，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0020 未通过")

        print("[PASS] TC-0020 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0020_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0020()