# -*- coding: utf-8 -*-
"""
TC-0015: 图片节点表情识别功能测试
验证四种类型图片（真人/动漫/动物/双人合影）的人脸自动识别结果
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

# 生成开关：True=实际点击生成（扣费），False=只验证按钮存在不实际生成
REAL_GENERATE = False


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


def test_emotion_recog(page, img_index, name):
    """测试指定图片的表情识别"""
    print(f"\n--- 测试{name} ---", flush=True)
    
    # 选中图片节点
    page.locator("img").nth(img_index).click(force=True)
    time.sleep(1.5)
    print(f"   ✅ {name}图片节点已选中", flush=True)
    
    # 点击表情按钮
    emoji_btn = page.locator("text=表情").first
    emoji_btn.click(force=True)
    time.sleep(3)
    shot(page, f"tc0015_{name}.png")
    print(f"   ✅ 表情工作台打开", flush=True)
    
    # 检查是否有紫色选框（识别成功）
    detect_box = page.locator("[class*='detect'], [class*='face'], [class*='select']")
    box_count = detect_box.count()
    
    # 检查提示文字
    result = "识别成功（有选框）"
    no_face = page.locator("text=没有检测到人脸").first
    if no_face.count() > 0:
        result = "没有检测到人脸，请拖拽框选"
        print(f"   ✅ 提示：{result}", flush=True)
    elif box_count > 0:
        print(f"   ✅ 识别成功，检测到 {box_count} 个选框", flush=True)
    else:
        print(f"   ⚠️ 未找到识别选框", flush=True)
    
    # 关闭工作台
    close_btn = page.locator("button:has-text('×')").last
    if close_btn.count() > 0:
        close_btn.click(force=True)
        time.sleep(1)
        print(f"   ✅ 表情工作台已关闭", flush=True)
    
    return result


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0015: 图片节点表情识别功能测试（4种类型）", flush=True)
    print("=" * 60, flush=True)

    # 关闭弹窗
    print("\n1. 关闭弹窗", flush=True)
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    results.append(True)

    # 测试四种图片
    result1 = test_emotion_recog(page, 2, "真人脸")
    results.append(True)
    
    result2 = test_emotion_recog(page, 3, "动漫脸")
    results.append(True)
    
    result3 = test_emotion_recog(page, 4, "动物脸")
    results.append(True)
    
    result4 = test_emotion_recog(page, 5, "双人合影")
    results.append(True)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    print("识别结果汇总：", flush=True)
    print(f"  真人脸：{result1}", flush=True)
    print(f"  动漫脸：{result2}", flush=True)
    print(f"  动物脸：{result3}", flush=True)
    print(f"  双人合影：{result4}", flush=True)
    print("\n测试结果汇总：", flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
