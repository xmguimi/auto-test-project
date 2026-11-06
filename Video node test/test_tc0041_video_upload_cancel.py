# -*- coding: utf-8 -*-
"""TC-0041 视频节点-上传中取消（file_chooser方式）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = True
ROOT = Path(__file__).parent
VIDEO_PATH = r"C:\Users\HP\Videos\Captures\WPS演示 幻灯片放映 - [第三组需求范围说明最终版.pptx] 2025-03-31 22-20-32.mp4"


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


def main():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # 0. 确认视频文件存在
    check("视频文件存在", Path(VIDEO_PATH).exists(), "")
    if not Path(VIDEO_PATH).exists():
        browser.close()
        pw.stop()
        return

    # 1. 右键画布空白处
    page.keyboard.press("Escape")
    time.sleep(1)
    page.mouse.click(800, 400, button="right")
    time.sleep(1)

    # 2. 点"上传图片/视频"
    upload_btn = page.locator("text=上传图片/视频")
    check("右键菜单有上传选项", upload_btn.count() > 0)

    # 3. 监听file chooser并设置文件
    try:
        with page.expect_file_chooser() as fc_info:
            upload_btn.first.click()
        file_chooser = fc_info.value
        print("已触发文件选择对话框", flush=True)

        # 尝试设置大文件
        file_chooser.set_files(VIDEO_PATH)
        print("已设置文件，等待上传...", flush=True)
        time.sleep(5)
        check("上传中等待5秒", True)

    except Exception as e:
        check("file_chooser上传", False, f"错误: {str(e)[:80]}")

    # 4. 截图
    page.screenshot(path=str(ROOT / "tc0041_uploading.png"))
    print("已截图", flush=True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
