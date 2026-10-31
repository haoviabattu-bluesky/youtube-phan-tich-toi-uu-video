# -*- coding: utf-8 -*-
"""Kiem tra: tab Reach co bi loi 'Oops' khong, va text dung la gi."""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc

VID = "pTmVyc6Z2W4"
CH = "UCIimxP275YufOXXIlu9y9Lg"
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-overview/period-default",
                  wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)
        parts = page.evaluate(sc.DEEP)
        print("overview: so text =", len(parts), "| co 'Oops':", any("Oops" in t for t in parts))

        # bam Reach
        ok = page.evaluate(sc.CLICK_TEXT, "Reach")
        print("bam 'Reach' ->", ok)
        for i in range(6):
            time.sleep(8)
            parts = page.evaluate(sc.DEEP)
            j = " | ".join(parts)
            has_imp = any(t.strip() == "Thumbnail impressions" for t in parts)
            print(f"  +{(i+1)*8}s: n={len(parts)} co_impressions={has_imp} Oops={'Oops' in j}")
            if has_imp:
                print("  TIM THAY. Cac text quanh 'Thumbnail impressions':")
                k = [n for n, t in enumerate(parts) if t.strip() == "Thumbnail impressions"][0]
                for t in parts[k:k + 8]:
                    print("     ", repr(t[:80]))
                break
        else:
            print("  KHONG thay. 40 text cuoi:")
            for t in parts[-40:]:
                print("     ", repr(t[:80]))
        page.close()
