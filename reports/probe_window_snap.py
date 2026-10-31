# -*- coding: utf-8 -*-
"""Probe quyet dinh: cua so 6h / 12h / 24h co bi Studio SNAP ve ca ngay khong?
So cung 1 video (ep05 lbJMkB5Vus0)."""
import sys, os, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc

VID = sys.argv[1] if len(sys.argv) > 1 else "lbJMkB5Vus0"
NOW = datetime.datetime.now(datetime.timezone.utc)
CASES = {"6h": 6, "12h": 12, "24h": 24, "48h": 48, "72h": 72}

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    for name, hrs in CASES.items():
        s = int((NOW - datetime.timedelta(hours=hrs)).timestamp() * 1000)
        e = int(NOW.timestamp() * 1000)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-reach_viewers/period-{s},{e}",
                  wait_until="domcontentloaded", timeout=90000)
        parts = sc.wait_text(page, ["Thumbnail impressions"])
        imp = sc.after(parts, "Thumbnail impressions", lambda t: None if "%" in t else sc.num(t), span=3)
        ctr = sc.pct_after(parts, "Thumbnail click-through rate")
        vw = sc.after(parts, "Views", sc.num)
        lab = [t for t in parts if "Custom" in t or "Since" in t][:2]
        print(f"{name:>4}: imp={imp} ctr={ctr} views={vw} | labels={lab}")
        page.close()
