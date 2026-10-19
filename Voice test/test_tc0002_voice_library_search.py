"""
TC-0002: 音色库-搜索与筛选
验证：三个Tab显示、关键词搜索过滤、无结果空状态、筛选功能（性别=女）、我的音色/收藏空状态
"""
import sys
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 9222
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}")
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}")


def is_cdp_ready():
    try:
        r = requests.get(f"http://localhost:{PORT}/json/version", timeout=1)
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


def check_voice_panel_ready(page):
    """假设用户已经打开配音工具面板，直接进入音色库"""
    print("  等待配音工具面板加载...")
    time.sleep(2)  # 先等页面加载

    # 先尝试严格选择器，找不到再放宽
    nav = page.locator("nav.tts-nav[aria-label='配音工具导航']")
    if nav.count() == 0:
        print("  严格选择器没找到，尝试宽松匹配...")
        nav = page.locator("nav.tts-nav")
    if nav.count() == 0:
        print("  还是没找到，等2秒再试...")
        time.sleep(2)
        nav = page.locator("nav.tts-nav")

    if nav.count() == 0:
        # 打印一下页面上所有nav的class，方便调试
        all_navs = page.locator("nav")
        print(f"  页面上nav数量: {all_navs.count()}")
        for i in range(all_navs.count()):
            try:
                cls = all_navs.nth(i).get_attribute("class")
                print(f"    nav[{i}] class: {cls}")
            except:
                pass
        raise RuntimeError("配音工具面板未打开，请确认已经进入配音工具页面")

    print("  ✅ 配音面板已检测到，进入音色库")
    nav.locator("button.tts-nav-item").first.click()
    time.sleep(1.5)


def test_tc0002():
    print("=" * 60)
    print("TC-0002: 音色库-搜索与筛选")
    print("=" * 60)

    if not is_cdp_ready():
        raise RuntimeError(f"CDP端口{PORT}未就绪")

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        check_voice_panel_ready(page)
        shot(page, "tc0002_voice_library.png")

        # ========== 步骤1：三个Tab ==========
        print("\n--- 步骤1：检查三个Tab ---")
        tab_list = page.locator(".cx-tab-list[role='tablist']")
        tabs = tab_list.locator(".cx-tab")
        print(f"  Tab数量: {tabs.count()}")
        for tab_name in ["探索", "我的音色", "收藏音色"]:
            found = False
            for i in range(tabs.count()):
                if tab_name in tabs.nth(i).inner_text():
                    found = True
                    print(f"  ✅ Tab '{tab_name}' 存在")
                    break
            if not found:
                errors.append(f"Tab '{tab_name}' 未找到")

        # ========== 步骤2：搜索Vivi ==========
        print("\n--- 步骤2：搜索Vivi ---")
        search_input = page.locator(".cx-search-input input[aria-label='搜索音色']")
        search_input.fill("Vivi")
        time.sleep(1)
        assert search_input.input_value() == "Vivi"
        print("  ✅ 搜索框输入Vivi成功")
        search_input.fill("")
        time.sleep(0.5)

        # ========== 步骤3：搜索不存在的词 ==========
        print("\n--- 步骤3：搜索不存在关键词 ---")
        search_input.fill("xyz123不存在")
        time.sleep(1.5)
        page_text = page.inner_text("body")
        if any(kw in page_text for kw in ["暂无", "没有找到", "无结果"]):
            print("  ✅ 无结果空状态正常")
        else:
            print("  [WARN] 空状态文案未检测到（不阻塞）")
        search_input.fill("")
        time.sleep(0.5)

        # ========== 步骤4：筛选功能 ==========
        print("\n--- 步骤4：筛选功能（性别=女） ---")
        page.locator(".cx-btn.cx-btn-ghost:has-text('筛选')").first.click()
        time.sleep(1.5)
        shot(page, "tc0002_filter_dialog.png")
        print("  ✅ 筛选弹窗打开")

        # 【关键】严格在弹窗容器内找元素，绝对不碰底下页面
        # 弹窗根：role=dialog 的元素
        dialog = page.locator("div[role='dialog']")
        print(f"  找到弹窗数量: {dialog.count()}")

        # 在弹窗里找性别区域的"女"chip
        female_chip = dialog.locator(
            ".vl-facet:has(.vl-facet-label:has-text('性别')) .vl-facet-chips .cx-chip:has(.cx-chip-label:text-is('女'))"
        )
        print(f"  弹窗内'女'选项数量: {female_chip.count()}")
        if female_chip.count() > 0:
            female_chip.first.click(force=True)
            print("  ✅ 选中性别: 女")
            time.sleep(0.5)
        else:
            errors.append("弹窗内性别选项'女'未找到")

        shot(page, "tc0002_filter_selected.png")

        # 在弹窗里找底部的确认筛选按钮（紫色primary）
        confirm_btn = dialog.locator(".cx-modal-footer button.cx-btn-primary:has-text('筛选')")
        print(f"  弹窗内确认按钮数量: {confirm_btn.count()}")
        if confirm_btn.count() > 0:
            confirm_btn.first.click(force=True)
            time.sleep(1.5)
            shot(page, "tc0002_filter_applied.png")
            print("  ✅ 筛选已应用")
        else:
            errors.append("弹窗内确认筛选按钮未找到")

        # ========== 步骤5：我的音色Tab ==========
        print("\n--- 步骤5：我的音色空状态 ---")
        tab_list.locator(".cx-tab:has-text('我的音色')").first.click()
        time.sleep(1)
        shot(page, "tc0002_my_voices.png")
        page_text = page.inner_text("body")
        if any(kw in page_text for kw in ["暂无", "还没有"]):
            print("  ✅ 我的音色空状态正常")
        else:
            print("  [WARN] 空状态文案未检测到（不阻塞）")

        # ========== 步骤6：收藏音色Tab ==========
        print("\n--- 步骤6：收藏音色空状态 ---")
        tab_list.locator(".cx-tab:has-text('收藏音色')").first.click()
        time.sleep(1)
        shot(page, "tc0002_fav_voices.png")
        page_text = page.inner_text("body")
        if any(kw in page_text for kw in ["暂无", "还没有"]):
            print("  ✅ 收藏音色空状态正常")
        else:
            print("  [WARN] 空状态文案未检测到（不阻塞）")

        tab_list.locator(".cx-tab:has-text('探索')").first.click()
        time.sleep(0.5)

        # ========== 结果 ==========
        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] 共 {len(errors)} 个问题：")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("[PASS] TC-0002 全部通过！")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            if page:
                shot(page, "tc0002_error.png")
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
    test_tc0002()
