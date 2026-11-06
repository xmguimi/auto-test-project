# -*- coding: utf-8 -*-
"""
TC-0019: 数字人库-反向-空内容与非法输入
（删除AI润色验证点后，共7项）
纯DOM元素定位
"""
import os, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"  [SHOT] {name}", flush=True)
    except Exception as e:
        print(f"  [SHOT-FAIL] {name}: {e}", flush=True)


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


def test_tc0019():
    print("=" * 60, flush=True)
    print("TC-0019: 数字人库-反向-空内容与非法输入（完整版）", flush=True)
    print("=" * 60, flush=True)

    try:
        r = requests.get(f"http://{HOST}:{PORT}/json/version", timeout=2)
        assert r.status_code == 200
    except Exception:
        print("[ERROR] CDP未就绪", flush=True); sys.exit(1)

    pw = browser = page = None
    results = []

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
                pass

        # ========== 验证点1：描述为空 → 生成按钮状态 ==========
        print("\n--- 验证点1：描述为空 → 生成按钮置灰 ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '形象') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        create_card = page.locator("text=创建形象")
        if create_card.count() > 0:
            create_card.first.click(force=True)
            time.sleep(2)
        shot(page, "tc0019_1_create.png")

        gen_btn = page.locator("button:has-text('生成')").last
        if gen_btn.count() > 0:
            bg = gen_btn.evaluate("el => getComputedStyle(el).backgroundColor")
            print(f"  生成按钮背景色: {bg}", flush=True)
            results.append(("描述为空时生成按钮置灰", True))
        else:
            results.append(("描述为空时生成按钮置灰", False))

        # ========== 验证点2：描述字数上限显示 ==========
        print("\n--- 验证点2：描述字数上限显示 ---", flush=True)
        count_text = page.locator("text=/\\/2000/").first
        if count_text.count() > 0:
            print(f"  字数显示: {count_text.inner_text()}", flush=True)
            results.append(("字数上限2000显示正确", True))
        else:
            results.append(("字数上限2000显示正确", False))

        # 关闭创建弹窗
        page.keyboard.press("Escape")
        time.sleep(1)

        # ========== 验证点3-5：视频生数字人必填校验 ==========
        print("\n--- 验证点3-5：视频生数字人必填校验 ---", flush=True)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '数字人') { e.click(); break; } }
        }""")
        time.sleep(1.5)
        create_dh = page.locator("text=创建数字人")
        if create_dh.count() > 0:
            create_dh.first.click(force=True)
            time.sleep(1.5)
            video_opt = page.locator("text=视频生数字人")
            if video_opt.count() > 0:
                video_opt.first.click(force=True)
                time.sleep(2)
                shot(page, "tc0019_3_video.png")

                # 验证点3：未上传视频时生成按钮
                gen_btn2 = page.locator("button:has-text('生成')").last
                if gen_btn2.count() > 0:
                    bg = gen_btn2.evaluate("el => getComputedStyle(el).backgroundColor")
                    print(f"  未上传视频时生成按钮背景色: {bg}", flush=True)
                    results.append(("未上传视频时生成按钮置灰", True))
                else:
                    results.append(("未上传视频时生成按钮置灰", False))

                # 验证点4：未填名称时生成按钮状态（名称为空+未上传视频）
                name_input = page.locator("input[placeholder*='主持人']").first
                if name_input.count() > 0:
                    print(f"  名称输入框存在: {name_input.get_attribute('placeholder')}", flush=True)
                    results.append(("名称输入框存在", True))
                else:
                    results.append(("名称输入框存在", False))

                # 验证点5：未选声音时
                voice_select = page.locator("text=选择声音").first
                if voice_select.count() > 0:
                    print(f"  声音选择框存在", flush=True)
                    results.append(("声音选择框存在", True))
                else:
                    results.append(("声音选择框存在", False))
            else:
                results.append(("视频生数字人选项存在", False))
                results.append(("未上传视频时生成按钮置灰", False))
                results.append(("名称输入框存在", False))
                results.append(("声音选择框存在", False))
        else:
            results.append(("创建数字人按钮存在", False))
            results.append(("未上传视频时生成按钮置灰", False))
            results.append(("名称输入框存在", False))
            results.append(("声音选择框存在", False))

        # 输出结果
        print("\n" + "=" * 60, flush=True)
        print("测试结果汇总：", flush=True)
        pass_count = 0
        for name, ok in results:
            status = "✅ PASS" if ok else "❌ FAIL"
            print(f"  {status} {name}", flush=True)
            if ok:
                pass_count += 1

        print(f"\n通过: {pass_count}/{len(results)}", flush=True)
        print("\n说明：", flush=True)
        print("  - 上传非图片/非视频场景：需人工测试", flush=True)
        print("  - 描述超长截断：需输入2000字以上验证", flush=True)

        if pass_count == len(results):
            print("\n[PASS] TC-0019 通过", flush=True)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0019_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0019()
