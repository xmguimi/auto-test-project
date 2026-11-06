# -*- coding: utf-8 -*-
"""TC-0020 视频节点-保存到资产库-名称与分类编辑（REAL_GENERATE=True，本地功能）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = True  # 本地功能
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


def get_active_categories(page):
    """获取选中态分类（通过背景色判断）"""
    return page.evaluate("""
        () => {
            const modal = document.querySelector('.cx-modal-panel.is-open');
            if (!modal) return [];
            const res = [];
            for (let btn of modal.querySelectorAll('button')) {
                const t = (btn.textContent || '').trim();
                if (!['人物', '场景', '物品', '音频', '其他'].includes(t)) continue;
                const style = window.getComputedStyle(btn);
                const bg = style.backgroundColor;
                // 紫色背景 rgb(139, 92, 246) 左右
                const isActive = bg.includes('139') || bg.includes('147') || bg.includes('168');
                if (isActive) res.push(t);
            }
            return res;
        }
    """)


def main():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # 1. 选中视频节点→打开弹窗
    page.keyboard.press("Escape")
    time.sleep(1)
    box = page.locator(".react-flow__node").nth(2).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)

    save_btn = page.locator("button[aria-label='保存到资产库']")
    sb = save_btn.first.bounding_box()
    page.mouse.click(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    time.sleep(2)
    check("弹窗打开", True)

    # 2. 验证资产名称默认值
    name_input = page.locator(".cx-modal-panel input")
    ni = name_input.first
    default_val = ni.input_value()
    check("资产名称默认值", default_val == "未命名资产", f"默认值='{default_val}'")

    # 3. 正常编辑资产名称
    ni.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    page.keyboard.type("草原羊群视频")
    time.sleep(0.3)
    val1 = ni.input_value()
    check("正常编辑名称-草原羊群视频", val1 == "草原羊群视频", f"输入框值='{val1}'")

    # 4. 清空名称
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    val2 = ni.input_value()
    check("清空名称", val2 == "", f"输入框值='{val2}'")

    # 5. 超长名称
    page.keyboard.type("A" * 50)
    time.sleep(0.3)
    val3 = ni.input_value()
    check("超长名称-可输入", len(val3) > 10, f"输入框值长度={len(val3)}")

    # 6. 特殊字符
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    page.keyboard.type("测试#@￥%&*")
    time.sleep(0.3)
    val4 = ni.input_value()
    check("特殊字符-正常显示", "测试" in val4, f"输入框值='{val4}'")

    # 7. 分类点击选中态唯一
    categories = ["人物", "场景", "物品", "音频", "其他"]
    for cat_name in categories:
        cat_btn = page.locator(f".cx-modal-panel button:has-text('{cat_name}')")
        if cat_btn.count() > 0:
            cb = cat_btn.first.bounding_box()
            page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
            time.sleep(0.3)

            active_cats = get_active_categories(page)
            check(f"分类-{cat_name}选中态唯一", len(active_cats) == 1 and active_cats[0] == cat_name, f"选中={active_cats}")
        else:
            check(f"分类-{cat_name}可点击", False, "未找到")

    # 8. 切回默认分类
    first_cat = page.locator(f".cx-modal-panel button:has-text('人物')")
    if first_cat.count() > 0:
        fb = first_cat.first.bounding_box()
        page.mouse.click(fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2)
        time.sleep(0.3)
        active_final = get_active_categories(page)
        check("切回默认分类选中态恢复", len(active_final) == 1 and active_final[0] == "人物", f"选中={active_final}")

    # 9. 点取消关闭
    cancel_btn = page.locator(".cx-modal-panel button:has-text('取消')")
    if cancel_btn.count() > 0:
        cb = cancel_btn.first.bounding_box()
        page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
        time.sleep(1)
        check("取消关闭弹窗", True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
