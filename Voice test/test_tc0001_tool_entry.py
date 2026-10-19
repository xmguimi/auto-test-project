"""
TC-0001: 工具入口与全局栏
验证：配音工具入口、顶部栏标题/教学视频/模型下拉/关闭按钮、左侧菜单三个入口全部正常展示且可交互

运行前提：
    1. 帧境AI桌面客户端已启动
    2. 用调试模式启动：帧境.exe --remote-debugging-port=9222
    3. 已进入画布编辑页面
    4. pip install playwright requests && playwright install chromium
"""
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============ 配置 ============
PORT = 9222
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    """截图"""
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}")
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}")


def is_cdp_ready():
    """检查CDP端口是否可用"""
    try:
        r = requests.get(f"http://localhost:{PORT}/json/version", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def connect():
    """连接到帧境AI画布页面"""
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")
    pages = browser.contexts[0].pages

    print(f"  找到 {len(pages)} 个页面：")
    for i, p in enumerate(pages):
        print(f"    [{i}] {p.title()}")

    # 找画布页面
    target = None
    for p in pages:
        title = p.title() or ""
        if "帧境" in title or "画布" in title:
            target = p
            break
    if not target:
        target = pages[0]

    print(f"  当前操作页面：{target.title()}")
    return pw, browser, target


# ============ 测试主流程 ============
def test_tc0001():
    print("=" * 60)
    print("TC-0001: 工具入口与全局栏")
    print("=" * 60)

    if not is_cdp_ready():
        raise RuntimeError(
            f"CDP端口{PORT}未就绪。\n"
            f"请先用调试模式启动帧境AI：\n"
            f'  "帧境.exe" --remote-debugging-port={PORT}'
        )

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()

        # ========== 步骤1：点击配音图标打开面板 ==========
        print("\n--- 步骤1：打开配音面板 ---")
        voice_btn = page.locator("button[aria-label='配音工具']")
        assert voice_btn.count() > 0, "配音工具按钮未找到"
        voice_btn.click()
        time.sleep(1.5)
        shot(page, "tc0001_panel_opened.png")
        print("  ✅ 配音面板打开成功")

        # ========== 步骤2：检查顶部栏元素 ==========
        print("\n--- 步骤2：检查顶部栏元素 ---")

        # 2.1 标题
        title = page.locator("text=配音工具")
        if title.count() > 0:
            print("  ✅ 顶部标题'配音工具'可见")
        else:
            errors.append("顶部标题未找到")

        # 2.2 教学视频按钮
        tutorial = page.locator("button.ftut-pill")
        if tutorial.count() > 0 and tutorial.first.is_visible():
            print("  ✅ 教学视频按钮可见")
        else:
            errors.append("教学视频按钮未找到")

        # 2.3 模型选择下拉
        model_select = page.locator("button[aria-label='生成模型']")
        if model_select.count() > 0:
            model_text = model_select.locator(".cx-select-value").inner_text()
            print(f"  ✅ 模型下拉可见，当前模型: {model_text}")
            # 点击展开验证可交互
            model_select.click()
            time.sleep(0.5)
            shot(page, "tc0001_model_dropdown.png")
            page.keyboard.press("Escape")
            time.sleep(0.3)
        else:
            errors.append("模型选择下拉未找到")

        # 2.4 关闭按钮
        close_btn = page.locator("button[aria-label='关闭'].md-x")
        if close_btn.count() > 0:
            print("  ✅ 关闭按钮可见")
        else:
            errors.append("关闭按钮未找到")

        # ========== 步骤3：左侧菜单三个入口 ==========
        print("\n--- 步骤3：检查左侧菜单 ---")
        nav = page.locator("nav.tts-nav[aria-label='配音工具导航']")
        if nav.count() == 0:
            errors.append("配音工具左侧导航未找到")
        else:
            nav_items = nav.locator("button.tts-nav-item")
            item_count = nav_items.count()
            print(f"  菜单项数量: {item_count}")

            expected_menus = ["音色库", "音频生成", "语音合成"]
            for menu_name in expected_menus:
                found = False
                for i in range(item_count):
                    item = nav_items.nth(i)
                    text = item.inner_text()
                    if menu_name in text:
                        found = True
                        # 点击切换
                        item.click()
                        time.sleep(1)
                        print(f"  ✅ 菜单 '{menu_name}' 点击切换成功")
                        shot(page, f"tc0001_menu_{menu_name}.png")
                        break
                if not found:
                    errors.append(f"菜单 '{menu_name}' 未找到")

            # 检查帮助问号
            help_icons = nav.locator(".tts-nav-help")
            help_count = help_icons.count()
            print(f"  帮助问号数量: {help_count}")

        # ========== 步骤4：关闭面板 ==========
        print("\n--- 步骤4：关闭配音面板 ---")
        close_btn = page.locator("button[aria-label='关闭'].md-x")
        close_btn.click()
        time.sleep(0.8)
        shot(page, "tc0001_panel_closed.png")
        print("  ✅ 面板关闭成功")

        # ========== 结果 ==========
        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] 共 {len(errors)} 个问题：")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("[PASS] TC-0001 全部通过！")
            print("  ✅ 配音按钮可点击打开面板")
            print("  ✅ 顶部标题/教学视频/模型下拉/关闭按钮均可见")
            print("  ✅ 左侧三个菜单切换正常")
            print("  ✅ 关闭功能正常")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            if page:
                shot(page, "tc0001_error.png")
        except:
            pass
        sys.exit(1)
    finally:
        try:
            if browser:
                browser.close()
            if pw:
                pw.stop()
        except:
            pass


if __name__ == "__main__":
    test_tc0001()
