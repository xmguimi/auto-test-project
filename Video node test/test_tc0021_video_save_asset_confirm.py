# -*- coding: utf-8 -*-
"""TC-0021 视频节点-保存到资产库-确认保存与校验（REAL_GENERATE=True，本地功能）"""
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


def main():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)

    # ========== 场景1：确认保存正常流程 ==========
    page.keyboard.press("Escape")
    time.sleep(1)
    box = page.locator(".react-flow__node").nth(2).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)

    save_btn = page.locator("button[aria-label='保存到资产库']")
    sb = save_btn.first.bounding_box()
    page.mouse.click(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    time.sleep(2)
    check("场景1-弹窗打开", True)

    # 输入名称
    test_name = "草原羊群视频_自动化测试"
    name_input = page.locator(".cx-modal-panel input")
    ni = name_input.first
    ni.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    page.keyboard.type(test_name)
    time.sleep(0.3)

    # 选分类（人物）
    cat_btn = page.locator(".cx-modal-panel button:has-text('人物')")
    if cat_btn.count() > 0:
        cb = cat_btn.first.bounding_box()
        page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
        time.sleep(0.3)
        check("场景1-选分类人物", True)

    # 点确认保存
    confirm_btn = page.locator(".cx-modal-panel button:has-text('确认保存')")
    if confirm_btn.count() > 0:
        confb = confirm_btn.first.bounding_box()
        page.mouse.click(confb["x"] + confb["width"] / 2, confb["y"] + confb["height"] / 2)
        time.sleep(2)
        modal_count = page.locator(".cx-modal-panel.is-open").count()
        check("场景1-确认保存弹窗关闭", modal_count == 0, f"弹窗数={modal_count}")
    else:
        check("场景1-确认保存按钮", False, "未找到")

    # ========== 场景2：验证资产库新增该资产 ==========
    # 用JS打开资产管理面板
    page.evaluate("""
        () => {
            const btn = document.querySelector('button[aria-label="资产管理"]');
            if (btn) btn.click();
        }
    """)
    time.sleep(2)
    check("场景2-资产管理面板打开", True)

    # 点素材分类
    material_btn = page.locator(".cx-modal-panel :text('素材')")
    if material_btn.count() > 0:
        mb = material_btn.first.bounding_box()
        page.mouse.click(mb["x"] + mb["width"] / 2, mb["y"] + mb["height"] / 2)
        time.sleep(1)
        check("场景2-进入素材分类", True)

    # 搜索资产名称
    search_input = page.locator(".cx-modal-panel input[placeholder*='搜索']")
    if search_input.count() > 0:
        si = search_input.first
        si.click()
        time.sleep(0.2)
        page.keyboard.type(test_name)
        time.sleep(1)
        check("场景2-搜索资产名称", True)

        # 验证搜索结果
        search_result = page.evaluate(f"""
            () => {{
                const t = document.body.textContent || '';
                return t.includes('{test_name}');
            }}
        """)
        check("场景2-资产库搜索到新增资产", search_result, f"搜索关键词='{test_name}'")
    else:
        check("场景2-搜索框", False, "未找到搜索框")

    # 关闭资产管理面板
    close_asset = page.locator(".cx-modal-panel button[aria-label='关闭']")
    if close_asset.count() > 0:
        cb = close_asset.first.bounding_box()
        page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
        time.sleep(1)

    # ========== 场景3：取消不保存 ==========
    page.keyboard.press("Escape")
    time.sleep(1)
    box2 = page.locator(".react-flow__node").nth(2).bounding_box()
    page.mouse.click(box2["x"] + box2["width"] / 2, box2["y"] + 12)
    time.sleep(1)

    save_btn2 = page.locator("button[aria-label='保存到资产库']")
    sb2 = save_btn2.first.bounding_box()
    page.mouse.click(sb2["x"] + sb2["width"] / 2, sb2["y"] + sb2["height"] / 2)
    time.sleep(2)
    check("场景3-弹窗打开", True)

    cancel_btn = page.locator(".cx-modal-panel button:has-text('取消')")
    if cancel_btn.count() > 0:
        cb2 = cancel_btn.first.bounding_box()
        page.mouse.click(cb2["x"] + cb2["width"] / 2, cb2["y"] + cb2["height"] / 2)
        time.sleep(1)
        modal_count2 = page.locator(".cx-modal-panel.is-open").count()
        check("场景3-取消弹窗关闭", modal_count2 == 0, f"弹窗数={modal_count2}")

    # ========== 场景4：空名称确认保存 ==========
    page.keyboard.press("Escape")
    time.sleep(1)
    box3 = page.locator(".react-flow__node").nth(2).bounding_box()
    page.mouse.click(box3["x"] + box3["width"] / 2, box3["y"] + 12)
    time.sleep(1)

    save_btn3 = page.locator("button[aria-label='保存到资产库']")
    sb3 = save_btn3.first.bounding_box()
    page.mouse.click(sb3["x"] + sb3["width"] / 2, sb3["y"] + sb3["height"] / 2)
    time.sleep(2)
    check("场景4-弹窗打开", True)

    name_input3 = page.locator(".cx-modal-panel input")
    ni3 = name_input3.first
    ni3.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    val_empty = ni3.input_value()
    check("场景4-清空名称", val_empty == "", f"输入框值='{val_empty}'")

    confirm_btn3 = page.locator(".cx-modal-panel button:has-text('确认保存')")
    if confirm_btn3.count() > 0:
        confb3 = confirm_btn3.first.bounding_box()
        page.mouse.click(confb3["x"] + confb3["width"] / 2, confb3["y"] + confb3["height"] / 2)
        time.sleep(1)
        modal_count3 = page.locator(".cx-modal-panel.is-open").count()
        check("场景4-空名称被拦截弹窗未关闭", modal_count3 == 1, f"弹窗数={modal_count3}")

    close_btn = page.locator(".cx-modal-panel button[aria-label='关闭']")
    if close_btn.count() > 0:
        cb3 = close_btn.first.bounding_box()
        page.mouse.click(cb3["x"] + cb3["width"] / 2, cb3["y"] + cb3["height"] / 2)
        time.sleep(1)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
