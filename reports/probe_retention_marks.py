# -*- coding: utf-8 -*-
"""Probe: cac moc giu chan co trong DOM khong (5/10/20/30/60s) — dump vung 'still watching'."""
import sys, os, time, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc

VID = sys.argv[1] if len(sys.argv) > 1 else "lbJMkB5Vus0"
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)
    page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-overview/period-default",
              wait_until="domcontentloaded", timeout=90000)
    parts = sc.wait_text(page, ["still watching"])
    idx = [i for i, t in enumerate(parts) if "still watching" in t]
    print("IDX:", idx)
    for i in idx:
        print("---- around", i)
        for t in parts[max(0, i - 6):i + 8]:
            print("   ", repr(t[:120]))
    print("ALL MARKS:", re.findall(r"(\d+)% of viewers are still watching at around the ([\d:]+) mark", " | ".join(parts)))
    # Thu hover len bieu do retention de xem co moc khac
    try:
        el = page.query_selector("ytpa-retention-panel, #retention-panel, ytcp-video-analytics-retention-panel")
        print("panel:", bool(el))
    except Exception as e:
        print("panel err", e)
    page.close()
