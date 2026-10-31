# -*- coding: utf-8 -*-
"""Probe: Studio da xu ly ngay 10-17 chua? So sanh cua so 10-17 (JST) voi cua so 10-16 (JST)."""
import sys, os, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import sheet_metrics_sync as sms
from studio_collect import wait_text, after, pct_after, num

VID = sys.argv[1] if len(sys.argv) > 1 else "nNlqnf28Kak"
JST = datetime.timezone(datetime.timedelta(hours=9))


def window(day):
    a = datetime.datetime(day.year, day.month, day.day, 0, 0, tzinfo=JST)
    b = a + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
    return int(a.timestamp() * 1000), int(b.timestamp() * 1000)


with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)
    for d in (datetime.date(2026, 10, 16), datetime.date(2026, 10, 17)):
        s, e = window(d)
        page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-reach_viewers/period-{s},{e}",
                  wait_until="domcontentloaded", timeout=90000)
        parts = wait_text(page, ["Thumbnail impressions"])
        imp = after(parts, "Thumbnail impressions", lambda t: None if "%" in t else num(t), span=3)
        ctr = pct_after(parts, "Thumbnail click-through rate")
        views = after(parts, "Views", num)
        label = [t for t in parts if "Custom" in t or "—" in t][:3]
        print(f"{d} JST: imp={imp} ctr={ctr} views={views} label={label}")
    page.close()
