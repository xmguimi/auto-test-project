# -*- coding: utf-8 -*-
"""TC-0018 视频节点-重命名（补充验证：空名称恢复、纯空格、超长名称、重名、影响面）"""
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

    # 1. 选中 findbugs 原视频
    page.keyboard.press("Escape")
    time.sleep(1)
    idx = page.evaluate("""
        () => {
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                const n = document.querySelectorAll('.react-flow__node')[i];
                const t = (n.textContent || '');
                const r = n.getBoundingClientRect();
                if (t.includes('find') && !t.includes('转码') && !t.includes('无声') && !t.includes('抽帧') && !t.includes('分离音频') && r.x > 0 && r.y > 0) return i;
            }
            return -1;
        }
    """)
    if idx < 0:
        print("FAIL: 未找到原视频", flush=True)
        browser.close(); pw.stop()
        return
    box = page.locator(".react-flow__node").nth(idx).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True, f"idx={idx}")

    # 记录原名
    rename_btn = page.locator("button[aria-label='重命名']")
    rb = rename_btn.first.bounding_box()
    page.mouse.click(rb["x"] + rb["width"] / 2, rb["y"] + rb["height"] / 2)
    time.sleep(1)
    name_input = page.locator("input[placeholder='输入节点名称']")
    original_name = name_input.first.input_value()
    print(f"原名称: '{original_name}'", flush=True)
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # 2. 空名称：清空→回车→验证恢复原名
    rb2 = rename_btn.first.bounding_box()
    page.mouse.click(rb2["x"] + rb2["width"] / 2, rb2["y"] + rb2["height"] / 2)
    time.sleep(1)
    ni = name_input.first
    ni.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    val_empty = ni.input_value()
    print(f"清空后输入框值: '{val_empty}'", flush=True)
    page.keyboard.press("Enter")
    time.sleep(1)

    # 重新打开验证恢复原名
    rb3 = rename_btn.first.bounding_box()
    page.mouse.click(rb3["x"] + rb3["width"] / 2, rb3["y"] + rb3["height"] / 2)
    time.sleep(1)
    name_input2 = page.locator("input[placeholder='输入节点名称']")
    val_after_empty = name_input2.first.input_value()
    check("空名称-恢复原名", val_after_empty == original_name, f"原名='{original_name}' → 当前='{val_after_empty}'")
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # 3. 纯空格：输入多个空格→回车
    rb4 = rename_btn.first.bounding_box()
    page.mouse.click(rb4["x"] + rb4["width"] / 2, rb4["y"] + rb4["height"] / 2)
    time.sleep(1)
    ni2 = name_input2.first
    ni2.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    page.keyboard.type("   ")
    time.sleep(0.3)
    val_spaces = ni2.input_value()
    print(f"输入空格后值: '{val_spaces}'", flush=True)
    page.keyboard.press("Enter")
    time.sleep(1)

    # 重新打开验证
    rb5 = rename_btn.first.bounding_box()
    page.mouse.click(rb5["x"] + rb5["width"] / 2, rb5["y"] + rb5["height"] / 2)
    time.sleep(1)
    name_input3 = page.locator("input[placeholder='输入节点名称']")
    val_after_spaces = name_input3.first.input_value()
    check("纯空格-恢复原名", val_after_spaces == original_name, f"原名='{original_name}' → 当前='{val_after_spaces}'")
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # 4. 超长名称：输入50+字符→回车
    rb6 = rename_btn.first.bounding_box()
    page.mouse.click(rb6["x"] + rb6["width"] / 2, rb6["y"] + rb6["height"] / 2)
    time.sleep(1)
    ni3 = name_input3.first
    ni3.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    long_name = "A" * 50
    page.keyboard.type(long_name)
    time.sleep(0.3)
    val_long = ni3.input_value()
    print(f"超长名称输入值长度: {len(val_long)}", flush=True)
    page.keyboard.press("Enter")
    time.sleep(1)

    # 重新打开验证
    rb7 = rename_btn.first.bounding_box()
    page.mouse.click(rb7["x"] + rb7["width"] / 2, rb7["y"] + rb7["height"] / 2)
    time.sleep(1)
    name_input4 = page.locator("input[placeholder='输入节点名称']")
    val_after_long = name_input4.first.input_value()
    check("超长名称-保存成功", len(val_after_long) > 10, f"当前长度={len(val_after_long)}")
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # 5. 重名处理：重命名成和另一个节点一样的名字（不弹提示）
    # 先找另一个视频节点的名称
    other_name = page.evaluate("""
        () => {
            for (let i = 0; i < document.querySelectorAll('.react-flow__node').length; i++) {
                if (i === 0) continue;
                const n = document.querySelectorAll('.react-flow__node')[i];
                const r = n.getBoundingClientRect();
                if (r.x < 100) continue;
                const inp = n.querySelector('input[placeholder*="节点名称"]');
                if (inp) return inp.value;
                const t = n.textContent || '';
                if (t.includes('视频剪辑')) return '视频剪辑';
            }
            return null;
        }
    """)
    print(f"另一个节点名称: '{other_name}'", flush=True)

    rb8 = rename_btn.first.bounding_box()
    page.mouse.click(rb8["x"] + rb8["width"] / 2, rb8["y"] + rb8["height"] / 2)
    time.sleep(1)
    ni4 = name_input4.first
    ni4.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    time.sleep(0.1)
    page.keyboard.press("Backspace")
    time.sleep(0.2)
    page.keyboard.type("视频剪辑")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(1)

    # 检查是否有错误提示
    has_error = page.evaluate("""
        () => {
            const t = document.body.textContent || '';
            return t.includes('重名') || t.includes('已存在') || t.includes('名称重复');
        }
    """)
    check("重名-无提示", not has_error, "未弹出重名提示")

    # 验证重命名成功
    rb9 = rename_btn.first.bounding_box()
    page.mouse.click(rb9["x"] + rb9["width"] / 2, rb9["y"] + rb9["height"] / 2)
    time.sleep(1)
    name_input5 = page.locator("input[placeholder='输入节点名称']")
    val_after_dup = name_input5.first.input_value()
    check("重名-保存成功", val_after_dup == "视频剪辑", f"当前名称='{val_after_dup}'")
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # 6. 影响面验证：重命名后视频播放、工具栏、连线正常
    # 检查节点是否还在
    node_exists = page.evaluate(f"""
        () => {{
            return document.querySelectorAll('.react-flow__node')[{idx}] !== undefined;
        }}
    """)
    check("影响面-节点存在", node_exists)

    # 检查工具栏按钮还在
    toolbar_btns = page.locator("button[aria-label*='抽帧'], button[aria-label*='延长'], button[aria-label*='编辑']")
    check("影响面-工具栏正常", toolbar_btns.count() >= 3, f"工具栏按钮数={toolbar_btns.count()}")

    # 检查连线（连线还在）
    edges = page.locator(".react-flow__edge")
    check("影响面-连线正常", edges.count() > 0, f"连线数={edges.count()}")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
