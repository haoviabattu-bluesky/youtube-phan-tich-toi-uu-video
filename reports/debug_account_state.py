# -*- coding: utf-8 -*-
"""Kiem tra trang thai tai khoan trong profile GPM nay: dang nhap? kenh nao? co bi gioi han?"""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc

g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)

        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)
        print("URL:", page.url[:110])
        parts = page.evaluate(sc.DEEP)
        print("so text:", len(parts), "| Oops:", any("Oops" in t for t in parts))
        print("dau trang:")
        for t in parts[:25]:
            print("   ", repr(t[:75]))

        # thu 1 video khac, tab overview
        page.goto("https://studio.youtube.com/video/vy7ucq5Zy64/analytics/tab-overview/period-default",
                  wait_until="domcontentloaded", timeout=90000)
        time.sleep(12)
        parts = page.evaluate(sc.DEEP)
        j = " | ".join(parts)
        print("\nvideo khac: n=", len(parts), "| Oops:", "Oops" in j,
              "| co 'Views':", any(t.strip() == "Views" for t in parts))
        page.close()
