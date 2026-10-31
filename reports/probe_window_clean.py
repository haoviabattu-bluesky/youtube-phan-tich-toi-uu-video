# -*- coding: utf-8 -*-
"""Probe chac chan: moi cua so = 1 TAB MOI (tranh doc so cu), kiem ca URL + nhan 'Custom' + co 'Oops'."""
import sys, os, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc

VID = sys.argv[1] if len(sys.argv) > 1 else "nNlqnf28Kak"
WINDOWS = {
    "JST 10-16": (datetime.timezone(datetime.timedelta(hours=9)), datetime.date(2026, 10, 16)),
    "JST 10-17": (datetime.timezone(datetime.timedelta(hours=9)), datetime.date(2026, 10, 17)),
    "PT  10-16": (datetime.timezone(datetime.timedelta(hours=-7)), datetime.date(2026, 10, 16)),
    "PT  10-17": (datetime.timezone(datetime.timedelta(hours=-7)), datetime.date(2026, 10, 17)),
}

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    for name, (tz, d) in WINDOWS.items():
        a = datetime.datetime(d.year, d.month, d.day, tzinfo=tz)
        s = int(a.timestamp() * 1000)
        e = int((a + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).timestamp() * 1000)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        url = f"https://studio.youtube.com/video/{VID}/analytics/tab-reach_viewers/period-{s},{e}"
        page.goto(url, wait_until="load", timeout=90000)
        time.sleep(14)
        parts = page.evaluate(sc.DEEP)
        j = " | ".join(parts)
        imp = sc.after(parts, "Thumbnail impressions", lambda t: None if "%" in t else sc.num(t), span=3)
        ctr = sc.pct_after(parts, "Thumbnail click-through rate")
        vw = sc.after(parts, "Views", sc.num)
        print(f"{name}: imp={imp} ctr={ctr} views={vw} | OOPS={'Oops' in j} | URL_OK={str(s) in page.url} | N={len(parts)}")
        page.close()
