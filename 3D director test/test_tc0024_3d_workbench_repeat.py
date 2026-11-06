# -*- coding: utf-8 -*-
"""
TC-0024: 3D导演台-工作台反复开关
测试：验证多次打开/关闭3D工作台后状态正常（无卡顿、无内存泄漏迹象、画布节点不受影响）
用例编号: TC-0024
自动化脚本文件名: test_tc0024_3d_workbench_repeat.py

前置条件:
  1. 系统服务正常，网络连通
  2. 账号已登录
  3. 生产版环境
  4. 画布中已存在3D导演台节点（脚本会自动准备：缺失时双击画布从菜单创建）

测试方案:
  1. 选中3D导演台节点，打开工作台
  2. 关闭工作台
  3. 重复打开/关闭5次
  4. 观察每次打开是否正常，画布节点是否受影响

预期结果:
  1. 每次打开/关闭都正常
  2. 多次操作后无卡顿、无内存泄漏迹象
  3. 画布节点不受影响
  4. 全程无报错
"""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
ROOT = Path(__file__).parent
SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)

REAL_GENERATE = True

# 单次打开/关闭超过该秒数视为卡顿
SLOW_THRESHOLD = 8.0


def shot(page, name):
    page.screenshot(path=str(SHOT_DIR / name))
    print(f"  [SHOT] {name}", flush=True)


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


def workbench_open(page):
    """判断工作台是否处于打开状态（以工作台特有的'导演视角'标签可见为准；
    实测'未命名场景'标题在DOM中匹配不到，不可用作信号）"""
    tab = page.locator("text=导演视角").first
    return tab.count() > 0 and tab.is_visible()


def canvas_node_exists(page):
    """判断画布上3D导演台节点是否可见（节点文本实际为'未命名3D 导演台'）"""
    node = page.locator("text=3D 导演台").first
    return node.count() > 0 and node.is_visible()


def ensure_canvas(page):
    """确保回到画布视图：若页面存在'返回画布'按钮则点击返回"""
    back = page.locator("text=返回画布").first
    if back.count() > 0 and back.is_visible():
        back.click(force=True)
        time.sleep(2)
        return True
    return True


def ensure_director_node(page):
    """确保画布上存在3D导演台节点：缺失时双击画布空白处，从菜单创建"""
    if canvas_node_exists(page):
        return True
    # 取消当前选中，避免双击命中已有节点
    page.keyboard.press("Escape")
    time.sleep(0.8)
    # 双击画布空白处（避开节点区域）
    page.mouse.dblclick(750, 350)
    time.sleep(1.5)
    item = page.locator(".cm-item:has-text('3D 导演台')").first
    if item.count() > 0:
        item.click(force=True)
        time.sleep(2)
    else:
        try:
            items = page.evaluate(
                "() => [...document.querySelectorAll('.cm-item')]"
                ".map(e => (e.textContent || '').trim()).slice(0, 40)"
            )
            print(f"   [DBG] 菜单项: {items}", flush=True)
        except Exception:
            pass
        return False
    return canvas_node_exists(page)


def click_open_workbench_btn(page):
    """点击'打开工作台'按钮：优先按aria-label定位，兜底按文本JS点击"""
    open_btn = page.locator("button[aria-label='打开工作台']").first
    if open_btn.count() > 0:
        open_btn.click(force=True)
        return True
    ok = page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button');
            for (let btn of btns) {
                const label = (btn.getAttribute('aria-label') || '') + btn.textContent;
                if (label.includes('打开工作台')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }
    """)
    if not ok:
        try:
            labels = page.evaluate(
                "() => [...document.querySelectorAll('button')]"
                ".map(b => (b.getAttribute('aria-label') || '') + '|' + (b.textContent || '').trim())"
                ".slice(0, 60)"
            )
            print(f"   [DBG] 当前按钮: {labels}", flush=True)
        except Exception:
            pass
    return ok


def open_workbench(page):
    """打开工作台：选中3D导演台节点 -> 点击'打开工作台'按钮"""
    node = page.locator("text=3D 导演台").first
    node.click(force=True)
    time.sleep(0.5)
    if not click_open_workbench_btn(page):
        raise RuntimeError("未找到'打开工作台'按钮")
    time.sleep(2)


def close_workbench(page):
    """关闭工作台：JS点击工作台顶栏'.top-bar-actions'内的'关闭'按钮(cx-ibtn sm)
    实测（2026-11-04）：空工作台点击后直接关闭、无确认框；
    注意不要点窗口标题栏的关闭按钮（会关整个应用）；
    若出现'确认关闭应用'类对话框，自动点'取消'保护应用。
    兜底：找不到关闭按钮时尝试点击'发送到画布'。"""
    page.evaluate("""
        () => {
            const c = document.querySelector('.top-bar-actions');
            if (c) {
                const btns = c.querySelectorAll('button');
                for (let b of btns) {
                    if (b.getAttribute('aria-label') === '关闭') {
                        b.click();
                        return true;
                    }
                }
            }
            const btns = document.querySelectorAll('button');
            for (let b of btns) {
                if ((b.textContent || '').includes('发送到画布')) {
                    b.click();
                    return true;
                }
            }
            return false;
        }
    """)
    time.sleep(1.2)
    # 安全网：若弹出确认对话框，点'取消'（仅点可见的取消按钮）
    page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button');
            for (let b of btns) {
                const t = (b.textContent || '').trim();
                const aria = b.getAttribute('aria-label') || '';
                if (/^取消$/.test(t) || /^取消$/.test(aria)) {
                    const r = b.getBoundingClientRect();
                    const st = getComputedStyle(b);
                    if (r.width > 5 && r.height > 5 && st.display !== 'none' && st.visibility !== 'hidden') {
                        b.click();
                        return true;
                    }
                }
            }
            return false;
        }
    """)
    time.sleep(0.5)


def heap_mb(page):
    """读取渲染进程JS堆内存(MB)，用于观察内存泄漏趋势；取不到返回None"""
    try:
        m = page.evaluate(
            "() => window.performance && window.performance.memory"
            " ? window.performance.memory.usedJSHeapSize : -1"
        )
        if m and m > 0:
            return round(m / 1024 / 1024, 1)
        return None
    except Exception:
        return None


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0024: 3D导演台-工作台反复开关", flush=True)
    print("=" * 60, flush=True)

    # 0. 确保回到画布视图
    print("\n0. 确保回到画布视图", flush=True)
    try:
        ensure_canvas(page)
        print("   ✅ 已回到画布视图", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 0.2 前置检查：画布上存在3D导演台节点
    print("\n0.2 前置检查：画布上存在3D导演台节点", flush=True)
    try:
        if ensure_director_node(page):
            print("   ✅ 3D导演台节点就绪", flush=True)
            results.append(True)
        else:
            print("   ❌ 无法创建/定位3D导演台节点", flush=True)
            results.append(False)
        shot(page, "tc0024_setup_node.png")
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 0.3 若工作台已处于打开状态，先关闭
    print("\n0.3 确保工作台处于关闭状态", flush=True)
    try:
        if workbench_open(page):
            close_workbench(page)
            time.sleep(1)
        print("   ✅ 已确保工作台关闭", flush=True)
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    open_times = []
    close_times = []
    heaps = []

    # 重复打开/关闭5次
    for i in range(1, 6):
        print(f"\n--- 第{i}次开关 ---", flush=True)

        # 1. 打开工作台
        print(f"\n{i}.1 打开工作台", flush=True)
        try:
            t0 = time.time()
            open_workbench(page)
            dt = round(time.time() - t0, 2)
            open_times.append(dt)
            if workbench_open(page):
                print(f"   ✅ 第{i}次打开成功（耗时 {dt}s）", flush=True)
                results.append(True)
            else:
                print(f"   ❌ 第{i}次打开失败", flush=True)
                results.append(False)
            shot(page, f"tc0024_open_{i}.png")
        except Exception as e:
            print(f"   ❌ 第{i}次打开失败: {e}", flush=True)
            results.append(False)

        # 2. 关闭工作台
        print(f"\n{i}.2 关闭工作台", flush=True)
        try:
            t0 = time.time()
            close_workbench(page)
            time.sleep(1)
            dt = round(time.time() - t0, 2)
            close_times.append(dt)
            if not workbench_open(page):
                print(f"   ✅ 第{i}次关闭成功（耗时 {dt}s）", flush=True)
                results.append(True)
            else:
                print(f"   ⚠️ 第{i}次关闭未成功", flush=True)
                results.append(False)
            shot(page, f"tc0024_closed_{i}.png")
        except Exception as e:
            print(f"   ❌ 第{i}次关闭失败: {e}", flush=True)
            results.append(False)

        # 3. 画布节点不受影响
        print(f"\n{i}.3 画布节点检查", flush=True)
        try:
            if canvas_node_exists(page):
                print("   ✅ 画布节点正常显示，未受影响", flush=True)
                results.append(True)
            else:
                print("   ❌ 画布节点异常/消失", flush=True)
                results.append(False)
        except Exception as e:
            print(f"   ❌ 失败: {e}", flush=True)
            results.append(False)

        # 内存采样（观察趋势）
        m = heap_mb(page)
        if m is not None:
            heaps.append(m)
            print(f"   [MEM] JS堆内存: {m}MB", flush=True)

    # 4. 性能检查：卡顿（打开/关闭耗时）与内存趋势
    print("\n4. 性能检查（卡顿/内存趋势）", flush=True)
    try:
        slow_flag = False
        if open_times:
            mx_open = max(open_times)
            avg_open = round(sum(open_times) / len(open_times), 2)
            print(f"   打开耗时: {open_times}，平均 {avg_open}s，最大 {mx_open}s", flush=True)
            if mx_open > SLOW_THRESHOLD:
                slow_flag = True
                print(f"   ⚠️ 打开耗时超过 {SLOW_THRESHOLD}s，疑似卡顿", flush=True)
        if close_times:
            mx_close = max(close_times)
            avg_close = round(sum(close_times) / len(close_times), 2)
            print(f"   关闭耗时: {close_times}，平均 {avg_close}s，最大 {mx_close}s", flush=True)
            if mx_close > SLOW_THRESHOLD:
                slow_flag = True
                print(f"   ⚠️ 关闭耗时超过 {SLOW_THRESHOLD}s，疑似卡顿", flush=True)
        if heaps:
            print(f"   JS堆内存趋势: {heaps}MB", flush=True)
            if len(heaps) >= 2 and heaps[-1] > heaps[0] * 1.5 and heaps == sorted(heaps):
                print("   ⚠️ JS堆内存持续上升，存在内存泄漏迹象", flush=True)
                results.append(False)
            else:
                print("   ✅ 无内存泄漏迹象", flush=True)
                results.append(True)
        if not slow_flag and open_times and close_times:
            print("   ✅ 多次开关无卡顿", flush=True)
            results.append(True)
        if slow_flag:
            results.append(False)
    except Exception as e:
        print(f"   ❌ 性能检查失败: {e}", flush=True)
        results.append(False)

    # 5. 最终画布节点状态
    print("\n5. 最终画布节点状态", flush=True)
    try:
        if canvas_node_exists(page):
            print("   ✅ 5次开关后画布节点正常", flush=True)
            results.append(True)
        else:
            print("   ❌ 画布节点异常", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 输出结果
    print("\n" + "=" * 60, flush=True)
    pass_count = sum(results)
    print(f"通过: {pass_count}/{len(results)}", flush=True)

    browser.close()
    pw.stop()


if __name__ == "__main__":
    test()
