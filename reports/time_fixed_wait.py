# -*- coding: utf-8 -*-
"""Do lai 3 video voi thoi gian cho DAI (25s) thay vi 90s poll lien tuc.
Muc dich: xac dinh toc do THAT khi cho du trang tai."""
import sys, os, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc, studio_daily as sd
import spike_sources

CH = "UCIimxP275YufOXXIlu9y9Lg"
VIDS = ["pTmVyc6Z2W4", "vy7ucq5Zy64", "ctRisa4AEH4"]
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}
meta = {it["id"]: spike_sources.pub_dt(it["snippet"]["publishedAt"])
        for it in spike_sources._get(VIDS, "snippet")}

with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        print(f"{'video':14}{'overview':>10}{'reach':>8}{'24h':>8}{'daily':>8}{'TONG':>8}")
        for vid in VIDS:
            h = (datetime.datetime.now(datetime.timezone.utc) - meta[vid]).total_seconds() / 3600
            T = []
            # overview
            t = time.time()
            page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-overview/period-default",
                      wait_until="domcontentloaded", timeout=90000)
            time.sleep(22)
            parts = page.evaluate(sc.DEEP)
            T.append(time.time() - t)
            # reach (bam)
            t = time.time()
            page.evaluate(sc.CLICK_TEXT, "Reach")
            time.sleep(20)
            parts = page.evaluate(sc.DEEP)
            T.append(time.time() - t)
            # 24h truot
            t = time.time()
            now = datetime.datetime.now()
            s = int((now - datetime.timedelta(hours=24)).timestamp() * 1000)
            e = int(now.timestamp() * 1000)
            page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-reach_viewers/period-{s},{e}",
                      wait_until="domcontentloaded", timeout=90000)
            time.sleep(22)
            parts = page.evaluate(sc.DEEP)
            T.append(time.time() - t)
            # bang ngay
            t = time.time()
            page.goto(sd.TABLE_URL.format(vid=vid), wait_until="domcontentloaded", timeout=90000)
            time.sleep(22)
            parts = page.evaluate(sc.DEEP)
            rows = sd.parse_table(parts)
            T.append(time.time() - t)
            print(f"{vid:14}{T[0]:>9.0f}s{T[1]:>7.0f}s{T[2]:>7.0f}s{T[3]:>7.0f}s{sum(T):>7.0f}s  rows={len(rows)}", flush=True)
        page.close()
