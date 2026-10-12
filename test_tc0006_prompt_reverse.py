import os
import sys
import re
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============ 配置区 ============
PORT = 9222
ROOT = Path(__file__).parent

_ABS_IMG = Path(r"D:\Desktop\自动化测试\auto-test-project\testdata\羊群.jpg")
_REL_IMG = ROOT / "testdata" / "羊群.jpg"
IMAGE_PATH = _ABS_IMG if _ABS_IMG.exists() else _REL_IMG

EXE_CANDIDATES = [
    r"F:\zhenjing\framerealm-canvas\帧境.exe",
    r"C:\Program Files\帧境AI\帧境.exe",
    r"C:\Program Files (x86)\帧境AI\帧境.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\帧境AI\帧境.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\framerealm-canvas\帧境.exe"),
]

REVERSE_TIMEOUT = 120
EXPECTED_KEYWORDS = ["羊", "群", "草地", "草原", "山坡", "牧场", "绵羊"]

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
def upload_image(page, image_path: Path):
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
    shot(page, "tc0006_after_upload.png")


def find_image_node(page):
    print("\n=== 查找图片节点 ===")
    loc = page.locator(".react-flow__node")
    n = loc.count()
    print(f"节点总数: {n}")
    if n == 0:
        raise RuntimeError("没有节点")
    return loc.nth(n - 1)


# ============ 右键菜单 ============
def right_click_node(page, node):
    print("\n=== 右键点击图片节点 ===")
    box = node.bounding_box()
    if not box:
        raise RuntimeError("节点 bounding_box 为空")

    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    print(f"节点中心: ({cx:.1f},{cy:.1f})")

    page.mouse.click(cx, cy)
    time.sleep(0.5)
    page.mouse.click(cx, cy, button="right")
    time.sleep(1)
    shot(page, "tc0006_after_right_click.png")


def click_menu_item(page, text_keyword):
    """
    点击右键菜单中包含指定文字的项。
    帧境右键菜单项 class 是 cm-item。
    """
    print(f"\n=== 点击菜单项：包含 '{text_keyword}' ===")

    candidates = [
        f".cm-item:has-text('{text_keyword}')",
        f"[class*='cm-item']:has-text('{text_keyword}')",
        f"[role='menuitem']:has-text('{text_keyword}')",
        f"[class*='menu-item']:has-text('{text_keyword}')",
        f"li:has-text('{text_keyword}')",
    ]

    for sel in candidates:
        try:
            loc = page.locator(sel)
            cnt = loc.count()
            if cnt == 0:
                continue
            print(f"  选择器 '{sel}' 命中 {cnt} 个")
            for i in range(cnt):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                    box = el.bounding_box()
                    if not box:
                        continue
                    print(f"    [{i}] 可见，box={box}")
                    el.click(timeout=3000)
                    print(f"  [OK] 已点击 '{text_keyword}'")
                    return True
                except Exception as e:
                    print(f"    [{i}] 点击失败: {e}")
        except Exception as e:
            print(f"  '{sel}' 失败: {e}")

    raise RuntimeError(f"找不到菜单项 '{text_keyword}'")


# ============ 等待新文本节点 ============
def wait_for_new_text_node(page, nodes_before, timeout=REVERSE_TIMEOUT):
    """
    等待反推生成的新节点出现，并读取内容。
    """
    print(f"\n=== 等待反推结果（最多 {timeout}s） ===")
    print(f"点击前节点数: {nodes_before}")

    start = time.time()
    last_text = ""
    stable_count = 0

    while time.time() - start < timeout:
        cur_count = page.locator(".react-flow__node").count()
        elapsed = time.time() - start

        if cur_count > nodes_before:
            new_node = page.locator(".react-flow__node").nth(cur_count - 1)
            try:
                text = (new_node.inner_text() or "").strip()
            except Exception:
                text = ""

            if text:
                print(f"[{elapsed:.1f}s] 节点数={cur_count}，最后节点文本长度={len(text)}")
                if text == last_text:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_text = text

                if stable_count >= 2 and len(text) > 10:
                    print(f"[OK] 反推结果稳定（{elapsed:.1f}s）")
                    return new_node, text
            else:
                print(f"[{elapsed:.1f}s] 节点数={cur_count}，最后节点文本为空，继续等...")
        else:
            if int(elapsed) % 5 == 0:
                print(f"[{elapsed:.1f}s] 节点数={cur_count}，还没新节点...")

        time.sleep(1)

    print(f"[WARN] {timeout}s 内未拿到结果")
    cur_count = page.locator(".react-flow__node").count()
    if cur_count > nodes_before:
        new_node = page.locator(".react-flow__node").nth(cur_count - 1)
        try:
            text = (new_node.inner_text() or "").strip()
            print(f"兜底取到的文本: {text[:200]}")
            return new_node, text
        except Exception as e:
            print(f"兜底读取失败: {e}")
    return None, ""


def dump_nodes_summary(page):
    print("\n=== 当前所有节点信息 ===")
    nodes = page.locator(".react-flow__node")
    n = nodes.count()
    print(f"节点总数: {n}")
    for i in range(n):
        try:
            t = (nodes.nth(i).inner_text() or "").strip().replace("\n", " ")
            print(f"  [{i}] {t[:80]}")
        except Exception as e:
            print(f"  [{i}] 读取失败: {e}")


# ============ 断言 ============
def assert_prompt_result(prompt_text: str):
    print("\n=== 断言反推结果 ===")

    assert prompt_text, "反推结果为空"
    print(f"  结果长度: {len(prompt_text)}")
    print(f"  结果内容: {prompt_text[:300]}")
    assert len(prompt_text) >= 10, f"结果过短: {prompt_text}"

    matched = [kw for kw in EXPECTED_KEYWORDS if kw in prompt_text]
    print(f"  匹配关键词: {matched}")
    assert matched, (
        f"结果与图片场景不符。期望含 {EXPECTED_KEYWORDS} 之一，"
        f"实际: {prompt_text[:200]}"
    )

    bad_pattern = re.compile(r"[�]{1,}|[\x00-\x08\x0b-\x0c\x0e-\x1f]")
    assert not bad_pattern.search(prompt_text), f"结果含乱码: {prompt_text[:200]}"

    error_words = ["失败", "错误", "error", "fail", "timeout", "超时"]
    lower = prompt_text.lower()
    for w in error_words:
        if w in lower:
            raise AssertionError(f"结果含错误提示 '{w}': {prompt_text[:200]}")

    print("[PASS] 反推结果断言通过")


# ============ 主流程 ============
def test_prompt_reverse():
    """TC-0006：图片节点右键 → 提示词反推"""

    if not IMAGE_PATH.exists():
        print(f"[ERROR] 找不到测试图片: {IMAGE_PATH}")
        sys.exit(1)
    print(f"[OK] 测试图片: {IMAGE_PATH}")

    exe = find_exe()
    print(f"[OK] 帧境AI 路径: {exe}")
    ensure_app_running(exe)

    pw, browser, page = connect_to_frame_realm()

    try:
        print(f"\n页面 URL: {page.url}")
        shot(page, "tc0006_connected.png")

        upload_image(page, IMAGE_PATH)

        nodes_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 上传后节点数（基准）: {nodes_before}")
        dump_nodes_summary(page)

        image_node = find_image_node(page)

        right_click_node(page, image_node)

        click_menu_item(page, "提示词反推")
        time.sleep(1.5)
        shot(page, "tc0006_after_click_reverse.png")

        new_node, prompt_text = wait_for_new_text_node(page, nodes_before)
        shot(page, "tc0006_after_result.png")

        if not prompt_text:
            print("\n[INFO] 未拿到结果，打印当前所有节点供排查：")
            dump_nodes_summary(page)
            raise RuntimeError("反推结果为空或超时")

        assert_prompt_result(prompt_text)

        print("\n=== TC-0006 测试通过 ===")
        print(f"反推结果: {prompt_text[:300]}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            shot(page, "tc0006_error.png")
            dump_nodes_summary(page)
        except Exception:
            pass
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_prompt_reverse()