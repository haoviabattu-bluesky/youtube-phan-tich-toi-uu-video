# -*- coding: utf-8 -*-
"""Do thoi gian THAT cua CA 2 buoc ma task 05:00 chay cho moi video:
   read_video_full (N/O/P/Q) + studio_daily.collect_daily (bang theo ngay)."""
import sys, os, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc, studio_daily as sd
from sheet_metrics_sync import read_video_full
import spike_sources

CH = "UCIimxP275YufOXXIlu9y9Lg"
VIDS = ["pTmVyc6Z2W4", "vy7ucq5Zy64", "ctRisa4AEH4", "qfg_YVoo9RA", "6woJHXK_x7M"]
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

meta = {it["id"]: spike_sources.pub_dt(it["snippet"]["publishedAt"])
        for it in spike_sources._get(VIDS, "snippet")}

t0 = time.time()
rows = []
with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    t_open = time.time() - t0
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        print(f"mo profile + chuyen kenh: {t_open:.0f}s\n")
        print(f"{'video':14}{'read_video':>11}{'daily':>8}{'TONG':>8}  ok")
        for vid in VIDS:
            h = (datetime.datetime.now(datetime.timezone.utc) - meta[vid]).total_seconds() / 3600
            t = time.time()
            r = read_video_full(page, vid)
            t1 = time.time() - t
            t = time.time()
            d = sd.collect_daily(page, vid, sc.DEEP, float(r.get("views") or 0) or 100.0, h, r.get("views"))
            t2 = time.time() - t
            rows.append((t1, t2, r.get("ok"), d.get("current_distribution_status")))
            print(f"{vid:14}{t1:>10.1f}s{t2:>7.1f}s{t1+t2:>7.1f}s  {r.get('ok')} {d.get('current_distribution_status')}", flush=True)
        page.close()

tot = time.time() - t0
n = len(VIDS)
avg = sum(a + b for a, b, _, _ in rows) / n
print(f"\nmo profile: {t_open:.0f}s")
print(f"trung binh/video (ca 2 buoc): {avg:.1f}s")
print(f"TONG {n} video: {tot:.0f}s")
print(f"\n=> 96 video: {11*48 + 96*avg:.0f}s = {(11*48 + 96*avg)/60:.0f} phut")
