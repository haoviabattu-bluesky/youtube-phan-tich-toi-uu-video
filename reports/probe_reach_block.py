# -*- coding: utf-8 -*-
"""Probe: dump khoi Reach cua 1 video de xac dinh gia tri nao la 'Thumbnail impressions' that."""
import sys, os, time, json
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
    sc.wait_text(page, ["Views"])
    page.evaluate(sc.CLICK_TEXT, "Reach")
    parts = sc.wait_text(page, ["Thumbnail impressions"])
    json.dump(parts, open("reports/probe_reach_parts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    i = parts.index("Thumbnail impressions")
    print("=== from idx", i, "===")
    for t in parts[i:i + 46]:
        print("   ", repr(t[:100]))
    page.close()
