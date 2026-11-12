# -*- coding: utf-8 -*-
r"""DOI NGON NGU HIEN THI cua tai khoan GEO sang English (US) de tool doc duoc nhan tieng Anh.

Menu avatar -> "Ngôn ngữ hiển thị: Tiếng Việt" -> "English (US)".

  env -u PYTHONPATH py -3.13 scratch_analysis/doi_ngon_ngu_en.py
"""
import os, sys, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp
import studio_human as sh

OUT = os.path.join(ROOT, "reports", "geo_chan_doan")
os.makedirs(OUT, exist_ok=True)
CH = "UCDSfOc6Zy36qgt66I-SQyYg"

CLICK_BY_TEXT = """(arg) => {
    const [needle, mode] = arg;
    const hits = [];
    const walk = (root) => {
        root.querySelectorAll('*').forEach(e => {
            const t = (e.textContent||'').trim();
            if (!t || t.length > 120) { if (e.shadowRoot) walk(e.shadowRoot); return; }
            const own = e.children.length === 0 ? t : '';
            const ok = mode === 'prefix' ? t.startsWith(needle) : (own && own.indexOf(needle) >= 0);
            if (ok) hits.push(e);
            if (e.shadowRoot) walk(e.shadowRoot);
        });
    };
    walk(document);
    const e = hits[hits.length-1];
    if (!e) return null;
    const r = e.getBoundingClientRect();
    e.scrollIntoView({block: 'center'});
    e.click();
    return {txt: (e.textContent||'').trim().slice(0,60), x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
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
        page.evaluate("""() => { const b = document.querySelector('button#avatar-btn') ||
            document.querySelector('#avatar-btn') ||
            [...document.querySelectorAll('button')].find(b => (b.getAttribute('aria-label')||'').match(/tài khoản|account/i));
            if (b) b.click(); }""")
        time.sleep(4)
        r1 = page.evaluate(CLICK_BY_TEXT, ["Ngôn ngữ hiển thị", "prefix"])
        log("click 'Ngôn ngữ hiển thị':", json.dumps(r1, ensure_ascii=False))
        if not r1:
            r1 = page.evaluate(CLICK_BY_TEXT, ["Ngôn ngữ", "prefix"])
            log("  thu lai 'Ngôn ngữ':", json.dumps(r1, ensure_ascii=False))
        time.sleep(3)
        page.screenshot(path=os.path.join(OUT, "menu_ngon_ngu.png"))
        # submenu: chon English
        picked = None
        for needle in ("English (US)", "English (United States)", "English"):
            r2 = page.evaluate(CLICK_BY_TEXT, [needle, "exact"])
            log(f"click '{needle}':", json.dumps(r2, ensure_ascii=False))
            if r2:
                picked = r2["txt"]
                break
        time.sleep(6)
        page.screenshot(path=os.path.join(OUT, "sau_chon_en.png"))
        log("da chon:", picked)
        # kiem tra lai Studio
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        try:
            has_en = bool(page.evaluate(sh.FIND, "Content"))
        except Exception:
            has_en = False
        log("studio title:", (page.title() or "")[:70], "| menu 'Content' =", has_en)
        page.screenshot(path=os.path.join(OUT, "studio_en.png"))
        try:
            page.close()
        except Exception:
            pass
        if launched:
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:
                pass
