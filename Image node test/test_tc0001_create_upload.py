"""
TC-0014 自动化测试：新建图片节点 + 上传本地图片
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

完全模拟用户操作：
    1. 双击画布 → 弹出菜单
    2. 选择【图片节点】→ 新建图片节点
    3. 点击节点里的【上传】按钮 → 弹 Windows 系统文件对话框
    4. 用 pywinauto 操作对话框（Alt+D 目录，Alt+N 文件名，回车）
    5. 图片导入成功，节点内显示图片

关键：
    节点里有两个按钮：<上传>、<绘制草图>。
    要点的是 <上传> 按钮，不是"点击上传"提示文字。

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

_ABS_IMG = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\草原.jpg")
_REL_IMG = ROOT / "testdata" / "草原.jpg"
IMAGE_PATH = _ABS_IMG if _ABS_IMG.exists() else _REL_IMG
IMAGE_DIR = IMAGE_PATH.parent
IMAGE_NAME = IMAGE_PATH.name

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


# ============ 新建图片节点 ============
def dblclick_canvas(page):
    print("\n=== 双击画布 ===")
    page.mouse.dblclick(600, 400)
    time.sleep(1.5)
    shot(page, "tc0014_after_dblclick_canvas.png")


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


# ============ 【核心修正】找图片节点里的「上传」按钮 ============
def find_upload_button(page):
    """
    找图片节点里的「上传」按钮。
    注意：节点里有"点击上传"文字（提示），也有"上传"按钮（可点）。
    必须用 get_by_role('button') 限定到按钮。
    """
    print("\n  查找图片节点里的「上传」按钮")

    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    if n == 0:
        print("  [FAIL] 画布上没有节点")
        return None
    node = nodes.nth(n - 1)

    try:
        text = (node.inner_text() or "").strip()
        print(f"  节点内文字: '{text[:150]}'")
    except Exception:
        pass

    # ============ 策略 1（最精确）：在节点内找 role=button 且 name="上传" 的 ============
    try:
        # 用 get_by_role 限定 name 精确等于"上传"
        btn = node.get_by_role("button", name="上传", exact=True)
        cnt = btn.count()
        print(f"    node.get_by_role('button', name='上传', exact=True) 命中 {cnt} 个")
        for i in range(cnt):
            el = btn.nth(i)
            if el.is_visible():
                box = el.bounding_box()
                if box:
                    print(f"      [{i}] pos=({box['x']:.0f},{box['y']:.0f}) size=({box['width']:.0f}x{box['height']:.0f})")
                return el, "role:button:上传(exact)"
    except Exception as e:
        print(f"    策略1失败: {e}")

    # ============ 策略 2：遍历节点内所有 button，text 精确等于"上传" ============
    try:
        btns = node.locator("button")
        print(f"    节点内 button 总数: {btns.count()}")
        for i in range(btns.count()):
            b = btns.nth(i)
            if not b.is_visible():
                continue
            t = (b.inner_text() or "").strip()
            title = b.get_attribute("title") or ""
            aria = b.get_attribute("aria-label") or ""
            box = b.bounding_box()
            pos = f"({box['x']:.0f},{box['y']:.0f})" if box else "?"
            print(f"      button[{i}] text='{t}' title='{title}' aria='{aria}' pos={pos}")
            if t == "上传":
                return b, f"button:text='上传'"
    except Exception as e:
        print(f"    策略2失败: {e}")

    # ============ 策略 3：找 text='上传' 且是 button 的父级 ============
    try:
        texts = node.get_by_text("上传", exact=True)
        print(f"    node.get_by_text('上传', exact=True) 命中 {texts.count()} 个")
        for i in range(texts.count()):
            el = texts.nth(i)
            if not el.is_visible():
                continue
            tag = el.evaluate("el => el.tagName")
            print(f"      [{i}] tag={tag}")
            if tag == "BUTTON":
                return el, "get_by_text:上传(BUTTON)"
            # 父级是 button
            try:
                parent = el.locator("xpath=ancestor::button[1]")
                if parent.count() > 0:
                    return parent.first, "get_by_text:上传(父级button)"
            except Exception:
                pass
    except Exception as e:
        print(f"    策略3失败: {e}")

    print("  [FAIL] 找不到「上传」按钮")
    return None, None


# ============ pywinauto 操作系统文件对话框 ============
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
        print(f"  对话框标题: '{dlg.window_text()}'")
    except Exception:
        pass

    try:
        dlg.set_focus()
        time.sleep(0.5)
    except Exception:
        pass

    # 步骤 1：Alt+D 地址栏 → 输目录 → 回车
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
        print("  [OK] 已跳转目录")
    except Exception as e:
        print(f"  步骤1失败: {e}")

    # 步骤 2：Alt+N 文件名框 → 输文件名 → 回车
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
        print("  [OK] 已回车打开")
    except Exception as e:
        print(f"  步骤2失败: {e}")

    return True


# ============ 上传图片（完全模拟用户操作） ============
def upload_image(page):
    print("\n\n########## 上传图片（模拟用户操作）##########")
    print(f"  文件: {IMAGE_PATH}")

    if not IMAGE_PATH.exists():
        print(f"  [ERROR] 文件不存在")
        return False

    if not PYWINAUTO_OK:
        print("  [FAIL] pywinauto 未安装")
        return False

    # 1. 找「上传」按钮
    upload_btn, entry_type = find_upload_button(page)
    if not upload_btn:
        print("  [FAIL] 找不到「上传」按钮")
        return False

    print(f"  上传按钮: {entry_type}")

    # 2. 点击「上传」按钮 → 触发系统对话框
    print("\n  点击「上传」按钮...")
    try:
        upload_btn.scroll_into_view_if_needed()
        time.sleep(0.3)
    except Exception:
        pass

    try:
        upload_btn.click(timeout=3000)
        print("  [OK] 点击成功")
    except Exception as e:
        print(f"  点击失败: {e}，尝试 force=True")
        try:
            upload_btn.click(timeout=3000, force=True)
            print("  [OK] force 点击成功")
        except Exception as e2:
            print(f"  force 也失败: {e2}，尝试坐标点击")
            try:
                box = upload_btn.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    print("  [OK] 坐标点击")
            except Exception as e3:
                print(f"  坐标点击也失败: {e3}")
                return False

    time.sleep(3)
    shot(page, "tc0014_after_click_upload.png")

    # 3. pywinauto 系统对话框
    dialog_ok = handle_system_dialog(IMAGE_DIR, IMAGE_NAME)

    time.sleep(3)
    shot(page, "tc0014_after_upload.png")

    return dialog_ok


# ============ 验证图片显示 ============
def check_image_display(page):
    print("\n\n########## 验证图片显示 ##########")

    print("  查找节点内的 <img>：")
    imgs = page.locator(".react-flow__node img")
    cnt = imgs.count()
    print(f"  找到 {cnt} 个 img")

    result = {"img_count": 0, "img_src": "", "img_size": None}

    for i in range(cnt):
        el = imgs.nth(i)
        try:
            if not el.is_visible():
                continue
            src = el.get_attribute("src") or ""
            box = el.bounding_box()
            if box:
                print(f"    img[{i}] src='{src[:80]}' size=({box['width']:.0f}x{box['height']:.0f})")
            else:
                print(f"    img[{i}] src='{src[:80]}'")
            if src and (src.startswith("blob:") or src.startswith("data:") or src.startswith("file:") or src.startswith("http")):
                result["img_count"] = 1
                result["img_src"] = src
                result["img_size"] = box
                break
        except Exception:
            pass

    print("\n  查找节点内的 canvas：")
    canvases = page.locator(".react-flow__node canvas")
    print(f"  找到 {canvases.count()} 个 canvas")

    print("\n  查找节点内文字：")
    nodes = page.locator(".react-flow__node")
    for i in range(nodes.count()):
        try:
            t = (nodes.nth(i).inner_text() or "").strip()
            if t:
                print(f"    node[{i}] text='{t[:80]}'")
        except Exception:
            pass

    return result


# ============ 主流程 ============
def test_tc0014():
    print("=== TC-0014：新建图片节点 + 上传本地图片 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        node_count_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {node_count_before}")

        dblclick_canvas(page)
        click_menu_item(page, "图片节点")
        time.sleep(1.5)
        shot(page, "tc0014_after_add_image_node.png")
        wait_for_new_node(page, node_count_before, timeout=15)
        shot(page, "tc0014_new_node.png")

        upload_ok = upload_image(page)
        img_result = check_image_display(page)

        print("\n\n=== 结果汇总 ===")
        print(f"  {'✅' if upload_ok else '❌'} 上传图片")
        print(f"  {'✅' if img_result['img_count'] > 0 else '❌'} 节点内图片数: {img_result['img_count']}")
        if img_result['img_src']:
            print(f"  图片 src: {img_result['img_src'][:80]}")

        print("\n\n=== 断言 ===")
        errors = []

        if not upload_ok:
            errors.append("图片上传失败")
        if img_result['img_count'] == 0:
            errors.append("节点内没有显示图片")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0014，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0014 未通过")

        print("[PASS] TC-0014 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0014_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0014()