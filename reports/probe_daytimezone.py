# -*- coding: utf-8 -*-
"""Probe: xac dinh mui gio cua bang theo ngay Studio. So window theo JST / PT / UTC voi tung dong trong bang."""
import sys, os, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_daily as sd
from studio_collect import wait_text, after, pct_after, num

VID = sys.argv[1] if len(sys.argv) > 1 else "nNlqnf28Kak"
TZS = {"JST": 9, "PT": -7, "UTC": 0}


def window(day, off):
    tz = datetime.timezone(datetime.timedelta(hours=off))
    a = datetime.datetime(day.year, day.month, day.day, tzinfo=tz)
    return int(a.timestamp() * 1000), int((a + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).timestamp() * 1000)


with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)

    # bang theo ngay
    page.goto(sd.TABLE_URL.format(vid=VID), wait_until="domcontentloaded", timeout=90000)
    rows = {}
    for _ in range(15):
        time.sleep(3)
        parts = page.evaluate(__import__("studio_collect").DEEP)
        rows = sd.parse_table(parts)
        if rows:
            break
    print("BANG THEO NGAY (nhan -> imp/ctr/views):")
    for d, v in sorted(rows.items()):
        print("   ", d, v)

    for name, off in TZS.items():
        for d in sorted(rows)[-2:]:
            s, e = window(d, off)
            page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-reach_viewers/period-{s},{e}",
                      wait_until="domcontentloaded", timeout=90000)
            pp = wait_text(page, ["Thumbnail impressions"])
            imp = after(pp, "Thumbnail impressions", lambda t: None if "%" in t else num(t), span=3)
            ctr = pct_after(pp, "Thumbnail click-through rate")
            vw = after(pp, "Views", num)
            print(f"   window {name} {d} -> imp={imp} ctr={ctr} views={vw}")
    page.close()
