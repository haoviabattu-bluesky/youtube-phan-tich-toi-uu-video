# -*- coding: utf-8 -*-
"""Probe khoi 'YouTube search terms' tren tab Reach: xem co 'Not enough traffic data' khong."""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc

VIDS = sys.argv[1:] or ["6rM_7jwLs2k"]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)
    for vid in VIDS:
        page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-overview/period-default",
                  wait_until="domcontentloaded", timeout=90000)
        sc.wait_text(page, ["Views"])
        page.evaluate(sc.CLICK_TEXT, "Reach")
        parts = sc.wait_text(page, ["Thumbnail impressions"])
        try:
            i = parts.index("YouTube search terms")
            print(f"=== {vid} idx={i} ===")
            for t in parts[i:i + 14]:
                print("   ", repr(t[:90]))
        except ValueError:
            print(f"=== {vid}: KHONG co khoi 'YouTube search terms' ===")
            print("   traffic-source?", [t for t in parts if "Browse features" in t][:2])
    page.close()
