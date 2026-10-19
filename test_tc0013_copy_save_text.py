"""
TC-0013 自动化测试：文本节点复制 Markdown + 保存到资产库
测试软件：帧境 AI（桌面版，Electron，画布基于 React Flow）

流程：
    1. 双击画布 → 新建文本节点
    2. 双击节点进入编辑，输入三行文字：一个美丽的模特 / 高 / 瘦
    3. 点击工具栏【复制 Markdown】（不是 Ctrl+C 选中文字）
    4. 粘贴到页面底部的中控台（.promptbox 内的 .wprompt-ed），验证复制内容
    5. 点击工具栏【保存到资产库】
    6. 弹窗中选【其他】分类，点【确认保存】
    7. 点击左侧【资产管理】
    8. 点击分类栏里的【其他】标签
    9. 验证文本已保存

关键结构：
    - 复制按钮：工具栏 button[title='复制 Markdown']
    - 中控台输入框：.promptbox 内的 div[data-lexical-editor='true']
                  或 div.wprompt-ed.text-mode
    - 保存弹窗分类：.grid.grid-cols-3 内的 button:text-is('其他')
    - 资产库分类栏：.am-cattabs 内的 .cx-chip-label 文字="其他"

运行前置：
    pip install playwright requests
    python -m playwright install chromium
    帧境 AI 已带 --remote-debugging-port=9222 启动
"""

import os
import sys
import re
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = 9222
ROOT = Path(__file__).parent

LINE1 = "一个美丽的模特"
LINE2 = "高"
LINE3 = "瘦"

SHOT_DIR = ROOT / "screenshots"
SHOT_DIR.mkdir(exist_ok=True)


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT_DIR / name))
        print(f"[SHOT] {name}")
    except Exception as e:
        print(f"[SHOT-FAIL] {name}: {e}")


def is_cdp_ready(port=PORT):
    try:
        r = requests.get(f"http://localhost:{port}/json/version", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def connect():
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")
    pages = browser.contexts[0].pages
    target = None
    for p in pages:
        if "帧境" in (p.title() or ""):
            target = p
            break
    if not target:
        target = pages[0]

    try:
        target.context.grant_permissions(["clipboard-read", "clipboard-write"])
        print("[OK] 已授予剪贴板权限")
    except Exception as e:
        print(f"[WARN] 授权失败: {e}")

    return pw, browser, target


# ============ 新建文本节点 ============
def dblclick_canvas(page):
    print("\n=== 双击画布 ===")
    page.mouse.dblclick(600, 400)
    time.sleep(1.5)
    shot(page, "tc0013_after_dblclick_canvas.png")


def click_menu_item(page, text_keyword):
    print(f"\n=== 点菜单 '{text_keyword}' ===")
    try:
        loc = page.locator(".cm-item")
        for i in range(loc.count()):
            el = loc.nth(i)
            try:
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if text_keyword in t:
                    el.click(timeout=3000)
                    print(f"  [OK] 点击 [{i}] '{t[:30]}'")
                    return True
            except Exception:
                pass
    except Exception as e:
        print(f"  失败: {e}")
    raise RuntimeError(f"找不到菜单项 '{text_keyword}'")


def wait_for_new_node(page, before, timeout=15):
    print("\n=== 等待新节点 ===")
    start = time.time()
    while time.time() - start < timeout:
        cur = page.locator(".react-flow__node").count()
        if cur > before:
            print(f"  [OK] {before} → {cur}")
            return cur
        time.sleep(1)
    raise RuntimeError("新节点未出现")


def dblclick_node(page):
    print("\n=== 双击节点进入编辑 ===")
    nodes = page.locator(".react-flow__node")
    if nodes.count() == 0:
        raise RuntimeError("画布上没有节点")
    node = nodes.last
    box = node.bounding_box()
    if not box:
        raise RuntimeError("节点没有 bounding_box")
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.dblclick(cx, cy)
    time.sleep(1.5)
    shot(page, "tc0013_after_dblclick_node.png")


def find_editor(page):
    for sel in [
        "[contenteditable='true']",
        "[class*='ProseMirror']",
        "[class*='editor']",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    return el, sel
        except Exception:
            pass
    return None, None


def input_lines(page, lines):
    print(f"\n=== 输入 {len(lines)} 行文字 ===")
    editor, sel = find_editor(page)
    if editor:
        print(f"  编辑区: {sel}")
        try:
            editor.click(timeout=3000)
            time.sleep(0.3)
        except Exception:
            pass
        page.keyboard.press("Control+A")
        time.sleep(0.2)
        page.keyboard.press("Delete")
        time.sleep(0.2)

    for i, line in enumerate(lines):
        for ch in line:
            page.keyboard.type(ch, delay=60)
        if i < len(lines) - 1:
            page.keyboard.press("Enter")
            time.sleep(0.2)
    time.sleep(0.5)
    shot(page, "tc0013_after_input.png")


# ============ 工具栏按钮 ============
def find_toolbar_button(page, title_keyword):
    editor, _ = find_editor(page)
    editor_y = 0
    if editor:
        box = editor.bounding_box()
        if box:
            editor_y = box["y"]

    btns = page.locator("button")
    for i in range(btns.count()):
        el = btns.nth(i)
        try:
            if not el.is_visible():
                continue
            box = el.bounding_box()
            if not box:
                continue
            if not (editor_y - 300 < box["y"] < editor_y + 30):
                continue
            title = (el.get_attribute("title") or "").strip()
            if title_keyword in title:
                return el, title
        except Exception:
            pass
    return None, None


def click_copy_markdown(page):
    print("\n\n########## 点击【复制 Markdown】按钮 ##########")
    btn, title = find_toolbar_button(page, "复制")
    if btn:
        try:
            btn.click(timeout=3000)
            print(f"  [OK] 点击工具栏按钮 title='{title}'")
            time.sleep(1)
            shot(page, "tc0013_after_copy.png")
            return True, title
        except Exception as e:
            print(f"  点击失败: {e}")
            return False, ""
    print("  [FAIL] 找不到复制按钮")
    return False, ""


# ============ 【修正】粘贴到中控台 ============
def paste_to_composer(page):
    """粘贴到页面底部的中控台输入框"""
    print("\n\n########## 粘贴到中控台输入框验证 ##########")

    composer = None

    # 策略 1（最精确）：.promptbox 容器内的 data-lexical-editor
    try:
        promptbox = page.locator(".promptbox").first
        if promptbox.count() > 0:
            inner = promptbox.locator("div[data-lexical-editor='true']").first
            if inner.count() > 0 and inner.is_visible():
                composer = inner
                print("  找到中控台输入框: .promptbox 内的 data-lexical-editor")
    except Exception as e:
        print(f"  策略1失败: {e}")

    # 策略 2：class 含 text-mode 的 .wprompt-ed
    if not composer:
        try:
            loc = page.locator("div.wprompt-ed.text-mode")
            if loc.count() > 0:
                for i in range(loc.count()):
                    el = loc.nth(i)
                    if el.is_visible():
                        composer = el
                        print(f"  找到中控台输入框: div.wprompt-ed.text-mode [{i}]")
                        break
        except Exception as e:
            print(f"  策略2失败: {e}")

    # 策略 3：找 .wprompt-ed 最后一个
    if not composer:
        try:
            loc = page.locator("div.wprompt-ed")
            cnt = loc.count()
            for i in range(cnt - 1, -1, -1):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                composer = el
                print(f"  找到中控台输入框: div.wprompt-ed [{i}]（兜底）")
                break
        except Exception as e:
            print(f"  策略3失败: {e}")

    if not composer:
        print("  [FAIL] 找不到中控台输入框")
        return None

    # 点击中控台输入框（让焦点从节点编辑器转移过来）
    clicked = False
    try:
        composer.click(timeout=3000, force=True)
        time.sleep(0.5)
        clicked = True
        print("  [OK] 点击中控台输入框")
    except Exception as e:
        print(f"  点击失败: {e}")

    if not clicked:
        try:
            composer.evaluate("el => el.focus()")
            time.sleep(0.5)
            print("  [OK] JS 聚焦")
        except Exception as e:
            print(f"  JS 聚焦也失败: {e}")
            return None

    # 验证焦点确实在中控台
    try:
        focused = page.evaluate("""() => {
            const el = document.activeElement;
            if (!el) return null;
            return {
                tag: el.tagName,
                cls: (el.className || '').slice(0, 80),
                editor: el.getAttribute('data-lexical-editor') || '',
                text: (el.innerText || '').slice(0, 50),
            };
        }""")
        print(f"  当前焦点: {focused}")
    except Exception:
        pass

    # 清空
    page.keyboard.press("Control+A")
    time.sleep(0.2)
    page.keyboard.press("Delete")
    time.sleep(0.3)

    # 粘贴
    page.keyboard.press("Control+V")
    time.sleep(1)
    shot(page, "tc0013_after_paste_composer.png")

    # 读内容
    try:
        pasted = composer.evaluate("el => el.innerText || el.textContent || ''")
        print(f"  粘贴后中控台内容: '{pasted[:300]}'")
        return pasted
    except Exception as e:
        print(f"  读取失败: {e}")
        return None


# ============ 点击保存到资产库 ============
def click_save_to_library(page):
    print("\n\n########## 点击【保存到资产库】 ##########")
    btn, title = find_toolbar_button(page, "保存")
    if btn:
        try:
            btn.click(timeout=3000)
            print(f"  [OK] 点击 title='{title}'")
            time.sleep(1.5)
            shot(page, "tc0013_after_click_save.png")
            return True
        except Exception as e:
            print(f"  点击失败: {e}")
            return False
    print("  [FAIL] 找不到保存按钮")
    return False


# ============ 保存弹窗 ============
def handle_save_dialog(page):
    print("\n\n########## 处理保存弹窗 ##########")
    time.sleep(1)

    dialog = None
    for sel in [".cx-modal-panel[role='dialog']", "[role='dialog']", "[class*='modal']"]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if "保存文本到资产库" in t:
                    dialog = el
                    print(f"  找到保存弹窗: {sel} [{i}]")
                    break
            if dialog:
                break
        except Exception:
            pass

    shot(page, "tc0013_save_dialog.png")

    # ============ 选【其他】 ============
    print("\n  选择【其他】分类")
    other_clicked = False

    if dialog:
        # 策略 1：.grid.grid-cols-3 容器内的 button:text-is('其他')
        try:
            cat_grid = dialog.locator(".grid.grid-cols-3").first
            if cat_grid.count() > 0:
                btn = cat_grid.locator("button:text-is('其他')").first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=3000)
                    print("  [OK] 点击 .grid.grid-cols-3 内的【其他】按钮")
                    other_clicked = True
                    time.sleep(0.5)
                    shot(page, "tc0013_after_click_other.png")
        except Exception as e:
            print(f"  策略1失败: {e}")

        # 策略 2：弹窗内 button:text-is('其他')
        if not other_clicked:
            try:
                btn = dialog.locator("button:text-is('其他')").first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=3000)
                    print("  [OK] 点击 button:text-is('其他')")
                    other_clicked = True
                    time.sleep(0.5)
                    shot(page, "tc0013_after_click_other.png")
            except Exception as e:
                print(f"  策略2失败: {e}")

    if not other_clicked:
        print("  [WARN] 没找到【其他】分类")

    # ============ 点【确认保存】 ============
    print("\n  点击【确认保存】")
    confirm_clicked = False

    if dialog:
        try:
            btn = dialog.locator("button:has-text('确认保存')").first
            if btn.count() > 0:
                btn.click(timeout=3000)
                print("  [OK] 点击弹窗内【确认保存】")
                confirm_clicked = True
                time.sleep(2)
                shot(page, "tc0013_after_confirm_save.png")
        except Exception as e:
            print(f"  弹窗内定位失败: {e}")

    if not confirm_clicked:
        try:
            btn = page.get_by_role("button", name="确认保存").first
            if btn.count() > 0:
                btn.click(timeout=3000)
                print("  [OK] 通过 role=button 点击【确认保存】")
                confirm_clicked = True
                time.sleep(2)
                shot(page, "tc0013_after_confirm_save.png")
        except Exception as e:
            print(f"  role 定位失败: {e}")

    feedback = []
    time.sleep(1)
    for kw in ["保存成功", "已保存", "成功"]:
        try:
            loc = page.get_by_text(kw, exact=False)
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    t = (el.inner_text() or "").strip()[:60]
                    if t:
                        feedback.append(t)
        except Exception:
            pass

    if feedback:
        print(f"  [OK] 找到反馈: {feedback[:3]}")
    else:
        print("  [WARN] 没找到成功反馈（弹窗消失也算成功）")

    shot(page, "tc0013_after_save_feedback.png")
    return other_clicked, confirm_clicked, feedback


# ============ 资产库分类标签 ============
def click_asset_category_tab(page, tab_text, container=None):
    print(f"  点击资产库分类【{tab_text}】")

    cattabs = None
    if container:
        try:
            cand = container.locator(".am-cattabs")
            if cand.count() > 0:
                cattabs = cand.first
                print("    在弹窗内找到 .am-cattabs")
        except Exception:
            pass

    if not cattabs:
        try:
            cand = page.locator(".am-cattabs")
            if cand.count() > 0:
                cattabs = cand.first
                print("    在页面找到 .am-cattabs")
        except Exception:
            pass

    if not cattabs:
        print("    [WARN] 找不到 .am-cattabs")
        return False

    # 策略 1：.cx-chip-label 文字精确匹配
    try:
        label = cattabs.locator(".cx-chip-label").filter(
            has_text=re.compile(rf"^{re.escape(tab_text)}$")
        ).first
        if label.count() > 0 and label.is_visible():
            try:
                chip = label.locator("xpath=..")
                chip.click(timeout=3000)
                print("    [OK] 点击 .cx-chip-label 的父级 .cx-chip")
            except Exception:
                label.click(timeout=3000)
                print("    [OK] 点击 .cx-chip-label")
            return True
    except Exception as e:
        print(f"    策略1失败: {e}")

    # 策略 2：.cx-chip 文字精确匹配
    try:
        chip = cattabs.locator(f".cx-chip:text-is('{tab_text}')").first
        if chip.count() > 0 and chip.is_visible():
            chip.click(timeout=3000)
            print("    [OK] 点击 .cx-chip:text-is")
            return True
    except Exception as e:
        print(f"    策略2失败: {e}")

    # 策略 3：cattabs 内精确文本
    try:
        el = cattabs.get_by_text(tab_text, exact=True).first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=3000)
            print("    [OK] 通过精确文本点击")
            return True
    except Exception as e:
        print(f"    策略3失败: {e}")

    return False


# ============ 验证资产管理 ============
def check_asset_library(page):
    print("\n\n########## 验证资产管理 ##########")

    print("  点击左侧【资产管理】")
    clicked = False
    for sel in [
        "[aria-label='资产管理']",
        "[title='资产管理']",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click(timeout=3000)
                print(f"  [OK] 点击 '{sel}'")
                clicked = True
                time.sleep(2)
                shot(page, "tc0013_after_click_asset.png")
                break
        except Exception:
            pass

    if not clicked:
        try:
            el = page.get_by_role("button", name="资产管理").first
            if el.count() > 0 and el.is_visible():
                el.click(timeout=3000)
                print("  [OK] 通过 role=button 点击资产管理")
                clicked = True
                time.sleep(2)
                shot(page, "tc0013_after_click_asset.png")
        except Exception as e:
            print(f"  role 定位失败: {e}")

    if not clicked:
        print("  [FAIL] 找不到资产管理按钮")
        return None

    asset_panel = None
    for sel in [".cx-modal-panel[role='dialog']", "[role='dialog']", "[class*='modal']"]:
        try:
            loc = page.locator(sel)
            for i in range(loc.count()):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                t = (el.inner_text() or "").strip()
                if "资产管理" in t:
                    asset_panel = el
                    print(f"  找到资产管理弹窗: {sel} [{i}]")
                    break
            if asset_panel:
                break
        except Exception:
            pass

    print("\n  点击分类标签【其他】")
    other_clicked = False
    if asset_panel:
        other_clicked = click_asset_category_tab(page, "其他", container=asset_panel)
    else:
        other_clicked = click_asset_category_tab(page, "其他")

    if other_clicked:
        time.sleep(1.5)
        shot(page, "tc0013_asset_other.png")
    else:
        print("  [WARN] 没点中【其他】分类标签")

    print("\n  检查是否有保存的文本")
    found = False
    try:
        loc = page.get_by_text(LINE1, exact=False)
        for i in range(loc.count()):
            el = loc.nth(i)
            if el.is_visible():
                print(f"  [OK] 找到文本 '{LINE1}'")
                found = True
                break
    except Exception:
        pass

    try:
        loc = page.get_by_text("资产库文本内容", exact=False)
        for i in range(loc.count()):
            el = loc.nth(i)
            if el.is_visible():
                print(f"  [OK] 找到资产名称「资产库文本内容」")
                found = True
                break
    except Exception:
        pass

    if not found:
        print("  [WARN] 资产管理里没找到刚保存的文本")

    shot(page, "tc0013_final_asset_library.png")
    return {"other_clicked": other_clicked, "found": found}


# ============ 主流程 ============
def test_tc0013():
    print("=== TC-0013：文本节点复制 Markdown + 保存资产库 ===")

    if not is_cdp_ready():
        raise RuntimeError("CDP 未就绪")

    pw, browser, page = connect()

    try:
        node_count_before = page.locator(".react-flow__node").count()
        print(f"[INFO] 初始节点数: {node_count_before}")

        # 1. 新建文本节点
        dblclick_canvas(page)
        click_menu_item(page, "文本节点")
        time.sleep(1.5)
        wait_for_new_node(page, node_count_before, timeout=15)

        # 2. 双击节点进入编辑
        dblclick_node(page)

        # 3. 输入三行文字
        input_lines(page, [LINE1, LINE2, LINE3])

        # 4. 点击复制 Markdown（工具栏按钮）
        copy_ok, copy_title = click_copy_markdown(page)

        clipboard_text = ""
        if copy_ok:
            time.sleep(0.5)
            try:
                clipboard_text = page.evaluate("() => navigator.clipboard.readText()")
            except Exception as e:
                print(f"  读剪贴板失败: {e}")
            print(f"\n  剪贴板内容: '{clipboard_text[:300]}'")

        # 5. 粘贴到中控台
        pasted_text = paste_to_composer(page)
        pasted_ok = (
            pasted_text
            and LINE1 in pasted_text
            and LINE2 in pasted_text
            and LINE3 in pasted_text
        )
        print(f"\n  粘贴内容含三行文字: {pasted_ok}")

        try:
            page.keyboard.press("Control+A")
            time.sleep(0.2)
            page.keyboard.press("Delete")
            time.sleep(0.3)
        except Exception:
            pass

        # 6. 重新进入节点编辑
        nodes = page.locator(".react-flow__node")
        if nodes.count() == 0:
            print("  [WARN] 画布上没有节点，重建")
            dblclick_canvas(page)
            click_menu_item(page, "文本节点")
            time.sleep(1.5)
            wait_for_new_node(page, 0, timeout=15)

        dblclick_node(page)
        time.sleep(1)

        save_ok = click_save_to_library(page)

        # 7. 处理保存弹窗
        other_clicked, confirm_clicked, feedback = handle_save_dialog(page)

        # 8. 验证资产管理
        asset_result = check_asset_library(page)

        # ============ 汇总 ============
        print("\n\n=== 结果汇总 ===")
        print(f"  {'✅' if copy_ok else '❌'} 点击复制 Markdown")
        print(f"  {'✅' if clipboard_text else '❌'} 剪贴板非空")
        print(f"  {'✅' if pasted_ok else '❌'} 粘贴到中控台，含三行文字")
        print(f"  {'✅' if save_ok else '❌'} 点击保存到资产库")
        print(f"  {'✅' if other_clicked else '❌'} 弹窗中选【其他】分类")
        print(f"  {'✅' if confirm_clicked else '❌'} 点击【确认保存】")
        print(f"  {'✅' if feedback else '⚠️'} 保存反馈: {len(feedback)} 条")
        if asset_result:
            print(f"  {'✅' if asset_result['other_clicked'] else '❌'} 资产库点【其他】标签")
            print(f"  {'✅' if asset_result['found'] else '❌'} 资产库找到保存的文本")

        # ============ 断言 ============
        print("\n\n=== 断言 ===")
        errors = []

        if not copy_ok:
            errors.append("复制 Markdown 按钮点击失败")
        if not pasted_ok:
            errors.append("粘贴到中控台后内容不对")
        if not save_ok:
            errors.append("保存到资产库按钮点击失败")
        if not confirm_clicked:
            errors.append("确认保存按钮点击失败")
        if asset_result:
            if not asset_result["other_clicked"]:
                errors.append("资产库未成功点击【其他】分类标签")
            if not asset_result["found"]:
                errors.append("资产管理中未找到保存的文本")
        else:
            errors.append("未能打开资产管理")

        print("\n" + "=" * 60)
        if errors:
            print(f"[FAIL] TC-0013，共 {len(errors)} 项：")
            for e in errors:
                print(f"  - {e}")
            print("=" * 60)
            raise AssertionError("TC-0013 未通过")

        print("[PASS] TC-0013 通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shot(page, "tc0013_error.png")
        sys.exit(1)
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    test_tc0013()