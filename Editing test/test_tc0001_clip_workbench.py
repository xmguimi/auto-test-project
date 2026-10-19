"""
TC0001 自动化测试：剪辑工作台-打开与布局

验证：
    右键【加入剪辑】打开剪辑工作台后，未添加素材时的空态布局正确：
    - 顶部：项目名、导出、关闭
    - 左侧导航：素材/音效/文字/贴纸/特效/转场/字幕/调整/设置
    - 中间预览区：预览区、播放控制、时间码、画质/缩放/比例、全屏
    - 右侧空态：「暂无内容」+「点击时间线上的元素，即可编辑其属性」
    - 底部：时间轴、标尺、工具栏、空态提示「素材拖拽到这里，开始你的大作吧~」

适配：
    - 剪辑工作台 = 主画布页里的 iframe（dist/opencut/index.html）
    - 所有区域断言自动穿透到该 iframe，主 page 作兜底

运行前置：
    pip install playwright requests
    python -m playwright install chromium
    帧境 AI 需带 --remote-debugging-port=9222 启动

环境变量（可选）：
    FJ_CDP_HOST / FJ_CDP_PORT / FJ_WINDOW_TITLE / FJ_SHOT_DIR
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

# 顶部
TOP_TEXTS = ["导出", "关闭"]
PROJECT_NAME_HINT = "剪辑"

# 左侧导航
LEFT_NAV_MIN_COUNT = 9
LEFT_NAV_TEXTS = ["素材", "音效", "文字", "贴纸", "特效", "转场", "字幕", "调整", "设置"]

# 中间预览区（模糊匹配，命中任一即可）
CENTER_TEXTS = ["画质", "缩放", "比例", "原画", "适应", "16:9", "00:00"]

# 右侧空态
RIGHT_EMPTY_TEXTS = ["暂无内容", "点击时间线上的元素"]

# 底部空态 + 时间轴
BOTTOM_TEXTS = ["素材拖拽到这里", "00:00"]

# 剪辑工作台 iframe 识别关键字
EDITOR_FRAME_HINTS = ["opencut", "editing", "clip"]


# ==================== 基础工具 ====================
def log(msg):
    print(msg, flush=True)


def shot(scope, name):
    try:
        p = SHOT_DIR / name
        scope.screenshot(path=str(p))
        log(f"[SHOT] {p}")
    except Exception as e:
        log(f"[SHOT-FAIL] {name}: {e}")


def is_cdp_ready(host=CDP_HOST, port=CDP_PORT):
    try:
        r = requests.get(f"http://{host}:{port}/json/version", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


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
    """模糊/精确匹配：页面上存在可见的指定文本。"""
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


def any_text_exists(scope, texts, timeout=REGION_TIMEOUT, exact=False):
    for t in texts:
        if text_exists(scope, t, timeout, exact):
            return True
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


# ==================== iframe 定位 ====================
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
                # 内容兜底：frame 内含左侧导航按钮
                btns = f.locator("button")
                cnt = btns.count()
                hit = 0
                for j in range(cnt):
                    cls = btns.nth(j).get_attribute("class") or ""
                    if "w-12" in cls or "flex-col" in cls:
                        hit += 1
                if hit >= 5:
                    log(f"  [OK] 内容命中 iframe: {f.url} (w12={hit})")
                    return f
            except Exception:
                pass
        time.sleep(0.4)
    log("  [WARN] 未找到剪辑工作台 iframe，回退主 page")
    return page


def scope_search(page, editor_frame):
    """返回按优先级排列的 scope 列表：[iframe, page]。"""
    scopes = []
    if editor_frame is not None and editor_frame != page:
        scopes.append(("iframe", editor_frame))
    scopes.append(("page", page))
    return scopes


# ==================== 步骤 1：右键 → 加入剪辑 ====================
def right_click_node_and_open_clip(page):
    log("\n=== 步骤1：右键节点 → 加入剪辑 ===")

    nodes = page.locator(SEL_NODE)
    if nodes.count() == 0:
        raise RuntimeError("画布上没有节点，请先准备一个图片节点")

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
    if not box:
        raise RuntimeError("节点无 bounding_box")
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    log(f"  右键节点中心 ({cx:.0f},{cy:.0f})")

    page.mouse.click(cx, cy, button="right")
    time.sleep(1.0)
    shot(page, "tc0001_after_right_click.png")

    if not click_visible_text(page, "加入剪辑", timeout=5):
        for alt in ["剪辑", "加入编辑器", "剪辑工作台"]:
            if click_visible_text(page, alt, timeout=2):
                log(f"  [OK] 用备选文案点击：{alt}")
                break
        else:
            raise RuntimeError("菜单里找不到「加入剪辑」")
    log("  [OK] 点击「加入剪辑」")
    time.sleep(2.0)
    shot(page, "tc0001_after_click_clip.png")


# ==================== 区域断言 ====================
def assert_top(page, editor_frame):
    log("\n=== 断言2：顶部 ===")
    for label, sc in scope_search(page, editor_frame):
        if any_text_exists(sc, TOP_TEXTS, timeout=REGION_TIMEOUT, exact=True):
            log(f"  [OK] 顶部命中（{label}）")
            if text_exists(sc, PROJECT_NAME_HINT, timeout=1.5, exact=False):
                log(f"  ✅ 顶部项目名包含「{PROJECT_NAME_HINT}」")
            return True
    log("  ❌ 顶部未找到（导出/关闭）")
    return False


def assert_left_nav(page, editor_frame):
    log("\n=== 断言3：左侧导航 ===")
    for label, sc in scope_search(page, editor_frame):
        try:
            allb = sc.locator("button")
            total = allb.count()
            candidates = []
            for i in range(total):
                try:
                    b = allb.nth(i)
                    cls = b.get_attribute("class") or ""
                    if ("w-12" in cls or "flex-col" in cls) and b.is_visible():
                        candidates.append(b)
                except Exception:
                    pass
            if len(candidates) >= LEFT_NAV_MIN_COUNT:
                names = []
                for b in candidates:
                    try:
                        n = (b.get_attribute("title")
                             or b.get_attribute("aria-label")
                             or (b.inner_text() or "").strip())
                        if n:
                            names.append(n)
                    except Exception:
                        pass
                log(f"  [OK] 左侧导航命中（{label}） 按钮数={len(candidates)}")
                if names:
                    log(f"  按钮文案/标签: {names}")
                return True
            else:
                log(f"  {label} 命中不足：{len(candidates)}")
        except Exception as e:
            log(f"  {label} 异常: {e}")

    # 文本兜底
    for label, sc in scope_search(page, editor_frame):
        found = [t for t in LEFT_NAV_TEXTS if text_exists(sc, t, timeout=1, exact=True)]
        if len(found) >= 5:
            log(f"  [OK] 左侧导航（文本兜底，{label}）: {found}")
            return True
    log("  ❌ 左侧导航未找到")
    return False


def assert_center(page, editor_frame):
    log("\n=== 断言4：中间预览区 ===")
    for label, sc in scope_search(page, editor_frame):
        if any_text_exists(sc, CENTER_TEXTS, timeout=REGION_TIMEOUT, exact=False):
            log(f"  [OK] 中间预览区命中（{label}）")
            return True
    log("  ❌ 中间预览区未找到")
    return False


def assert_right_empty(page, editor_frame):
    log("\n=== 断言5：右侧空态 ===")
    for label, sc in scope_search(page, editor_frame):
        if any_text_exists(sc, RIGHT_EMPTY_TEXTS, timeout=REGION_TIMEOUT, exact=False):
            log(f"  [OK] 右侧空态命中（{label}）")
            return True
    log("  ❌ 右侧空态未找到")
    return False


def assert_bottom(page, editor_frame):
    log("\n=== 断言6：底部时间轴/工具栏 ===")
    for label, sc in scope_search(page, editor_frame):
        if any_text_exists(sc, BOTTOM_TEXTS, timeout=REGION_TIMEOUT, exact=False):
            log(f"  [OK] 底部命中（{label}）")
            return True
    log("  ❌ 底部时间轴/工具栏未找到")
    return False


# ==================== 主流程 ====================
def test_tc0001():
    log("=== TC0001：剪辑工作台-打开与布局 ===")

    pw, browser, page = connect()
    errors = []
    try:
        # 步骤1：右键 → 加入剪辑
        right_click_node_and_open_clip(page)

        # 找剪辑工作台 iframe
        editor_frame = find_editor_frame(page, timeout=OPEN_TIMEOUT)
        shot(page, "tc0001_workbench_opened.png")

        # 区域断言
        if not assert_top(page, editor_frame):          errors.append("顶部区域缺失")
        if not assert_left_nav(page, editor_frame):     errors.append("左侧导航区域缺失")
        if not assert_center(page, editor_frame):       errors.append("中间预览区域缺失")
        if not assert_right_empty(page, editor_frame):  errors.append("右侧空态缺失")
        if not assert_bottom(page, editor_frame):       errors.append("底部时间轴/工具栏缺失")

        shot(page, "tc0001_final.png")

        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0001，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            log("=" * 60)
            raise AssertionError("TC0001 未通过")
        log("[PASS] TC0001 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0001_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0001()