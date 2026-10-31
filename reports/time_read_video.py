# -*- coding: utf-8 -*-
"""Do thoi gian read_video_full tren 1 video (ham ma task 05:00 dung)."""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import daily_profiles
from sheet_metrics_sync import read_video_full

VID = sys.argv[1] if len(sys.argv) > 1 else "pTmVyc6Z2W4"
CH = "UCIimxP275YufOXXIlu9y9Lg"
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

t0 = time.time()
with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    t_open = time.time() - t0
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        print("chuyen kenh:", f"/channel/{CH}" in page.url, "| mo profile:", f"{t_open:.0f}s")

        for n in range(2):
            t = time.time()
            r = read_video_full(page, VID)
            print(f"  lan {n+1}: {time.time()-t:.1f}s -> {r}")
        page.close()
print(f"TONG: {time.time()-t0:.0f}s")
