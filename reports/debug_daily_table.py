# -*- coding: utf-8 -*-
"""Kiem tra rieng BANG THEO NGAY (phan de hong nhat).
Thu: (a) URL hien tai, (b) cho lau hon, (c) mo tab moi, (d) doc lai sau khi reload."""
import sys, os, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc, studio_daily as sd

CH = "UCIimxP275YufOXXIlu9y9Lg"
VIDS = ["pTmVyc6Z2W4", "vy7ucq5Zy64", "ctRisa4AEH4"]
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)

        for vid in VIDS:
            t = time.time()
            page.goto(sd.TABLE_URL.format(vid=vid), wait_until="domcontentloaded", timeout=90000)
            rows, parts, n = {}, [], 0
            while time.time() - t < 60:
                time.sleep(3)
                n += 1
                parts = page.evaluate(sc.DEEP)
                rows = sd.parse_table(parts)
                if rows:
                    break
            j = " | ".join(parts)
            print(f"{vid}: {time.time()-t:.0f}s ({n} poll) rows={len(rows)} "
                  f"Oops={'Oops' in j} Total={'Total' in j} n_text={len(parts)}")
            if not rows:
                print("   end_day:", sd.report_end_day(parts))
                print("   text cuoi:", [x[:45] for x in parts[-14:]])
                # thu reload
                t2 = time.time()
                page.reload(wait_until="domcontentloaded", timeout=90000)
                for _ in range(15):
                    time.sleep(3)
                    parts = page.evaluate(sc.DEEP)
                    rows = sd.parse_table(parts)
                    if rows:
                        break
                print(f"   sau RELOAD: {time.time()-t2:.0f}s rows={len(rows)}")
        page.close()