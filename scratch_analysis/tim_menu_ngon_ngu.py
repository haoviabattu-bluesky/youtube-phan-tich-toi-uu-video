# -*- coding: utf-8 -*-
r"""Tim cho doi ngon ngu hien thi YouTube cua tai khoan GEO (menu avatar / trang account).

  env -u PYTHONPATH py -3.13 scratch_analysis/tim_menu_ngon_ngu.py
"""
import os, sys, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp

OUT = os.path.join(ROOT, "reports", "geo_chan_doan")
os.makedirs(OUT, exist_ok=True)

DEEP_TEXT = """() => {
    const parts = [];
    const walk = (root) => {
        root.querySelectorAll('*').forEach(e => {
            if (e.children.length === 0) { const t = (e.textContent||'').trim(); if (t) parts.push(t); }
            if (e.shadowRoot) walk(e.shadowRoot);
        });
    };
    walk(document);
    return parts;
}"""


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


with dp.open_group({"engine": "gpm", "mail": "normaneileenpm218@gmail.com"}, log) as (ws, launched):
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front()
        page.set_default_timeout(60000)
        page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        # bam avatar goc tren phai
        av = page.evaluate("""() => {
            const cands = [...document.querySelectorAll('button#avatar-btn, ytd-topbar-menu-button-renderer button, #avatar-btn')];
            const e = cands[0];
            if (!e) return null;
            const r = e.getBoundingClientRect(); e.click();
            return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""")
        log("click avatar:", json.dumps(av))
        time.sleep(4)
        parts = page.evaluate(DEEP_TEXT)
        log("menu (loc):", " | ".join([p for p in parts if len(p) < 40][:60])[:900])
        page.screenshot(path=os.path.join(OUT, "avatar_menu.png"))
        # thu trang account_language cu
        for u in ("https://www.youtube.com/account_language",):
            try:
                page.goto(u, wait_until="domcontentloaded", timeout=45000)
                time.sleep(4)
                log(u, "->", page.url[:90])
                t = page.evaluate(DEEP_TEXT)
                log("  text:", " | ".join(t[:40])[:500])
            except Exception as e:
                log(u, "loi:", str(e)[:80])
        try:
            page.close()
        except Exception:
            pass
        if launched:
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:
                pass
