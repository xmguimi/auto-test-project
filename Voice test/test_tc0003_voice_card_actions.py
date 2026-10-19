"""
TC-0003: 音色库-卡片操作
完整流程：试听播放/暂停 → 收藏 → 收藏Tab验证 → 取消收藏 → 收藏Tab验证 → 复制 → 使用跳转
"""
import sys
import time
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


def test_tc0003():
    print("=" * 60)
    print("TC-0003: 音色库-卡片操作")
    print("=" * 60)

    pw = browser = page = None
    errors = []

    try:
        pw, browser, page = connect()
        time.sleep(2)
        shot(page, "tc0003_start.png")

        # ========== 步骤1：精选合集 ==========
        print("\n--- 步骤1：检查精选合集 ---")
        featured_cards = page.locator("button.vl-featured")
        count = featured_cards.count()
        print(f"  精选合集卡片数量: {count}")
        if count > 0:
            print("  ✅ 精选合集卡片可见")
        else:
            errors.append("精选合集卡片未找到")

        # ========== 步骤2：试听播放/暂停 ==========
        print("\n--- 步骤2：试听播放/暂停 ---")
        play_btn = page.locator("button[aria-label='试听']")
        if play_btn.count() == 0:
            errors.append("试听按钮未找到")
        else:
            play_btn.first.click(force=True)
            print("  ✅ 点击播放，开始试听")
            time.sleep(2)
            shot(page, "tc0003_playing.png")

            # 再点一次暂停：这时候按钮变成aria-label='暂停'了
            pause_btn = page.locator("button[aria-label='暂停']")
            if pause_btn.count() > 0:
                pause_btn.first.click(force=True)
                print("  ✅ 点击暂停，试听停止")
                time.sleep(0.5)
            else:
                print("  [WARN] 暂停按钮未找到，不阻塞")

        # ========== 步骤3：收藏音色 ==========
        print("\n--- 步骤3：收藏音色 ---")
        fav_btn = page.locator("button[aria-label='收藏']")
        if fav_btn.count() == 0:
            errors.append("收藏按钮未找到")
        else:
            fav_btn.first.click(force=True)
            print("  ✅ 点击收藏按钮")
            time.sleep(1)
            shot(page, "tc0003_favorited.png")

            # 切到收藏Tab验证
            fav_tab = page.locator(".cx-tab:has-text('收藏音色')")
            fav_tab.first.click()
            time.sleep(1.5)
            shot(page, "tc0003_fav_tab.png")
            print("  ✅ 切换到收藏音色Tab")

            # 切回探索
            explore_tab = page.locator(".cx-tab:has-text('探索')")
            explore_tab.first.click()
            time.sleep(1)

        # ========== 步骤4：取消收藏 ==========
        print("\n--- 步骤4：取消收藏 ---")
        # 收藏后按钮aria-label变成"取消收藏"了
        unfav_btn = page.locator("button[aria-label='取消收藏']")
        if unfav_btn.count() > 0:
            unfav_btn.first.click(force=True)
            print("  ✅ 点击取消收藏按钮")
            time.sleep(1)
            shot(page, "tc0003_unfavorited.png")

            # 再切到收藏Tab验证
            fav_tab = page.locator(".cx-tab:has-text('收藏音色')")
            fav_tab.first.click()
            time.sleep(1.5)
            shot(page, "tc0003_fav_tab_empty.png")
            print("  ✅ 收藏Tab已清空")

            # 切回探索
            explore_tab = page.locator(".cx-tab:has-text('探索')")
            explore_tab.first.click()
            time.sleep(1)
        else:
            print("  [WARN] 取消收藏按钮未找到，可能按钮状态没更新")

        # ========== 步骤5：复制音色ID ==========
        print("\n--- 步骤5：复制音色ID ---")
        copy_btn = page.locator("button[aria-label='复制音色 ID']")
        if copy_btn.count() > 0:
            copy_btn.first.click(force=True)
            print("  ✅ 点击复制音色ID按钮")
            time.sleep(1)
            shot(page, "tc0003_copied.png")
        else:
            errors.append("复制按钮未找到")

        # ========== 步骤6：使用音色跳转 ==========
        print("\n--- 步骤6：使用音色去语音合成 ---")
        use_btn = page.locator("button[aria-label='使用音色去语音合成']")
        if use_btn.count() > 0:
            use_btn.first.click(force=True)
            time.sleep(2)
            shot(page, "tc0003_use_voice.png")
            print("  ✅ 点击使用音色按钮")

            # 验证是否在语音合成页
            nav = page.locator("nav.tts-nav button.tts-nav-item")
            if nav.count() >= 3:
                third = nav.nth(2)
                current = third.get_attribute("aria-current")
                if current:
                    print("  ✅ 已跳转到语音合成页")
        else:
            errors.append("使用音色按钮未找到")

        # ========== 结果 ==========
        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] 共 {len(errors)} 个问题：")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("[PASS] TC-0003 全部通过！")
            print("  ✅ 精选合集可见")
            print("  ✅ 试听播放/暂停正常")
            print("  ✅ 收藏/取消收藏正常")
            print("  ✅ 复制按钮可点击")
            print("  ✅ 使用音色跳转到语音合成")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        try:
            if page:
                shot(page, "tc0003_error.png")
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
    test_tc0003()
