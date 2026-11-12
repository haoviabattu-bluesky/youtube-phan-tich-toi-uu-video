# -*- coding: utf-8 -*-
r"""CHAN DOAN lane GEO: mo profile GPM normaneileenpm218, xem studio.youtube.com bi day sang dau.

  py -3.13 scratch_analysis/chan_doan_geo.py

In ra: danh sach tab dang mo, URL tung buoc, tai khoan/kenh dang active, chup man hinh.
"""
import os, sys, json, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.pop("PYTHONPATH", None)
from playwright.sync_api import sync_playwright
import daily_profiles as dp

MAIL = "normaneileenpm218@gmail.com"
OUT = os.path.join(ROOT, "reports", "geo_chan_doan")
os.makedirs(OUT, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


g = {"engine": "gpm", "mail": MAIL}
with dp.open_group(g, log) as (ws, _):
    log("ws =", ws[:70])
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(ws)
        ctx = br.contexts[0]
        log("so tab dang mo:", len(ctx.pages))
        for i, p in enumerate(ctx.pages):
            log(f"  tab {i}: {p.url[:110]}")
        page = ctx.new_page()
        for target in ("https://studio.youtube.com/", "https://studio.youtube.com/"):
            try:
                resp = page.goto(target, wait_until="domcontentloaded", timeout=45000)
                log("goto ->", page.url[:120], "| status", resp.status if resp else "?")
            except Exception as e:
                log("goto loi:", str(e)[:160], "| url hien tai:", page.url[:120])
            time.sleep(4)
            log("  sau 4s url =", page.url[:130])
        page.screenshot(path=os.path.join(OUT, "studio.png"))
        # kenh dang active
        try:
            page.goto("https://www.youtube.com/account_advanced", wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)
            txt = page.inner_text("body")[:600].replace("\n", " | ")
            log("account_advanced url =", page.url[:100])
            log("account_advanced text:", txt[:400])
        except Exception as e:
            log("account_advanced loi:", str(e)[:150])
        page.screenshot(path=os.path.join(OUT, "account.png"))
        log("anh:", OUT)
