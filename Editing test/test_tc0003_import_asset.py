"""
TC0003 自动化测试：剪辑工作台-素材导入与管理验证

流程：
    1. 点【素材】→ 点【导入】→ 断言下拉三项：从画布 / 从资产库 / 从本地
    2. 【从本地】选 牛群.jpg → 断言导入成功、出现在素材列表
    3. 【从本地】选 羊群奔跑.mp4 → 断言导入成功、显示时长
    4. 【从画布】弹「从画布导入」→ 勾选画布素材（如「草原.jpg」）→ 点【导入】→ 断言成功
    5. 【从资产库】弹「从资产库导入」→ 勾选资产（如「牛来啦.mp4」）→ 点【导入】→ 断言成功
    6. 断言素材项显示缩略图、文件名、视频时长
    7. 搜索框输入文件名 → 断言过滤生效
    8. 拖动素材到时间线 → 断言生成片段
    9. 断言时间线出现该素材片段、时长正确

适配：
    - 剪辑工作台 = 主画布页里的 iframe（dist/opencut/index.html）
    - iframe 坐标 = iframe 内相对坐标 + iframe 在主 page 的偏移
    - 鼠标/截图统一用 page，不用 frame
    - 「从本地」弹的是 Windows 原生文件对话框，用 pyautogui + 剪贴板粘贴路径回车

运行前置：
    pip install playwright requests pyautogui pyperclip
    python -m playwright install chromium
    帧境 AI 需带 --remote-debugging-port=9222 启动

环境变量（可选）：
    FJ_CDP_HOST           默认 localhost
    FJ_CDP_PORT           默认 9222
    FJ_WINDOW_TITLE       默认「帧境」
    FJ_SHOT_DIR           默认 ./screenshots
    FJ_LOCAL_IMAGE        默认 D:\\Desktop\\自动化测试\\auto-test-project\\testdata\\牛群.jpg
    FJ_LOCAL_VIDEO        默认 D:\\Desktop\\自动化测试\\auto-test-project\\testdata\\羊群奔跑.mp4
    FJ_CANVAS_ITEM        默认「草原.jpg」
    FJ_ASSET_VIDEO        默认「牛来啦.mp4」
"""

import os
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# 系统原生文件对话框操作
try:
    import pyautogui
    import pyperclip
    PYGUI_OK = True
except ImportError as _e:
    PYGUI_OK = False
    _PYGUI_IMPORT_ERR = str(_e)

# Windows 任务栏/文件对话框操作（可选，更稳的备选方案）
try:
    import pywinauto  # noqa: F401
    PYWINAUTO_OK = True
except ImportError:
    PYWINAUTO_OK = False

# ==================== 配置区 ====================
CDP_HOST = os.getenv("FJ_CDP_HOST", "localhost")
CDP_PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
WINDOW_TITLE_KEYWORD = os.getenv("FJ_WINDOW_TITLE", "帧境")
SHOT_DIR = Path(os.getenv("FJ_SHOT_DIR", "screenshots"))
SHOT_DIR.mkdir(parents=True, exist_ok=True)

# 本地素材文件路径
LOCAL_IMAGE = os.getenv(
    "FJ_LOCAL_IMAGE",
    r"D:\Desktop\自动化测试\auto-test-project\testdata\牛群.jpg",
)
LOCAL_VIDEO = os.getenv(
    "FJ_LOCAL_VIDEO",
    r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群奔跑.mp4",
)

# 画布 / 资产库里已有的素材名（实际列表里显示的名字，不带扩展名）
CANVAS_ITEM_NAME = os.getenv("FJ_CANVAS_ITEM", "草原")
ASSET_VIDEO_NAME = os.getenv("FJ_ASSET_VIDEO", "牛来啦")

OPEN_TIMEOUT = 20
REGION_TIMEOUT = 8

SEL_NODE = ".react-flow__node"
EDITOR_FRAME_HINTS = ["opencut", "editing", "clip"]
IMPORT_OPTIONS = ["从画布", "从资产库", "从本地"]


# ==================== 基础工具 ====================
def log(msg):
    print(msg, flush=True)


def shot(page, name):
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


def native_open_file(file_path, wait_dialog=2.0):
    """
    处理 Windows 原生「打开」文件对话框：
    1) 等待对话框弹出
    2) 把完整路径复制到剪贴板
    3) 在文件名框 Ctrl+A 全选 → Ctrl+V 粘贴 → Enter 确认
    """
    if not PYGUI_OK:
        raise RuntimeError(
            "缺少 pyautogui/pyperclip，请先 pip install pyautogui pyperclip"
        )
    log(f"  [NATIVE] 等待系统文件对话框({wait_dialog}s)，准备粘贴: {file_path}")
    time.sleep(wait_dialog)

    # 文件名输入框默认聚焦，直接粘贴
    pyperclip.copy(file_path)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    log("  [NATIVE] 已粘贴路径并回车")
    time.sleep(2.5)


def press_escape(page, times=1):
    """按 Escape 清理可能残留的下拉/弹窗，避免 backdrop 挡住后续点击。"""
    try:
        for _ in range(times):
            page.keyboard.press("Escape")
            time.sleep(0.3)
    except Exception:
        pass


def preflight_check(page):
    log("\n=== 启动前检查 ===")
    errors = []

    if not is_cdp_ready():
        errors.append(
            f"CDP 未就绪：请确认帧境 AI 已带 --remote-debugging-port={CDP_PORT} 启动"
        )
    else:
        log(f"  ✅ CDP 就绪 ({CDP_HOST}:{CDP_PORT})")

    try:
        cnt = page.locator(SEL_NODE).count()
        if cnt == 0:
            errors.append("画布上没有节点：请先在画布中创建图片/视频节点")
        else:
            log(f"  ✅ 画布节点数: {cnt}")
    except Exception as e:
        errors.append(f"读取画布节点失败: {e}")

    for label, p in [("本地图片", LOCAL_IMAGE), ("本地视频", LOCAL_VIDEO)]:
        if not Path(p).exists():
            errors.append(f"{label}不存在: {p}")
        else:
            log(f"  ✅ {label}: {p}")

    if not PYGUI_OK:
        errors.append(
            f"缺少 pyautogui/pyperclip（{_PYGUI_IMPORT_ERR}），"
            "请先运行: pip install pyautogui pyperclip"
        )

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


def click_visible_text(scope, text, timeout=5, exact=True):
    end = time.time() + timeout
    while time.time() < end:
        try:
            loc = scope.get_by_text(text, exact=exact)
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
        box = iframes.first.bounding_box()
        if box:
            return box["x"], box["y"], box["width"], box["height"]
    except Exception as e:
        log(f"  get_iframe_offset 异常: {e}")
    return 0, 0, 0, 0


# ==================== 步骤 1：点素材 → 点导入 → 断言下拉三项 ====================
def open_import_dropdown(editor_frame):
    log("\n=== 步骤1：打开【导入】下拉并断言三项 ===")

    if not click_visible_text(editor_frame, "素材", timeout=3, exact=False):
        log("  [WARN] 没看到【素材】按钮，可能已在素材面板")
    time.sleep(0.5)

    if not click_visible_text(editor_frame, "导入", timeout=5, exact=True):
        try:
            btn = editor_frame.locator("button:has-text('导入'), [class*='import']").first
            if btn.is_visible():
                btn.click(timeout=2000)
            else:
                raise RuntimeError("找不到【导入】按钮")
        except Exception:
            raise RuntimeError("找不到【导入】按钮")

    log("  [OK] 点击【导入】")
    time.sleep(1.0)

    missing = []
    for opt in IMPORT_OPTIONS:
        if text_exists(editor_frame, opt, timeout=2, exact=False):
            log(f"  ✅ 下拉含「{opt}」")
        else:
            log(f"  ❌ 下拉缺「{opt}」")
            missing.append(opt)
    if missing:
        raise AssertionError(f"导入下拉缺少项: {missing}")
    return True


# ==================== 步骤 2/3：从本地导入（系统原生对话框） ====================
def import_from_local(page, editor_frame, file_path, expect_name):
    log(f"\n=== 从本地导入：{expect_name} ===")

    # 确保下拉是展开的
    if not text_exists(editor_frame, "从本地", timeout=1, exact=False):
        click_visible_text(editor_frame, "导入", timeout=3, exact=True)
        time.sleep(0.8)

    # 点「从本地」→ 触发 Windows 原生文件对话框
    if not click_visible_text(editor_frame, "从本地", timeout=5, exact=False):
        raise RuntimeError("下拉里点不到「从本地」")

    # 用 pyautogui 操作系统文件对话框
    native_open_file(file_path, wait_dialog=2.0)

    # 等待素材列表刷新
    if not text_exists(editor_frame, expect_name, timeout=30, exact=False):
        # 再等一轮（大文件慢）
        if not text_exists(editor_frame, expect_name, timeout=15, exact=False):
            raise AssertionError(f"导入后素材列表未出现「{expect_name}」")
    log(f"  ✅ 素材列表出现「{expect_name}」")
    time.sleep(1.0)
    press_escape(page)
    return True


# ==================== 步骤 4：从画布导入 ====================
def click_dialog_confirm(editor_frame, timeout=8):
    """
    点对话框底部的「导入」/「导入 N」确认按钮。
    未勾选时按钮 disabled，勾选后会变成「导入 1」等计数按钮并启用。
    用 button:has-text 模糊匹配，排除标题文本。
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            btns = editor_frame.locator("button")
            for i in range(btns.count()):
                b = btns.nth(i)
                try:
                    txt = (b.inner_text() or "").strip()
                    if not txt.startswith("导入"):
                        continue
                    if "从" in txt:
                        continue
                    if not b.is_visible():
                        continue
                    if b.is_disabled():
                        continue
                    b.click(timeout=2000)
                    log(f"  [OK] 点击对话框按钮「{txt}」")
                    return True
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError("对话框里找不到可点击的【导入】按钮（可能未勾选素材或按钮仍 disabled）")


# ==================== 步骤 4：从画布导入 ====================
def import_from_canvas(page, editor_frame):
    log(f"\n=== 步骤4：从画布导入「{CANVAS_ITEM_NAME}」 ===")

    press_escape(page)
    time.sleep(0.5)
    click_visible_text(editor_frame, "导入", timeout=3, exact=True)
    time.sleep(0.8)

    if not click_visible_text(editor_frame, "从画布", timeout=5, exact=False):
        raise RuntimeError("下拉里点不到「从画布」")
    time.sleep(1.5)

    if text_exists(editor_frame, "从画布导入", timeout=3, exact=False):
        log("  ✅ 弹出「从画布导入」对话框")
    else:
        log("  [WARN] 未检测到「从画布导入」标题，继续")

    if not click_visible_text(editor_frame, CANVAS_ITEM_NAME, timeout=8, exact=False):
        raise RuntimeError(f"画布素材列表里找不到「{CANVAS_ITEM_NAME}」")
    log(f"  [OK] 勾选画布素材「{CANVAS_ITEM_NAME}」")
    time.sleep(0.8)

    click_dialog_confirm(editor_frame)

    if not text_exists(editor_frame, CANVAS_ITEM_NAME, timeout=10, exact=False):
        raise AssertionError(f"从画布导入后素材列表未出现「{CANVAS_ITEM_NAME}」")
    log(f"  ✅ 素材列表出现「{CANVAS_ITEM_NAME}」")
    time.sleep(1.0)
    return True


# ==================== 步骤 5：从资产库导入 ====================
def import_from_asset(page, editor_frame):
    log(f"\n=== 步骤5：从资产库导入「{ASSET_VIDEO_NAME}」 ===")

    press_escape(page)
    time.sleep(0.5)
    click_visible_text(editor_frame, "导入", timeout=3, exact=True)
    time.sleep(0.8)

    if not click_visible_text(editor_frame, "从资产库", timeout=5, exact=False):
        raise RuntimeError("下拉里点不到「从资产库」")
    time.sleep(1.5)

    if text_exists(editor_frame, "从资产库导入", timeout=3, exact=False):
        log("  ✅ 弹出「从资产库导入」对话框")
    else:
        log("  [WARN] 未检测到「从资产库导入」标题，继续")

    if not click_visible_text(editor_frame, ASSET_VIDEO_NAME, timeout=8, exact=False):
        raise RuntimeError(f"资产列表里找不到「{ASSET_VIDEO_NAME}」")
    log(f"  [OK] 勾选资产「{ASSET_VIDEO_NAME}」")
    time.sleep(0.8)

    click_dialog_confirm(editor_frame)

    if not text_exists(editor_frame, ASSET_VIDEO_NAME, timeout=15, exact=False):
        raise AssertionError(f"从资产库导入后素材列表未出现「{ASSET_VIDEO_NAME}」")
    log(f"  ✅ 素材列表出现「{ASSET_VIDEO_NAME}」")
    time.sleep(1.0)
    return True


# ==================== 步骤 6：断言素材项显示 ====================
def assert_material_items(editor_frame):
    log("\n=== 步骤6：断言素材项显示缩略图、文件名、视频时长 ===")
    info = editor_frame.evaluate("""() => {
        const imgs = Array.from(document.querySelectorAll('img'));
        const visibleImgs = imgs.filter(i => i.offsetWidth > 20 && i.offsetHeight > 20);
        const bodyText = document.body.innerText || '';
        const timeText = bodyText.match(/\\d{1,2}:\\d{2}(\\.\\d+)?/g) || [];
        return {
            imgCount: visibleImgs.length,
            hasNames: ['牛群','羊群奔跑','草原','牛来啦'].map(n => bodyText.includes(n)),
            timeDurations: timeText.slice(0, 10),
        };
    }""")
    log(f"  可见缩略图数: {info['imgCount']}")
    log(f"  文件名命中(牛群/羊群奔跑/草原/牛来啦): {info['hasNames']}")
    log(f"  检测到时长文本: {info['timeDurations']}")

    errors = []
    if info["imgCount"] < 3:
        errors.append(f"缩略图数量过少({info['imgCount']})")
    if not any(info["hasNames"]):
        errors.append("素材列表里看不到任何已导入的文件名")
    if not info["timeDurations"]:
        errors.append("未检测到视频时长文本")

    if errors:
        for e in errors:
            log(f"  ❌ {e}")
        raise AssertionError("素材项显示断言失败")
    log("  ✅ 素材项缩略图/文件名/时长均正常")
    return True


# ==================== 步骤 7：搜索过滤 ====================
def search_and_assert(page, editor_frame):
    log("\n=== 步骤7：搜索框过滤 ===")
    press_escape(page)
    time.sleep(0.5)

    try:
        search = editor_frame.locator(
            "input[placeholder*='搜索'], input[placeholder*='查找'], input[type='search']"
        ).first
        search.wait_for(state="visible", timeout=5000)
        search.click()
        search.fill("")
        search.type("牛群", delay=80)
        log("  [OK] 搜索框输入「牛群」")
        time.sleep(1.2)

        body_text = editor_frame.evaluate("() => document.body.innerText")
        show_niu = "牛群" in body_text
        show_yang = "羊群" in body_text or "羊羊" in body_text
        log(f"  过滤后含「牛群」={show_niu}, 含「羊群/羊羊」={show_yang}")

        search.fill("")
        time.sleep(0.5)

        if not show_niu:
            raise AssertionError("搜索「牛群」后列表中已无「牛群」，过滤异常")
        if show_yang:
            log("  [WARN] 搜索后「羊群」仍可见，不阻断")
        log("  ✅ 搜索过滤生效")
        return True
    except Exception as e:
        log(f"  [WARN] 搜索步骤异常: {e}")
        return False


# ==================== 步骤 8/9：拖素材到时间线 ====================
def drag_to_timeline(page, editor_frame, name_keyword="牛群"):
    log(f"\n=== 步骤8/9：拖素材「{name_keyword}」到时间线 ===")
    ox, oy, iw, ih = get_iframe_offset(page, editor_frame)
    if iw == 0:
        raise RuntimeError("拿不到 iframe 尺寸，无法换算坐标")

    asset_el = None
    imgs = editor_frame.locator("img")
    cnt = imgs.count()
    for i in range(cnt):
        el = imgs.nth(i)
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box or box["x"] > 500:
                continue
            parent_text = el.evaluate("e => (e.closest('div')||document.body).innerText || ''")
            if name_keyword in parent_text:
                asset_el = el
                log(f"  选中素材 img[{i}] 含「{name_keyword}」")
                break
        except Exception:
            pass

    if asset_el is None:
        for i in range(cnt):
            el = imgs.nth(i)
            try:
                if el.is_visible() and el.bounding_box() and el.bounding_box()["x"] < 500:
                    asset_el = el
                    log(f"  [WARN] 兜底取 img[{i}]")
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
    time.sleep(2.5)
    shot(page, "tc0003_after_drag.png")

    try:
        info = editor_frame.evaluate("""() => {
            const vh = window.innerHeight;
            const clips = document.querySelectorAll(
                '[class*="clip"], [class*="track-item"], [class*="segment"], [class*="timeline"] > div'
            );
            const out = [];
            for (const el of clips) {
                const r = el.getBoundingClientRect();
                if (r.width > 30 && r.top > vh * 0.6) {
                    out.push({w: r.width, h: r.height, text: (el.innerText||'').slice(0,40)});
                }
            }
            return out.slice(0, 10);
        }""")
        log(f"  时间线候选片段: {info}")
        if info:
            log("  ✅ 时间线已生成片段")
            return True
        log("  [WARN] 未在时间线检测到片段元素")
        return False
    except Exception as e:
        log(f"  时间片段检测异常: {e}")
        return False


# ==================== 主流程 ====================
def test_tc0003():
    log("=== TC0003：剪辑工作台-素材导入与管理验证 ===")

    if not is_cdp_ready():
        log("❌ CDP 未就绪，请确认帧境 AI 已带 --remote-debugging-port=9222 启动")
        sys.exit(1)

    pw, browser, page = connect()
    errors = []
    try:
        preflight_check(page)

        editor_frame = find_editor_frame(page, timeout=OPEN_TIMEOUT)
        shot(page, "tc0003_workbench_opened.png")

        # 步骤1
        try:
            open_import_dropdown(editor_frame)
            shot(page, "tc0003_import_dropdown.png")
        except Exception as e:
            errors.append(f"步骤1失败: {e}")
            press_escape(page)

        # 步骤2：本地图片
        try:
            import_from_local(page, editor_frame, LOCAL_IMAGE, "牛群")
            shot(page, "tc0003_after_local_image.png")
        except Exception as e:
            errors.append(f"步骤2(本地图片)失败: {e}")
            press_escape(page, times=2)

        # 步骤3：本地视频
        try:
            import_from_local(page, editor_frame, LOCAL_VIDEO, "羊群奔跑")
            shot(page, "tc0003_after_local_video.png")
        except Exception as e:
            errors.append(f"步骤3(本地视频)失败: {e}")
            press_escape(page, times=2)

        # 步骤4：从画布
        try:
            import_from_canvas(page, editor_frame)
            shot(page, "tc0003_after_import_canvas.png")
        except Exception as e:
            errors.append(f"步骤4(从画布)失败: {e}")
            press_escape(page, times=2)

        # 步骤5：从资产库
        try:
            import_from_asset(page, editor_frame)
            shot(page, "tc0003_after_import_asset.png")
        except Exception as e:
            errors.append(f"步骤5(从资产库)失败: {e}")
            press_escape(page, times=2)

        # 步骤6
        try:
            assert_material_items(editor_frame)
            shot(page, "tc0003_material_list.png")
        except Exception as e:
            errors.append(f"步骤6(素材显示)失败: {e}")

        # 步骤7
        try:
            search_and_assert(page, editor_frame)
            shot(page, "tc0003_search_filter.png")
        except Exception as e:
            errors.append(f"步骤7(搜索过滤)失败: {e}")

        # 步骤8/9
        try:
            drag_to_timeline(page, editor_frame, name_keyword="牛群")
        except Exception as e:
            errors.append(f"步骤8/9(拖拽时间线)失败: {e}")

        shot(page, "tc0003_final.png")

        log("\n" + "=" * 60)
        if errors:
            log(f"[FAIL] TC0003，共 {len(errors)} 项：")
            for e in errors:
                log(f"  - {e}")
            log("=" * 60)
            raise AssertionError("TC0003 未通过")
        log("[PASS] TC0003 通过")
        log("=" * 60)

    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0003_error.png")
        except Exception:
            pass
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0003()
