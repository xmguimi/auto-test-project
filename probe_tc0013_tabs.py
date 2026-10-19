"""
诊断保存弹窗的 DOM 结构
前提：手动点击了「保存到资产库」，保存弹窗保持打开
"""
import time
import requests
from playwright.sync_api import sync_playwright

PORT = 9222

if requests.get(f"http://localhost:{PORT}/json/version", timeout=1).status_code != 200:
    print("CDP 未就绪")
    exit()

pw = sync_playwright().start()
browser = pw.chromium.connect_over_cdp(f"http://localhost:{PORT}")
pages = browser.contexts[0].pages
page = None
for p in pages:
    if "帧境" in (p.title() or ""):
        page = p
        break
if not page:
    page = pages[0]

print(f"页面: {page.title()}")
print("3 秒后开始诊断（请确保保存弹窗已打开）...")
time.sleep(3)

print("\n========== 诊断 1：找「保存文本到资产库」弹窗 ==========")
result = page.evaluate("""() => {
    const all = document.querySelectorAll('*');
    for (const el of all) {
        const t = el.textContent || '';
        if (t.includes('保存文本到资产库') && t.includes('资产分类') && t.includes('提示词') && el.children.length < 30) {
            return {
                tag: el.tagName,
                className: el.className,
                role: el.getAttribute('role') || '',
                childCount: el.children.length,
                innerHTML: el.outerHTML.slice(0, 3000),
            };
        }
    }
    return null;
}""")

if result:
    print(f"  tag={result['tag']}")
    print(f"  class={result['className']}")
    print(f"  role={result['role']}")
    print(f"  childCount={result['childCount']}")
    print(f"\n  innerHTML:\n{result['innerHTML']}")
else:
    print("  没找到保存弹窗")

print("\n\n========== 诊断 2：保存弹窗里所有 button ==========")
# 找弹窗
dialog = None
for sel in ["[role='dialog']", "[class*='modal-panel']", "[class*='modal']"]:
    try:
        loc = page.locator(sel)
        for i in range(loc.count()):
            el = loc.nth(i)
            if not el.is_visible():
                continue
            t = (el.inner_text() or "")
            if "保存文本到资产库" in t:
                dialog = el
                print(f"  弹窗: {sel} [{i}]")
                break
        if dialog:
            break
    except Exception:
        pass

if dialog:
    btns = dialog.locator("button")
    print(f"  弹窗内共 {btns.count()} 个 button：")
    for i in range(btns.count()):
        b = btns.nth(i)
        try:
            if not b.is_visible():
                continue
            t = (b.inner_text() or "").strip()[:30]
            cls = b.get_attribute("class") or ""
            print(f"    [{i}] text='{t}' class='{cls[:100]}'")
        except Exception:
            pass

    # 也看 span / div
    print("\n  弹窗内所有含「其他」「提示词」「Agent」的元素：")
    for kw in ["其他", "提示词", "Agent"]:
        loc = dialog.get_by_text(kw, exact=True)
        for i in range(loc.count()):
            el = loc.nth(i)
            if not el.is_visible():
                continue
            tag = el.evaluate("el => el.tagName")
            cls = el.get_attribute("class") or ""
            box = el.bounding_box()
            parent_tag = el.locator("xpath=..").first.evaluate("el => el.tagName")
            parent_cls = el.locator("xpath=..").first.get_attribute("class") or ""
            print(f"    '{kw}' tag={tag} class='{cls[:60]}' pos=({box['x']:.0f},{box['y']:.0f})")
            print(f"      父级: {parent_tag} class='{parent_cls[:80]}'")

print("\n=== 诊断完成 ===")

browser.close()
pw.stop()