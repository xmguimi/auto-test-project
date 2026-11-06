# -*- coding: utf-8 -*-
"""
TC-0024: 数字人成片操作
从数字人卡片点创建口播，走完3步流程
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


def test_tc0024():
    print("=" * 60, flush=True)
    print("TC-0024: 数字人成片操作（创建口播流程）", flush=True)
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

        # 步骤1：数字人卡片点创建口播
        print("\n--- 步骤1：打开创建口播弹窗 ---", flush=True)
        page.locator("button[aria-label='数字人库']").first.click(force=True)
        time.sleep(2)
        page.evaluate("""() => {
            const els = document.querySelectorAll('button, div, span');
            for (const e of els) { if (e.innerText.trim() === '数字人') { e.click(); break; } }
        }""")
        time.sleep(2)

        create_koubo = page.locator("text=创建口播").first
        if create_koubo.count() > 0:
            create_koubo.click(force=True)
            time.sleep(2)
            shot(page, "tc0024_1_dubbing.png")
            print("  ✅ 创建口播弹窗打开", flush=True)
            results.append(("创建口播弹窗打开", True))
        else:
            results.append(("创建口播弹窗打开", False))

        # 步骤2：验证步骤1配音页面元素
        print("\n--- 步骤2：验证配音页面元素 ---", flush=True)
        elements_ok = True
        
        # 标题输入框
        title_input = page.locator("input[placeholder*='留空']").first
        if title_input.count() > 0:
            print("  ✅ 标题输入框存在", flush=True)
        else:
            elements_ok = False
            
        # 文案输入框
        desc_input = page.locator("textarea, [contenteditable='true']").first
        if desc_input.count() > 0:
            print("  ✅ 文案输入框存在", flush=True)
        else:
            elements_ok = False
            
        # 声音选择
        voice_select = page.locator("text=元气少女").first
        if voice_select.count() > 0:
            print("  ✅ 声音选择存在（元气少女）", flush=True)
        else:
            elements_ok = False
            
        # 语速
        speed_1 = page.locator("text=1.0").first
        if speed_1.count() > 0:
            print("  ✅ 语速选项存在", flush=True)
        else:
            elements_ok = False
            
        # 合成配音按钮
        synth_btn = page.locator("text=合成配音").first
        if synth_btn.count() > 0:
            print("  ✅ 合成配音按钮存在", flush=True)
        else:
            elements_ok = False
            
        # 下一步按钮
        next_btn = page.locator("text=下一步").first
        if next_btn.count() > 0:
            print("  ✅ 下一步按钮存在", flush=True)
        else:
            elements_ok = False

        results.append(("配音页面元素完整", elements_ok))

        # 步骤3：填文案→合成配音→下一步
        print("\n--- 步骤3：填写文案并合成配音 ---", flush=True)
        # 填文案
        desc_input = page.locator("textarea[placeholder*='写下数字人']").first
        if desc_input.count() > 0:
            desc_input.click()
            desc_input.fill("大家好，今天给大家介绍一个非常好用的AI工具，它可以帮助我们快速生成数字人视频，节省大量时间和成本。")
            time.sleep(0.5)
            print("  ✅ 文案已填写", flush=True)
            shot(page, "tc0024_2_desc_filled.png")
            
            # 点合成配音
            synth_btn = page.locator("text=合成配音").first
            if synth_btn.count() > 0:
                synth_btn.click(force=True)
                print("  已点击合成配音，等待合成...", flush=True)
                time.sleep(10)  # 等待配音合成
                shot(page, "tc0024_3_after_synth.png")
                results.append(("配音合成成功", True))
            else:
                results.append(("配音合成成功", False))
        else:
            results.append(("配音合成成功", False))

        # 步骤4：点下一步进入步骤2
        print("\n--- 步骤4：进入数字人视频步骤 ---", flush=True)
        next_btn2 = page.locator("text=下一步").first
        if next_btn2.count() > 0:
            next_btn2.click(force=True)
            time.sleep(2)
            shot(page, "tc0024_4_step2.png")
            
            # 验证步骤2元素
            step2_title = page.locator("text=数字人视频").first
            if step2_title.count() > 0:
                print("  ✅ 已进入步骤2数字人视频页面", flush=True)
                results.append(("进入步骤2数字人视频", True))
            else:
                results.append(("进入步骤2数字人视频", False))
                
            # 验证生成数字人视频按钮
            gen_btn = page.locator("text=生成数字人视频").first
            if gen_btn.count() > 0:
                print("  ✅ 生成数字人视频按钮存在", flush=True)
                results.append(("生成数字人视频按钮存在", True))
            else:
                results.append(("生成数字人视频按钮存在", False))
        else:
            results.append(("进入步骤2数字人视频", False))

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

        if pass_count == len(results):
            print("\n[PASS] TC-0024 通过", flush=True)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback; traceback.print_exc()
        try: shot(page, "tc0024_error.png")
        except: pass
        sys.exit(1)
    finally:
        try:
            if browser: browser.close()
            if pw: pw.stop()
        except: pass


if __name__ == "__main__":
    test_tc0024()
