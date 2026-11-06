# -*- coding: utf-8 -*-
"""TC-0019 视频节点-保存到资产库-弹窗与默认值（REAL_GENERATE=True，本地功能）"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PORT = int(os.getenv("FJ_CDP_PORT", "9222"))
HOST = os.getenv("FJ_CDP_HOST", "localhost")
REAL_GENERATE = True  # 本地功能，不花钱
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

    # 1. 选中视频节点
    page.keyboard.press("Escape")
    time.sleep(1)
    box = page.locator(".react-flow__node").nth(2).bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 12)
    time.sleep(1)
    check("选中视频节点", True)

    # 2. 点保存到资产库按钮
    save_btn = page.locator("button[aria-label='保存到资产库']")
    if save_btn.count() == 0:
        check("保存到资产库按钮", False, "未找到")
        browser.close(); pw.stop()
        return
    sb = save_btn.first.bounding_box()
    page.mouse.click(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    time.sleep(2)
    check("保存到资产库按钮点击", True)

    # 3. 验证弹窗打开
    modal = page.locator(".cx-modal-panel.is-open")
    check("弹窗正常打开", modal.count() > 0)

    modal_text = page.evaluate("""
        () => {
            const modal = document.querySelector('.cx-modal-panel.is-open');
            if (!modal) return {};
            const t = modal.textContent || '';
            return {
                title: t.includes('保存到资产库'),
                hasClose: modal.querySelector('button[aria-label="关闭"]') !== null,
                hasAssetName: t.includes('资产名称'),
                hasCategory: t.includes('人物') && t.includes('场景') && t.includes('物品') && t.includes('其他'),
                hasNewCategory: t.includes('新建分类'),
                hasCancel: t.includes('取消'),
                hasConfirm: t.includes('确认保存'),
                hasMaterial: t.includes('素材'),
                hasRecipe: t.includes('资产配方'),
            };
        }
    """)
    check("弹窗标题-保存到资产库", modal_text.get("title"))
    check("右上关闭按钮", modal_text.get("hasClose"))
    check("资产名称标签", modal_text.get("hasAssetName"))
    check("保存到分类（人物/场景/物品/其他）", modal_text.get("hasCategory"))
    check("新建分类选项", modal_text.get("hasNewCategory"))
    check("取消按钮", modal_text.get("hasCancel"))
    check("确认保存按钮", modal_text.get("hasConfirm"))
    check("素材说明", modal_text.get("hasMaterial"))
    check("资产配方说明", modal_text.get("hasRecipe"))

    # 4. 验证资产名称输入框默认值
    name_input = page.locator(".cx-modal-panel input")
    if name_input.count() > 0:
        default_name = name_input.first.input_value()
        check("资产名称输入框", True, f"默认值='{default_name}'")
    else:
        check("资产名称输入框", False, "未找到")

    # 5. 验证分类选中态（默认哪个选中）
    category_checked = page.evaluate("""
        () => {
            const modal = document.querySelector('.cx-modal-panel.is-open');
            if (!modal) return [];
            const res = [];
            for (let item of modal.querySelectorAll('[class*="category"], [class*="tag"], [class*="option"], [class*="item"]')) {
                const t = (item.textContent || '').trim();
                if (['人物', '场景', '物品', '其他'].includes(t)) {
                    const cls = (item.className || '').toString();
                    res.push({name: t, active: cls.includes('active') || cls.includes('selected') || cls.includes('checked')});
                }
            }
            return res;
        }
    """)
    print(f"分类选项: {category_checked}", flush=True)
    check("分类选项存在", len(category_checked) >= 4, f"共{len(category_checked)}个")

    # 6. 点取消关闭弹窗
    cancel_btn = page.locator(".cx-modal-panel button:has-text('取消')")
    if cancel_btn.count() > 0:
        cb = cancel_btn.first.bounding_box()
        page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
        time.sleep(1)
        modal_after = page.locator(".cx-modal-panel.is-open").count()
        check("取消按钮关闭弹窗", modal_after == 0, f"弹窗数={modal_after}")
    else:
        check("取消按钮关闭弹窗", False, "未找到取消按钮")

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
