"""
TC0002 自动化测试：剪辑工作台-选中素材后的属性面板

流程：
    1. 右键图片节点 → 加入剪辑
    2. 从左侧素材区把素材拖入时间线
    3. 选中时间线上的片段
    4. 断言中间预览区显示素材画面
    5. 断言右侧属性面板显示：层级/位置 X/Y/缩放 X/Y/旋转

适配：
    - 剪辑工作台 = 主画布页里的 iframe（dist/opencut/index.html）
    - iframe 坐标 = iframe 内相对坐标 + iframe 在主 page 的偏移
    - 鼠标/截图统一用 page，不用 frame

运行前置：
    pip install playwright requests
    python -m playwright install chromium
    帧境 AI 需带 --remote-debugging-port=9222 启动

环境变量（可选）：
    FJ_CDP_HOST      默认 localhost
    FJ_CDP_PORT      默认 9222
    FJ_WINDOW_TITLE  默认「帧境」
    FJ_SHOT_DIR      默认 ./screenshots
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ==================== 配置区 ====================
CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
WINDOW_TITLE_KEYWORD = os.getenv("FJ_WINDOW_TITLE", "帧境")
SHOT_DIR = Path(os.getenv("FJ_SHOT_DIR", "screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

OPEN_TIMEOUT = 20
REGION_TIMEOUT = 8

SEL_NODE = ".react-flow__node"
EDITOR_FRAME_HINTS = ["opencut", "editing", "clip"]

RIGHT_TEXTS = ["层级", "位置", "缩放", "旋转"]
CENTER_TEXTS = ["画质", "缩放", "比例", "原画", "适应", "16:9"]


# ==================== 基础工具 ====================
def log(msg):
    print(msg, flush=True)


def shot(page, name):
    """截图：只能用 page，不能用 frame。"""
    try:
        p = SHOT_DIR / name
        page.screenshot(path=str(p))
        log(f"[SHOT] {p}")
    except Exception as e:
        log(f"[SHOT-FAIL] {name}: {e}")


def is_cdp_ready(host=CDP_HOST, port=CDP_PORT):
    try:
        r = requests.get(f"http://{host}:{port}/json/version", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def preflight_check(page):
    """启动前检查：CDP、画布节点、依赖。"""
    log("\n=== 启动前检查 ===")
    errors = []

    # 1) CDP
    if not is_cdp_ready():
        errors.append(
            f"CDP 未就绪：请确认帧境 AI 已带 --remote-debugging-port={CDP_PORT} 启动"
        )
    else:
        log(f"  ✅ CDP 就绪 ({CDP_HOST}:{CDP_PORT})")

    # 2) 画布节点
    try:
        cnt = page.locator(SEL_NODE).count()
        if cnt == 0:
            errors.append("画布上没有节点：请先在画布中创建一个图片节点")
        else:
            log(f"  ✅ 画布节点数: {cnt}")
    except Exception as e:
        errors.append(f"读取画布节点失败: {e}")

    if errors:
        log("  ❌ 启动前检查未通过：")
        for e in errors:
            log(f"    - {e}")
        raise RuntimeError("启动前检查未通过")
    log("  ✅ 启动前检查通过")


def connect():
    if not is_cdp_ready():
        raise RuntimeError(f"CDP 未就绪：请确认帧境已带 --remote-debugging-port={CDP_PORT} 启动")
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
    pages = browser.contexts[0].pages
    log(f"[DEBUG] 共 {len(pages)} 个 page：")
    for i, p in enumerate(pages):
        try:
            log(f"  [{i}] title='{p.title()}' url='{p.url}'")
        except Exception:
            pass
    target = None
    for p in pages:
        try:
            if WINDOW_TITLE_KEYWORD in (p.title() or ""):
                target = p
                break
        except Exception:
            pass
    if not target:
        target = pages[0]
    log(f"[OK] 已连接主页面: title='{target.title()}'")
    return pw, browser, target


def text_exists(scope, text, timeout=REGION_TIMEOUT, exact=False):
    end = time.time() + timeout
    while time.time() < end:
        try:
            loc = scope.get_by_text(text, exact=exact)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def click_visible_text(page, text, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        try:
            loc = page.get_by_text(text, exact=True)
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    el.click(timeout=2000)
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def find_editor_frame(page, timeout=REGION_TIMEOUT):
    log(f"\n=== 查找剪辑工作台 iframe（最多 {timeout}s）===")
    end = time.time() + timeout
    while time.time() < end:
        for f in page.frames:
            try:
                if f == page.main_frame:
                    continue
                url = (f.url or "").lower()
                if any(k in url for k in EDITOR_FRAME_HINTS):
                    log(f"  [OK] URL 命中 iframe: {f.url}")
                    return f
            except Exception:
                pass
        time.sleep(0.4)
    log("  [WARN] 未找到剪辑工作台 iframe，回退主 page")
    return page


def get_iframe_offset(page, editor_frame):
    """
    返回剪辑工作台 iframe 在主 page 中的 (offset_x, offset_y, width, height)。
    鼠标/截图坐标换算用。
    """
    try:
        iframes = page.locator("iframe")
        cnt = iframes.count()
        for i in range(cnt):
            el = iframes.nth(i)
            src = (el.get_attribute("src") or "").lower()
            if any(k in src for k in EDITOR_FRAME_HINTS):
                box = el.bounding_box()
                if box:
                    log(f"  iframe 偏移: ({box['x']:.0f},{box['y']:.0f}) "
                        f"size=({box['width']:.0f}x{box['height']:.0f})")
                    return box["x"], box["y"], box["width"], box["height"]
        # 兜底：第一个可见 iframe
        box = iframes.first.bounding_box()
        if box:
            log(f"  [WARN] 用第一个 iframe 兜底: ({box['x']:.0f},{box['y']:.0f})")
            return box["x"], box["y"], box["width"], box["height"]
    except Exception as e:
        log(f"  get_iframe_offset 异常: {e}")
    return 0, 0, 0, 0


# ==================== 步骤 1：右键 → 加入剪辑 ====================
def right_click_node_and_open_clip(page):
    log("\n=== 步骤1：右键节点 → 加入剪辑 ===")
    nodes = page.locator(SEL_NODE)
    if nodes.count() == 0:
        raise RuntimeError("画布上没有节点")

    target = None
    for i in range(nodes.count()):
        n = nodes.nth(i)
        try:
            if n.locator("img").count() > 0 and n.is_visible():
                target = n
                break
        except Exception:
            pass
    if target is None:
        target = nodes.first

    box = target.bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.click(cx, cy, button="right")
    time.sleep(1.0)
    shot(page, "tc0002_after_right_click.png")

    if not click_visible_text(page, "加入剪辑", timeout=5):
        for alt in ["剪辑", "加入编辑器", "剪辑工作台"]:
            if click_visible_text(page, alt, timeout=2):
                log(f"  [OK] 用备选文案点击：{alt}")
                break
        else:
            raise RuntimeError("菜单里找不到「加入剪辑」")
    log("  [OK] 点击「加入剪辑」")
    time.sleep(2.0)
    shot(page, "tc0002_after_click_clip.png")


# ==================== 步骤 2：拖素材到时间线 ====================
def drag_asset_to_timeline(page, editor_frame):
    log("\n=== 步骤2：拖素材到时间线 ===")

    ox, oy, iw, ih = get_iframe_offset(page, editor_frame)
    if iw == 0:
        raise RuntimeError("拿不到 iframe 尺寸，无法换算坐标")

    # 找素材
    asset_el = None
    imgs = editor_frame.locator("img")
    cnt = imgs.count()
    log(f"  iframe 内 img 总数: {cnt}")
    for i in range(cnt):
        el = imgs.nth(i)
        try:
            if el.is_visible():
                box = el.bounding_box()
                if box and box["x"] < 500:
                    asset_el = el
                    log(f"  选中素材 img[{i}] 相对 iframe pos=({box['x']:.0f},{box['y']:.0f})")
                    break
        except Exception:
            pass
    if asset_el is None:
        raise RuntimeError("找不到可拖拽的素材元素")

    a_box = asset_el.bounding_box()
    ax = a_box["x"] + a_box["width"] / 2
    ay = a_box["y"] + a_box["height"] / 2

    tx = iw * 0.4
    ty = ih * 0.85

    ax_page, ay_page = ox + ax, oy + ay
    tx_page, ty_page = ox + tx, oy + ty
    log(f"  拖拽(page坐标) ({ax_page:.0f},{ay_page:.0f}) → ({tx_page:.0f},{ty_page:.0f})")

    page.mouse.move(ax_page, ay_page)
    time.sleep(0.3)
    page.mouse.down()
    time.sleep(0.3)
    steps = 25
    for i in range(1, steps + 1):
        x = ax_page + (tx_page - ax_page) * i / steps
        y = ay_page + (ty_page - ay_page) * i / steps
        page.mouse.move(x, y)
        time.sleep(0.02)
    time.sleep(0.3)
    page.mouse.up()
    time.sleep(2.0)
    shot(page, "tc0002_after_drag.png")


# ==================== 步骤 3：选中时间线片段 ====================
def select_timeline_clip(page, editor_frame):
    log("\n=== 步骤3：选中时间线片段 ===")

    ox, oy, iw, ih = get_iframe_offset(page, editor_frame)
    if iw == 0:
        log("  [WARN] iframe 尺寸未知，跳过")
        return False

    try:
        info = editor_frame.evaluate("""() => {
            const vh = window.innerHeight, vw = window.innerWidth;
            const out = [];
            const all = document.querySelectorAll(
                'div, img, [class*="clip"], [class*="timeline"], [class*="track"]'
            );
            for (const el of all) {
                const r = el.getBoundingClientRect();
                if (r.width > 60 && r.height > 20 && r.top > vh * 0.6) {
                    out.push({x: r.left + r.width/2, y: r.top + r.height/2,
                              w: r.width, h: r.height});
                }
            }
            return out.slice(0, 10);
        }""")
        log(f"  候选片段(iframe内): {info}")
        if info:
            cand = sorted(info, key=lambda c: c["y"])[0]
            cx_page = ox + cand["x"]
            cy_page = oy + cand["y"]
            page.mouse.click(cx_page, cy_page)
            log(f"  点击片段(page坐标) ({cx_page:.0f},{cy_page:.0f})")
            time.sleep(1.5)
            shot(page, "tc0002_after_select.png")
            return True
    except Exception as e:
        log(f"  片段查找异常: {e}")

    log("  [WARN] 未命中片段，退化为点击时间线区域中部")
    page.mouse.click(ox + iw * 0.3, oy + ih * 0.85)
    time.sleep(1.5)
    return False


# ==================== 步骤 4：断言中间预览区 ====================
def assert_center(editor_frame):
    log("\n=== 步骤4：断言中间预览区 ===")
    if any(text_exists(editor_frame, t, timeout=REGION_TIMEOUT, exact=False)
           for t in CENTER_TEXTS):
        log("  ✅ 中间预览区命中")
        return True
    log("  ❌ 中间预览区未命中")
    return False


# ==================== 步骤 5：断言右侧属性面板 ====================
def assert_right(editor_frame):
    log("\n=== 步骤5：断言右侧属性面板 ===")
    found = [t for t in RIGHT_TEXTS if text_exists(editor_frame, t, timeout=2, exact=False)]
    log(f"  命中: {found}")
    ok = len(found) >= 3
    log(f"  {'✅' if ok else '❌'} 右侧属性面板（命中 ≥3）")
    return ok


# ==================== 主流程 ====================
def test_tc0002():
    log("=== TC0002：剪辑工作台-选中素材后的属性面板 ===")

    # 先启动 playwright + 连接，再做 preflight（因为 preflight 需要 page）
    if not is_cdp_ready():
        log("❌ CDP 未就绪，请确认帧境 AI 已带 --remote-debugging-port=9222 启动")
        sys.exit(1)

    pw, browser, page = connect()
    errors = []
    try:
        # 启动前检查
        preflight_check(page)

        # 步骤1：右键 → 加入剪辑
        right_click_node_and_open_clip(page)

        # 找 iframe
        editor_frame = find_editor_frame(page, timeout=OPEN_TIMEOUT)
        shot(page, "tc0002_workbench_opened.png")

        # 步骤2：拖素材到时间线
        drag_asset_to_timeline(page, editor_frame)

        # 步骤3：选中片段
        select_timeline_clip(page, editor_frame)

        # 步骤4：中间预览区
        if not assert_center(editor_frame):
            errors.append("中间预览区未显示素材画面")

        # 步骤5：右侧属性面板
        if not assert_right(editor_frame):
            errors.append("右侧属性面板未显示层级/位置/缩放/旋转")

        shot(page, "tc0002_final.png")

        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0002，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            log("=" * 60)
            raise AssertionError("TC0002 未通过")
        log("[PASS] TC0002 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0002_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0002()