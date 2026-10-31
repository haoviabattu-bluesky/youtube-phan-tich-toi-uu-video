# -*- coding: utf-8 -*-
"""Kiem tra: Studio Analytics co loi tam thoi khong? Thu lai sau vai phut, ca 2 kieu URL."""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc

VID = "pTmVyc6Z2W4"
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

URLS = [
    ("overview period-default", f"https://studio.youtube.com/video/{VID}/analytics/tab-overview/period-default"),
    ("overview (khong period)", f"https://studio.youtube.com/video/{VID}/analytics/tab-overview"),
    ("analytics goc",           f"https://studio.youtube.com/video/{VID}/analytics"),
    ("analytics kenh",          "https://studio.youtube.com/channel/UCIimxP275YufOXXIlu9y9Lg/analytics"),
]

with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        for name, url in URLS:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(14)
                parts = page.evaluate(sc.DEEP)
                j = " | ".join(parts)
                oops = "Oops" in j
                has = any(t.strip() in ("Views", "Thumbnail impressions", "Channel analytics") for t in parts)
                print(f"{name:28} n={len(parts):>4} Oops={oops!s:5} co_so_lieu={has}")
                if oops:
                    k = [n for n, t in enumerate(parts) if "Oops" in t][0]
                    print("      context:", [t[:40] for t in parts[max(0,k-3):k+3]])
            except Exception as e:
                print(f"{name:28} LOI {str(e)[:70]}")
        page.close()
