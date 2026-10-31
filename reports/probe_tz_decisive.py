# -*- coding: utf-8 -*-
"""Probe quyet dinh: bang theo ngay cua Studio ghi theo MUI GIO NAO?
ep09 cGZVfCjdRlE co bang: 10-13:30 | 10-14:1561 | 10-15:3090 | 10-16:851
Thu cua so JST 10-14: neu ra 30 -> nhan ngay cua bang lech 1 ngay so voi JST."""
import sys, os, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc

VID = "cGZVfCjdRlE"
TARGETS = {"JST 10-14 (bang:30?)": 30, "JST 10-15 (bang:1561?)": 1561, "JST 10-16 (bang:3090?)": 3090}

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    for name, expect in TARGETS.items():
        day = int(name.split("-")[1].split()[0])
        tz = datetime.timezone(datetime.timedelta(hours=9))
        a = datetime.datetime(2026, 10, day, tzinfo=tz)
        s = int(a.timestamp() * 1000)
        e = int((a + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).timestamp() * 1000)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-reach_viewers/period-{s},{e}",
                  wait_until="domcontentloaded", timeout=90000)
        parts = sc.wait_text(page, ["Thumbnail impressions"])
        imp = sc.after(parts, "Thumbnail impressions", lambda t: None if "%" in t else sc.num(t), span=3)
        print(f"{name}: imp={imp} (ky vong {expect})")
        page.close()
