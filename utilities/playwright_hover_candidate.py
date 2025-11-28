from playwright.sync_api import Page
from playwright.sync_api import sync_playwright


def collect_candidates(page: Page, limit: int = 30):
    js = """
    () => {
      const set = new Set();
      const add = (el) => {
        if (!el || !el.tagName) return;
        let s = el.tagName.toLowerCase();
        if (el.id) s += '#' + el.id;
        if (el.className && typeof el.className === 'string') {
          const cs = el.className.split(/\\s+/).filter(Boolean).slice(0,2).join('.');
          if (cs) s += '.' + cs;
        }
        set.add(s);
      };
      const hints = ['[aria-haspopup]','[aria-controls]','[role="button"]','[data-tooltip]','[data-menu]','[data-dropdown]','[tabindex]','[title]'];
      for (const q of hints) try { document.querySelectorAll(q).forEach(add); } catch(e){}
      // light :hover scan (may skip cross-origin sheets)
      for (const ss of Array.from(document.styleSheets)) {
        try {
          for (const r of ss.cssRules || []) {
            if ((r.selectorText||'').includes(':hover')) {
              const left = r.selectorText.split(',').map(x=>x.trim().split(':hover')[0].trim())[0];
              try { document.querySelectorAll(left).forEach(add); } catch(e){}
            }
          }
        } catch(e){}
      }
      return Array.from(set).slice(0, 500);
    }
    """
    raw = page.evaluate(js)
    # quick visibility filter
    out = []
    for s in raw:
        try:
            bbox = page.evaluate("(sel)=>{ const e=document.querySelector(sel); if(!e) return null; const r=e.getBoundingClientRect(); const cs=window.getComputedStyle(e); if(cs.display==='none'||cs.visibility==='hidden') return null; return {w:r.width,h:r.height}; }", s)
            if bbox and bbox.get("w",0)*bbox.get("h",0) > 4:
                out.append(s)
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out



def verify_hover(page, selector: str, wait_ms: int = 250):
    inject = """
    () => {
      window.__mv = window.__mv || {mutations:[]};
      if(window.__m_obs) window.__m_obs.disconnect();
      const ob = new MutationObserver((mrs)=>{
        for(const m of mrs){
          for(const n of m.addedNodes) {
            try { window.__mv.mutations.push({tag: n.tagName, id: n.id||null, cls: n.className||null, outer: n.outerHTML? n.outerHTML.slice(0,200): null}); } catch(e){}
          }
        }
      });
      window.__m_obs = ob;
      ob.observe(document, {childList:true, subtree:true});
      return true;
    }
    """
    page.evaluate(inject)
    try:
        page.hover(selector, force=True)
    except Exception:
        pass
    page.wait_for_timeout(wait_ms)
    muts = page.evaluate("() => (window.__mv && window.__mv.mutations) ? window.__mv.mutations.slice(-30) : []")
    visible = page.evaluate("""
    () => {
      const res=[];
      document.querySelectorAll('body *').forEach(e=>{
        try {
          const r=e.getBoundingClientRect();
          const cs=window.getComputedStyle(e);
          if(r.width*r.height>8 && cs.display!=='none' && cs.visibility!=='hidden' && cs.opacity!=='0') {
            res.push({tag:e.tagName.toLowerCase(), id:e.id||null, cls: e.className? e.className.split(/\\s+/).slice(0,3).join(' '): null});
          }
        } catch(e){}
      });
      return res.slice(-30);
    }
    """)
    # merge and dedupe safely by stringifying key components
    found = muts + visible
    seen = set()
    out = []
    for f in found:
        # safe stringify of each key component
        t = f.get('tag'); i = f.get('id'); c = f.get('cls')
        key = ("" if t is None else str(t), "" if i is None else str(i), "" if c is None else str(c))
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    success = len(out) > 0
    return {"selector": selector, "success": bool(success and len(out)>0), "reveals": out[:10]}



def verify_click(page: Page, selector: str, wait_ms: int = 300):
    before = page.evaluate("(s)=>{const e=document.querySelector(s); if(!e) return null; return {aria: e.getAttribute('aria-expanded'), controls: e.getAttribute('aria-controls')};}", selector)
    # simple observer to capture adds/removals
    page.evaluate("""
    () => {
      window.__mc = window.__mc || {mutations:[]};
      if(window.__m2) window.__m2.disconnect();
      const ob = new MutationObserver((mrs)=>{
        for(const m of mrs){
          if(m.addedNodes) for(const n of m.addedNodes) try { window.__mc.mutations.push({type:'add', tag:n.tagName, id:n.id||null, cls:n.className||null}); } catch(e){}
          if(m.removedNodes) for(const n of m.removedNodes) try { window.__mc.mutations.push({type:'remove', tag:n.tagName, id:n.id||null, cls:n.className||null}); } catch(e){}
        }
      });
      window.__m2 = ob;
      ob.observe(document, {childList:true, subtree:true});
      return true;
    }
    """)
    try:
        page.click(selector, force=True)
    except Exception:
        pass
    page.wait_for_timeout(wait_ms)
    muts = page.evaluate("() => (window.__mc && window.__mc.mutations) ? window.__mc.mutations.slice(-40) : []")
    after = page.evaluate("(s)=>{const e=document.querySelector(s); if(!e) return null; return {aria: e.getAttribute('aria-expanded'), controls: e.getAttribute('aria-controls')};}", selector)
    # visible node scan
    visible = page.evaluate("""
    () => {
      const out=[];
      document.querySelectorAll('body *').forEach(e=>{
        try {
          const r=e.getBoundingClientRect();
          const cs=window.getComputedStyle(e);
          if(r.width*r.height>8 && cs.display!=='none' && cs.visibility!=='hidden' && cs.opacity!=='0') out.push({tag:e.tagName.toLowerCase(), id:e.id||null, cls:e.className? e.className.split(/\\s+/).slice(0,3).join(' '): null});
        } catch(e){}
      });
      return out.slice(-40);
    }
    """)
    aria_changed = False
    if before and after and before.get("aria") != after.get("aria"):
        aria_changed = True
    opened = bool(muts or aria_changed or len(visible)>0)
    # return small summary
    return {"selector": selector, "opened": opened, "aria_changed": aria_changed, "mutations": muts[:10], "visible": visible[:10]}



def run_gherkin(url):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded')
        cands = collect_candidates(page, limit=15)

        results = {'candidates': cands, 'hover': [], 'click': []}
        for s in cands:
            h = verify_hover(page, s)
            results['hover'].append(h)

            c = verify_click(page, s)
            results['click'].append(c)
        browser.close()


    return results



if __name__ == "__main__":
    print(run_gherkin("https://www.youtube.com/"))

