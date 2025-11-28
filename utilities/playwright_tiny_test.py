# yt_quick_test.py
from playwright.sync_api import sync_playwright
MIN_OBS = "() => { window.__m = []; const o=new MutationObserver(m=>{ m.forEach(r=> window.__m.push({type:r.type, added:r.addedNodes.length, removed:r.removedNodes.length, target: r.target && r.target.tagName})); }); o.observe(document, {childList:true, subtree:true, attributes:true}); window.__m_ob=o; return true; }"
READ_OBS = "() => (window.__m || []).slice(-40)"
CLEAR_OBS = "() => { if(window.__m) window.__m = []; return true; }"

def quick_test(url, selectors):
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        p = b.new_page()
        p.goto(url, wait_until="domcontentloaded", timeout=60000)
        results = {}
        for sel in selectors:
            r = {"exists": False, "aria": {}, "hover_mutation": False, "click_mutation": False}
            try:
                el = p.query_selector(sel)
                if not el:
                    results[sel] = r; continue
                r["exists"] = True
                # read aria attrs
                r["aria"] = {
                    "aria-haspopup": el.get_attribute("aria-haspopup"),
                    "aria-expanded": el.get_attribute("aria-expanded"),
                    "aria-controls": el.get_attribute("aria-controls"),
                    "role": el.get_attribute("role"),
                    "title": el.get_attribute("title")
                }
                # hover test
                p.evaluate(MIN_OBS)
                try:
                    el.hover(force=True)
                except: pass
                p.wait_for_timeout(250)
                muts = p.evaluate(READ_OBS)
                r["hover_mutation"] = len(muts) > 0
                p.evaluate(CLEAR_OBS)
                # click test (avoid navigation where obvious by preventing default if possible)
                p.evaluate(MIN_OBS)
                try:
                    # try a JS click to allow prevention handlers to run without navigation in many cases
                    p.evaluate("(s)=>{ const e=document.querySelector(s); if(!e) return null; e.click(); return true; }", sel)
                except:
                    try:
                        el.click(force=True)
                    except:
                        pass
                p.wait_for_timeout(350)
                muts2 = p.evaluate(READ_OBS)
                r["click_mutation"] = len(muts2) > 0
                # if aria-expanded changed after click, that's a strong signal
                after_exp = p.evaluate("(s)=>{ const e=document.querySelector(s); return e ? e.getAttribute('aria-expanded') : null }", sel)
                if r["aria"].get("aria-expanded") != after_exp:
                    r.setdefault("notes", []).append(f"aria-expanded flipped {r['aria'].get('aria-expanded')} -> {after_exp}")
                results[sel] = r
            except Exception as e:
                results[sel] = {"error": str(e)[:200]}
        b.close()
        return results

if __name__ == "__main__":
    sels = [
 'a.yt-spec-button-shape-next.yt-spec-button-shape-next--outline',
 'input.ytSearchboxComponentInput.yt-searchbox-input',
 'a.yt-simple-endpoint.style-scope',
 'a#logo.yt-simple-endpoint.style-scope',
 'button.yt-spec-button-shape-next.yt-spec-button-shape-next--tonal',
 'button.ytSearchboxComponentSearchButton',
 'button.yt-spec-button-shape-next.yt-spec-button-shape-next--text',
 'a#endpoint.yt-simple-endpoint.style-scope',
 'ytd-mini-guide-entry-renderer.style-scope.ytd-mini-guide-renderer',
 'yt-icon-button#guide-button.style-scope.ytd-masthead',
 'ytd-topbar-menu-button-renderer.style-scope.ytd-masthead'
    ]
    out = quick_test("https://www.youtube.com", sels)
    import json, pprint
    pprint.pprint(out)
