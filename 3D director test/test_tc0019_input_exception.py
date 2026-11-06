# -*- coding: utf-8 -*-
"""
TC-0019: 3D导演台-角色参数空输入与异常输入
测试：位置X输入框的空输入、特殊字符、超大数值、负数
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


def get_position_x_value(page):
    """获取位置X输入框的当前值"""
    input_box = page.locator("input[aria-label='角色位置 X']").first
    return input_box.input_value()


def set_position_x_value(page, value):
    """设置位置X输入框的值"""
    input_box = page.locator("input[aria-label='角色位置 X']").first
    input_box.click()
    input_box.fill("")
    input_box.fill(str(value))
    input_box.press("Enter")
    time.sleep(1)


def test():
    pw, browser, page = connect()
    time.sleep(2)
    results = []

    print("=" * 60, flush=True)
    print("TC-0019: 3D导演台-角色参数空输入与异常输入", flush=True)
    print("=" * 60, flush=True)

    # 1. 确认角色01已选中，位置X输入框可见
    print("\n1. 确认角色01已选中，位置X输入框可见", flush=True)
    try:
        input_x = page.locator("input[aria-label='角色位置 X']").first
        if input_x.count() > 0 and input_x.is_visible():
            current_value = get_position_x_value(page)
            print(f"   ✅ 位置X输入框可见，当前值: {current_value}", flush=True)
            results.append(True)
        else:
            print("   ❌ 位置X输入框未找到", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 2. 空输入测试：清空输入框，不输入任何内容，按回车
    print("\n2. 空输入测试", flush=True)
    try:
        input_x = page.locator("input[aria-label='角色位置 X']").first
        input_x.click()
        input_x.fill("")  # 清空
        input_x.press("Enter")
        time.sleep(1)
        after_value = get_position_x_value(page)
        print(f"   空输入后，位置X值: '{after_value}'", flush=True)
        shot(page, "tc0019_empty_input.png")
        if after_value != "":
            print("   ✅ 空输入被处理（自动恢复为0）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 空输入后输入框仍为空", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 3. 特殊字符测试：输入"@#￥%"
    print("\n3. 特殊字符测试", flush=True)
    try:
        # number类型输入框原生不允许输入特殊字符
        input_x = page.locator("input[aria-label='角色位置 X']").first
        input_x.click()
        input_x.fill("")
        # 尝试输入特殊字符，看是否被拒绝
        try:
            input_x.type("@#￥%")
            time.sleep(0.5)
        except:
            pass
        input_x.press("Enter")
        time.sleep(1)
        after_value = get_position_x_value(page)
        print(f"   尝试输入特殊字符后，位置X值: '{after_value}'", flush=True)
        shot(page, "tc0019_special_chars.png")
        if "@" not in after_value and "#" not in after_value:
            print("   ✅ 特殊字符被拒绝（number类型输入框原生限制）", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 特殊字符被接受", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 4. 超大数值测试：输入99999（5个9）
    print("\n4. 超大数值测试（输入99999）", flush=True)
    try:
        set_position_x_value(page, "99999")
        after_value = get_position_x_value(page)
        print(f"   输入99999后，位置X值: '{after_value}'", flush=True)
        shot(page, "tc0019_huge_number.png")
        # 检查角色是否在可视范围内（通过截图看角色是否可见）
        # 这里我们记录输入了超大数值，角色可能跑出可视范围
        print(f"   ⚠️ 输入99999后，角色可能跑出可视范围", flush=True)
        results.append(False)  # 实际不符合预期
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 5. 负数测试：输入-99999
    print("\n5. 负数测试（输入-99999）", flush=True)
    try:
        set_position_x_value(page, "-99999")
        after_value = get_position_x_value(page)
        print(f"   输入负数后，位置X值: '{after_value}'", flush=True)
        shot(page, "tc0019_negative_number.png")
        if "-" in after_value:
            print(f"   ✅ 负数可正常输入，当前值: {after_value}", flush=True)
            results.append(True)
        else:
            print(f"   ⚠️ 负数被转为正数", flush=True)
            results.append(False)
    except Exception as e:
        print(f"   ❌ 失败: {e}", flush=True)
        results.append(False)

    # 6. 恢复初始值为0
    print("\n6. 恢复位置X为初始值0", flush=True)
    try:
        set_position_x_value(page, "0")
        after_value = get_position_x_value(page)
        print(f"   恢复后位置X值: '{after_value}'", flush=True)
        shot(page, "tc0019_restored.png")
        if after_value == "0":
            print("   ✅ 已恢复初始值", flush=True)
            results.append(True)
        else:
            print("   ⚠️ 未恢复为0", flush=True)
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
