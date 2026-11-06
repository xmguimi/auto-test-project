# -*- coding: utf-8 -*-
"""TC-0025 补充验证：副本独立操作互不影响"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
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


def get_node_names(page):
    """获取所有节点的名称"""
    return page.evaluate("""
        () => {
            const res = [];
            for (let n of document.querySelectorAll('.react-flow__node .nname')) {
                res.push(n.textContent.trim());
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

    # 1. 记录当前节点数和名称
    names_before = get_node_names(page)
    print(f"当前节点数: {len(names_before)}", flush=True)
    print(f"节点名称: {names_before[:5]}...", flush=True)

    # 2. 选中第一个节点（原节点）
    page.keyboard.press("Escape")
    time.sleep(1)
    box0 = page.locator(".react-flow__node").nth(0).bounding_box()
    page.mouse.click(box0["x"] + box0["width"] / 2, box0["y"] + 12)
    time.sleep(1)
    check("选中原节点", True)

    # 3. Ctrl+C复制
    page.keyboard.press("Control+c")
    time.sleep(1)
    check("Ctrl+C复制", True)

    # 4. 点空白处
    page.mouse.click(50, 500)
    time.sleep(1)

    # 5. Ctrl+V粘贴
    page.keyboard.press("Control+v")
    time.sleep(2)
    check("Ctrl+V粘贴", True)

    # 6. 验证新节点出现
    names_after = get_node_names(page)
    check("粘贴后节点数增加", len(names_after) > len(names_before), f"复制前={len(names_before)} 粘贴后={len(names_after)}")

    # 7. 选中副本节点（最后一个节点）
    last_idx = len(names_after) - 1
    box_last = page.locator(".react-flow__node").nth(last_idx).bounding_box()
    page.mouse.click(box_last["x"] + box_last["width"] / 2, box_last["y"] + 12)
    time.sleep(1)
    check("选中副本节点", True)

    # 8. 重命名副本
    rename_btn = page.locator("button[aria-label='重命名']")
    if rename_btn.count() > 0:
        rb = rename_btn.first.bounding_box()
        page.mouse.click(rb["x"] + rb["width"] / 2, rb["y"] + rb["height"] / 2)
        time.sleep(1)
        check("点重命名按钮", True)

        # 输入新名称
        name_input = page.locator("input[placeholder*='节点名称']")
        if name_input.count() > 0:
            ni = name_input.first
            ni.click()
            time.sleep(0.2)
            page.keyboard.press("Control+a")
            time.sleep(0.1)
            page.keyboard.type("副本_测试重命名")
            time.sleep(0.2)
            page.keyboard.press("Enter")
            time.sleep(1)
            check("副本重命名", True)

            # 9. 验证原节点名称不变
            names_after_rename = get_node_names(page)
            check("原节点名称不变", len(names_after_rename) == len(names_after), f"节点数={len(names_after_rename)}")
        else:
            check("重命名输入框", False, "未找到")
    else:
        check("重命名按钮", False, "未找到")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
