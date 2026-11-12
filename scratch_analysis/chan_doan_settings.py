# -*- coding: utf-8 -*-
r"""Mo hop thoai Cai dat cua Studio (kenh GEO) va liet ke cac o chon ngon ngu.

  env -u PYTHONPATH py -3.13 scratch_analysis/chan_doan_settings.py
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


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


with dp.open_group({"engine": "gpm", "mail": "normaneileenpm218@gmail.com"}, log) as (ws, launched):
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front()
        page.set_default_timeout(60000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=60000)
        time.sleep(9)
        log("url:", page.url[:90])
        # bam 'Cai dat' o menu trai (tieng Viet: "Cài đặt", tieng Anh: "Settings")
        hit = None
        for lab in ("Cài đặt", "Settings"):
            try:
                if page.evaluate(sh.FIND, lab):
                    hit = lab
                    break
            except Exception:
                pass
        log("nhan menu tim thay:", hit)
        if hit:
            el = page.evaluate("""(lab) => {
                const walk = (root, out) => {
                    root.querySelectorAll('*').forEach(e => {
                        if (e.children.length === 0 && (e.textContent||'').trim() === lab) out.push(e);
                        if (e.shadowRoot) walk(e.shadowRoot, out);
                    });
                };
                const out = []; walk(document, out);
                const e = out[out.length-1];
                if (!e) return null;
                const r = e.getBoundingClientRect();
                e.click();
                return {x: r.x + r.width/2, y: r.y + r.height/2, txt: e.textContent.trim()};
            }""", hit)
            log("click:", json.dumps(el, ensure_ascii=False))
            time.sleep(8)
        txt = page.inner_text("body")[:1500].replace("\n", " | ")
        log("sau khi mo settings:", txt[:900])
        # liet ke cac o chon (ytcp-select / dropdown) trong dialog
        dd = page.evaluate("""() => {
            const out = [];
            const walk = (root) => {
                root.querySelectorAll('ytcp-select, tp-yt-paper-dropdown-menu, select, ytcp-dropdown-trigger').forEach(e => {
                    const r = e.getBoundingClientRect();
                    if (r.width > 0) out.push({tag: e.tagName, txt: (e.textContent||'').trim().slice(0,60),
                                               x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
                });
                root.querySelectorAll('*').forEach(e => { if (e.shadowRoot) walk(e.shadowRoot); });
            };
            walk(document);
            return out;
        }""")
        log("dropdown:", json.dumps(dd, ensure_ascii=False)[:1200])
        page.screenshot(path=os.path.join(OUT, "settings_dialog.png"), full_page=False)
        log("anh:", OUT)
        try:
            page.close()
        except Exception:
            pass
        if launched:
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:
                pass
