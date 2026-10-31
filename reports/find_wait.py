# -*- coding: utf-8 -*-
"""Tim cho CHO: read_video_full va collect_daily deu co vong wait_text(loops,gap).
Do xem moi vong cho bao lau va khi nao moi thay text can tim."""
import sys, os, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc, studio_daily as sd
import spike_sources

VID = "pTmVyc6Z2W4"
CH = "UCIimxP275YufOXXIlu9y9Lg"
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}
meta = {it["id"]: spike_sources.pub_dt(it["snippet"]["publishedAt"])
        for it in spike_sources._get([VID], "snippet")}

with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)

        # --- buoc 1: overview (read_video_full phan dau) ---
        t = time.time()
        page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-overview/period-default",
                  wait_until="domcontentloaded", timeout=90000)
        t_goto = time.time() - t
        t = time.time()
        n = 0
        while time.time() - t < 90:
            n += 1
            parts = page.evaluate(sc.DEEP)
            j = " | ".join(parts)
            if "Average view duration" in j and "Views" in j:
                break
            time.sleep(1)
        print(f"overview: goto={t_goto:.1f}s | thay text sau {time.time()-t:.1f}s ({n} lan poll)")

        # --- buoc 2: bam Reach ---
        t = time.time()
        page.evaluate(sc.CLICK_TEXT, "Reach")
        n = 0
        while time.time() - t < 90:
            n += 1
            parts = page.evaluate(sc.DEEP)
            if any(x.strip() == "Thumbnail impressions" for x in parts):
                break
            time.sleep(1)
        print(f"Reach  : thay text sau {time.time()-t:.1f}s ({n} lan poll)")

        # --- buoc 3: 24h truot ---
        now = datetime.datetime.now()
        s = int((now - datetime.timedelta(hours=24)).timestamp() * 1000)
        e = int(now.timestamp() * 1000)
        t = time.time()
        page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-reach_viewers/period-{s},{e}",
                  wait_until="domcontentloaded", timeout=90000)
        n = 0
        while time.time() - t < 90:
            n += 1
            parts = page.evaluate(sc.DEEP)
            if any(x.strip() == "Thumbnail impressions" for x in parts):
                break
            time.sleep(1)
        print(f"Reach24h: sau {time.time()-t:.1f}s ({n} lan poll)")

        # --- buoc 4: bang theo ngay (collect_daily) ---
        t = time.time()
        page.goto(sd.TABLE_URL.format(vid=VID), wait_until="domcontentloaded", timeout=90000)
        n = 0
        rows = {}
        while time.time() - t < 90:
            n += 1
            parts = page.evaluate(sc.DEEP)
            rows = sd.parse_table(parts)
            if rows:
                break
            time.sleep(1)
        print(f"bang ngay: sau {time.time()-t:.1f}s ({n} lan poll) | rows={len(rows)}")
        page.close()
