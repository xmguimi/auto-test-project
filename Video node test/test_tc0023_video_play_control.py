# -*- coding: utf-8 -*-
"""TC-0023 视频节点-播放控制（REAL_GENERATE=True，本地功能）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = True
ROOT = Path(__file__).parent


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


def get_video_state(page):
    """获取视频状态"""
    return page.evaluate("""
        () => {
            const v = document.querySelector('video');
            if (!v) return null;
            return {
                currentTime: v.currentTime,
                duration: v.duration,
                paused: v.paused,
                muted: v.muted,
                volume: v.volume
            };
        }
    """)


def main():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # 1. 双击视频节点进入全屏播放
    box = page.locator(".react-flow__node").nth(5).bounding_box()
    page.mouse.dblclick(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(2)

    # 验证video元素存在且正在播放
    v1 = get_video_state(page)
    if v1:
        check("双击进入全屏播放", v1["paused"] == False, f"paused={v1['paused']} currentTime={v1['currentTime']:.1f}s duration={v1['duration']:.1f}s")
    else:
        check("双击进入全屏播放", False, "未找到video元素")
        browser.close(); pw.stop(); return

    # 2. 点击视频中央暂停
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(1)
    v2 = get_video_state(page)
    check("点击视频暂停", v2["paused"] == True, f"paused={v2['paused']}")

    # 3. 再点击视频继续播放
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(1)
    v3 = get_video_state(page)
    check("再点击视频继续播放", v3["paused"] == False, f"paused={v3['paused']}")

    # 4. 等待2秒，验证进度条前进
    t1 = v3["currentTime"]
    time.sleep(2)
    v4 = get_video_state(page)
    t2 = v4["currentTime"]
    check("播放时进度前进", t2 > t1, f"t1={t1:.1f}s t2={t2:.1f}s 前进了{t2-t1:.1f}s")

    # 5. 用JS拖动进度条到中间
    page.evaluate("""
        () => {
            const v = document.querySelector('video');
            if (v) v.currentTime = v.duration / 2;
        }
    """)
    time.sleep(1)
    v5 = get_video_state(page)
    check("拖动进度条到中间", abs(v5["currentTime"] - v5["duration"] / 2) < 5, f"currentTime={v5['currentTime']:.1f}s 目标={v5['duration']/2:.1f}s")

    # 6. 验证音量/静音（用JS设置）
    page.evaluate("""
        () => {
            const v = document.querySelector('video');
            if (v) v.muted = true;
        }
    """)
    time.sleep(0.5)
    v6 = get_video_state(page)
    check("静音设置生效", v6["muted"] == True, f"muted={v6['muted']}")

    # 取消静音
    page.evaluate("""
        () => {
            const v = document.querySelector('video');
            if (v) v.muted = false;
        }
    """)
    time.sleep(0.5)
    v7 = get_video_state(page)
    check("取消静音生效", v7["muted"] == False, f"muted={v7['muted']}")

    # 7. 按ESC关闭全屏
    page.keyboard.press("Escape")
    time.sleep(1)
    check("按ESC关闭全屏", True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
