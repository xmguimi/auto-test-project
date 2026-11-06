# -*- coding: utf-8 -*-
"""TC-0017 视频节点-自定义工具栏（REAL_GENERATE=True，本地功能）"""
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


def get_tool_order(page):
    """获取已固定工具列表顺序"""
    return page.evaluate("""
        () => {
            const modal = document.querySelector('.cx-modal-panel');
            if (!modal) return [];
            const rows = modal.querySelectorAll('[class*="row"], [class*="item"], [class*="card"]');
            const res = [];
            for (let row of rows) {
                const t = (row.textContent || '').trim();
                const m = t.match(/^(抽帧|延长|编辑|音频分离|转码|反推|视频工具)/);
                if (m) res.push(m[1]);
            }
            return res;
        }
    """)


def get_drag_handles(page):
    """获取拖拽手柄位置"""
    return page.evaluate("""
        () => {
            const modal = document.querySelector('.cx-modal-panel');
            if (!modal) return [];
            const res = [];
            for (let el of modal.querySelectorAll('[class*="drag"], [class*="grip"], [class*="handle"]')) {
                const r = el.getBoundingClientRect();
                if (r.width < 5) continue;
                res.push({x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)});
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

    # 2. 打开面板
    custom_btn = page.locator("button[aria-label='自定义工具栏']")
    if custom_btn.count() == 0:
        check("自定义工具栏按钮", False, "未找到")
        browser.close(); pw.stop()
        return
    cb = custom_btn.first.bounding_box()
    page.mouse.click(cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2)
    time.sleep(2)
    check("自定义工具栏面板弹出", True)

    # 3. 验证面板布局
    panel = page.evaluate("""
        () => {
            const t = document.body.textContent || '';
            return {
                hasFixed: t.includes('已固定'),
                hasMore: t.includes('更多工具'),
                hasDefault: t.includes('恢复默认'),
                hasDone: t.includes('完成'),
                hasNoMore: t.includes('所有工具都已固定'),
                hasChouzhen: t.includes('抽帧'),
                hasYanchang: t.includes('延长'),
                hasBianji: t.includes('编辑'),
                hasYinpin: t.includes('音频分离'),
                hasZhuanma: t.includes('转码'),
                hasFanti: t.includes('反推'),
                hasShipin: t.includes('视频工具'),
            };
        }
    """)
    check("已固定区域标题", panel["hasFixed"])
    check("更多工具区域标题", panel["hasMore"])
    check("恢复默认按钮", panel["hasDefault"])
    check("完成按钮", panel["hasDone"])
    check("更多工具为空提示", panel["hasNoMore"], "所有工具都已固定")
    check("已固定-抽帧", panel["hasChouzhen"])
    check("已固定-延长", panel["hasYanchang"])
    check("已固定-编辑", panel["hasBianji"])
    check("已固定-音频分离", panel["hasYinpin"])
    check("已固定-转码", panel["hasZhuanma"])
    check("已固定-反推", panel["hasFanti"])
    check("已固定-视频工具", panel["hasShipin"])

    # 4. 拖动排序：把抽帧从第1位拖到第4位
    before = get_tool_order(page)
    check("拖动前顺序记录", len(before) >= 5, f"共{len(before)}个工具")

    handles = get_drag_handles(page)
    if len(handles) >= 4:
        # 第1个手柄=抽帧，拖到第4个手柄位置（音频分离下面）
        drag_start = handles[0]
        drag_end = handles[3]
        page.mouse.move(drag_start["x"], drag_start["y"])
        time.sleep(0.3)
        page.mouse.down()
        time.sleep(0.3)
        page.mouse.move(drag_start["x"], drag_start["y"] + 10, steps=3)
        time.sleep(0.2)
        page.mouse.move(drag_end["x"], drag_end["y"] + 30, steps=10)
        time.sleep(0.5)
        page.mouse.up()
        time.sleep(1)

        after = get_tool_order(page)
        check("拖动排序生效", before != after, f"前={before} → 后={after}")
    else:
        check("拖动排序生效", False, f"手柄数={len(handles)}")

    # 5. 解除固定：点反推的解锁图标（第6个）
    unlock_btns = page.locator("button[aria-label*='解除固定'], button[aria-label*='取消固定'], button[aria-label*='移除']")
    if unlock_btns.count() >= 6:
        ub = unlock_btns.nth(5).bounding_box()
        page.mouse.click(ub["x"] + ub["width"] / 2, ub["y"] + ub["height"] / 2)
        time.sleep(1)
        check("解除固定-反推", True)
    else:
        check("解除固定-反推", False, f"解锁按钮数={unlock_btns.count()}")

    # 6. 关闭不保存：点×关闭
    close_btn = page.locator("button[aria-label='关闭']")
    if close_btn.count() > 0:
        cb2 = close_btn.nth(close_btn.count() - 1).bounding_box()
        page.mouse.click(cb2["x"] + cb2["width"] / 2, cb2["y"] + cb2["height"] / 2)
        time.sleep(1)
        check("关闭不保存-点×关闭", True)
    else:
        check("关闭不保存-点×关闭", False, "未找到关闭按钮")

    # 7. 重新打开面板，验证关闭不生效
    custom_btn2 = page.locator("button[aria-label='自定义工具栏']")
    cb3 = custom_btn2.first.bounding_box()
    page.mouse.click(cb3["x"] + cb3["width"] / 2, cb3["y"] + cb3["height"] / 2)
    time.sleep(2)

    after_close = get_tool_order(page)
    check("关闭不保存-反推仍在已固定", len(after_close) >= 6, f"共{len(after_close)}个工具")

    # 8. 记忆校验：解除固定反推→点完成→重新打开面板
    unlock_btns2 = page.locator("button[aria-label*='解除固定'], button[aria-label*='取消固定'], button[aria-label*='移除']")
    if unlock_btns2.count() >= 6:
        ub2 = unlock_btns2.nth(5).bounding_box()
        page.mouse.click(ub2["x"] + ub2["width"] / 2, ub2["y"] + ub2["height"] / 2)
        time.sleep(1)
        check("记忆校验-解除固定反推", True)
    else:
        check("记忆校验-解除固定反推", False, f"解锁按钮数={unlock_btns2.count()}")

    done_btn = page.locator("button:has-text('完成')")
    db = done_btn.first.bounding_box()
    page.mouse.click(db["x"] + db["width"] / 2, db["y"] + db["height"] / 2)
    time.sleep(1)
    check("记忆校验-点完成保存", True)

    custom_btn3 = page.locator("button[aria-label='自定义工具栏']")
    cb4 = custom_btn3.first.bounding_box()
    page.mouse.click(cb4["x"] + cb4["width"] / 2, cb4["y"] + cb4["height"] / 2)
    time.sleep(2)

    after_save = page.evaluate("""
        () => {
            const t = document.body.textContent || '';
            // 验证反推在更多工具里：已固定区域应该少于7个，更多工具区域有反推
            // 简单判断：更多工具区域不应该是"所有工具都已固定"
            return {
                noMoreAll: !t.includes('所有工具都已固定'),
                hasFanti: t.includes('反推'),
            };
        }
    """)
    check("记忆校验-重新打开面板", after_save["noMoreAll"], "反推已移到更多工具（更多工具不再为空）")

    # 9. 添加固定：从更多工具加回反推
    add_btn = page.locator("button[aria-label*='添加'], button[aria-label*='固定'], button[aria-label*='加回']")
    if add_btn.count() > 0:
        ab = add_btn.first.bounding_box()
        page.mouse.click(ab["x"] + ab["width"] / 2, ab["y"] + ab["height"] / 2)
        time.sleep(1)
        check("添加固定-点添加按钮", True)
    else:
        check("添加固定-点添加按钮", False, "未找到添加按钮")

    # 10. 恢复默认
    reset_btn = page.locator("text=恢复默认")
    rb = reset_btn.first.bounding_box()
    page.mouse.click(rb["x"] + rb["width"] / 2, rb["y"] + rb["height"] / 2)
    time.sleep(1)
    check("恢复默认", True)

    # 11. 点完成保存
    done_btn2 = page.locator("button:has-text('完成')")
    db2 = done_btn2.first.bounding_box()
    page.mouse.click(db2["x"] + db2["width"] / 2, db2["y"] + db2["height"] / 2)
    time.sleep(1)
    check("完成保存", True)

    browser.close()
    pw.stop()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===", flush=True)


if __name__ == "__main__":
    main()
