# -*- coding: utf-8 -*-
"""
TC-0016: 视频生数字人-页面与参数
实际测试：上传视频、填名称、选声音
纯DOM元素定位 + pyautogui处理系统文件对话框
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

try:
    import pyautogui
    import pyperclip
    PYGUI_OK = True
except ImportError:
    PYGUI_OK = False

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)
VIDEO_PATH = r"D:\Desktop\自动化测试\auto-test-project\testdata\牛来啦.mp4"


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


def native_open_file(file_path, wait_dialog=3.0):
    """处理Windows原生文件对话框：粘贴路径回车"""
    if not PYGUI_OK:
        raise RuntimeError("缺少 pyautogui/pyperclip")
    print(f"  [NATIVE] 等待文件对话框({wait_dialog}s)，准备: {file_path}", flush=True)
    time.sleep(wait_dialog)
    # 先按Tab切换焦点到文件名输入框
    for _ in range(3):
        pyautogui.press("tab")
        time.sleep(0.1)
    # 复制路径
    pyperclip.copy(file_path)
    time.sleep(0.5)
    # 全选再粘贴
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1.0)
    pyautogui.press("enter")
    print("  [NATIVE] 已粘贴路径并回车", flush=True)
    time.sleep(5)


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    target = None
    for p in browser.contexts[0].pages:
        if "帧境" in (p.title() or ""):
            target = p
            break
    if not target:
        target = browser.contexts[0].pages[0]
    return pw, browser, target


def test_tc0016():
    print("=" * 60, flush=True)
    print("TC-0016: 视频生数字人页面与参数", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200
    except Exception:
        print("[ERROR] CDP未就绪", flush=True); sys.exit(1)

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        time.sleep(2)

        # 步骤0：进入项目
        print("\n--- 步骤0：进入项目 ---", flush=True)
        project = page.locator("text=剪辑测试")
        if project.count() > 0:
            try:
                project.first.click(force=True, timeout=3000)
                time.sleep(6)
            except:
                print("  [INFO] 已在项目中", flush=True)

        # 步骤1：进入视频生页面
        print("\n--- 步骤1：进入视频生页面 ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '数字人') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        create_btn = page.locator("text=创建数字人")
        if create_btn.count() > 0:
            create_btn.first.click(force=True)
            time.sleep(1.5)
        video_btn = page.locator("text=视频生数字人")
        if video_btn.count() > 0:
            video_btn.first.click(force=True)
            time.sleep(2)
        shot(page, "tc0016_page.png")

        # 步骤2：上传视频
        print("\n--- 步骤2：上传视频 ---", flush=True)
        choose_btn = page.locator("text=选择本地视频")
        if choose_btn.count() > 0:
            choose_btn.first.click(force=True)
            print("  [DEBUG] 已点选择本地视频，等2秒", flush=True)
            time.sleep(2)
            # 截屏看看文件对话框弹出来没有
            try:
                screenshot = pyautogui.screenshot()
                screenshot.save(str(SHOT_DIR / "tc0016_dialog_screen.png"))
                print("  [DEBUG] 已截屏当前屏幕", flush=True)
            except Exception as e:
                print(f"  [DEBUG] 截屏失败: {e}", flush=True)
            # 用pyautogui粘贴路径
            native_open_file(VIDEO_PATH, wait_dialog=0.0)
            time.sleep(5)
            print("  ✅ 已尝试上传视频", flush=True)
            shot(page, "tc0016_uploaded.png")
        else:
            errors.append("选择本地视频按钮未找到")

        # 步骤3：填名称
        print("\n--- 步骤3：填名称 ---", flush=True)
        name_input = page.locator("input:not([type='file'])")
        if name_input.count() > 0:
            name_input.first.click(force=True)
            time.sleep(0.3)
            page.keyboard.type("小王")
            time.sleep(0.5)
            print("  ✅ 已填名称：小王", flush=True)
        else:
            errors.append("名称输入框未找到")

        # 步骤4：选声音
        print("\n--- 步骤4：选声音 ---", flush=True)
        sound_select = page.locator("text=选择声音")
        if sound_select.count() > 0:
            sound_select.first.click(force=True)
            time.sleep(1)
            wise_voice = page.locator("text=智慧女声")
            if wise_voice.count() > 0:
                wise_voice.first.click(force=True)
                time.sleep(0.5)
                print("  ✅ 已选声音：智慧女声", flush=True)
            else:
                errors.append("智慧女声未找到")
        else:
            errors.append("声音选择框未找到")

        shot(page, "tc0016_filled.png")
        print("\n" + "=" * 60, flush=True)
        if errors:
            print(f"[FAIL] {len(errors)}项:", flush=True)
            [print(f"  - {e}", flush=True) for e in errors]
            sys.exit(1)
        print("[PASS] TC-0016 通过", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0016_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0016()
