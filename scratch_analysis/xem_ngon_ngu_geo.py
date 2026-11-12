# -*- coding: utf-8 -*-
r"""Xem ngon ngu tai khoan YouTube cua profile GEO + cac lua chon dropdown.

  env -u PYTHONPATH py -3.13 scratch_analysis/xem_ngon_ngu_geo.py
"""
import os, sys, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp

OUT = os.path.join(ROOT, "reports", "geo_chan_doan")
os.makedirs(OUT, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


with dp.open_group({"engine": "gpm", "mail": "normaneileenpm218@gmail.com"}, log) as (ws, launched):
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front()
        page.goto("https://www.youtube.com/account", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        log("url:", page.url[:90])
        txt = page.inner_text("body")[:1200].replace("\n", " | ")
        log("text:", txt[:900])
        info = page.evaluate("""() => {
            const out = {selects: [], labels: []};
            document.querySelectorAll('select').forEach((s,i)=>{
                out.selects.push({i, name: s.getAttribute('aria-label')||s.name||'', val: s.value,
                                  opts: [...s.options].slice(0,8).map(o=>o.value+'|'+o.text)});
            });
            document.querySelectorAll('ytcp-select, tp-yt-paper-dropdown-menu, select').forEach((e,i)=>{
                out.labels.push(i+':'+(e.tagName)+':'+(e.textContent||'').trim().slice(0,60));
            });
            return out;
        }""")
        log("selects:", json.dumps(info["selects"], ensure_ascii=False)[:800])
        page.screenshot(path=os.path.join(OUT, "account_page.png"), full_page=True)
        # thu Studio settings
        page.goto("https://studio.youtube.com/channel/UCDSfOc6Zy36qgt66I-SQyYg/editing/settings",
                  wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        log("studio settings url:", page.url[:100])
        log("studio settings text:", page.inner_text("body")[:600].replace("\n", " | "))
        page.screenshot(path=os.path.join(OUT, "studio_settings.png"), full_page=True)
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
