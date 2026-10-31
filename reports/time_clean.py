# -*- coding: utf-8 -*-
"""Do toc do THAT khi may RANH: dung y duong di task 05:00, 8 video 1 session.
Khong chay song song gi khac."""
import sys, os, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))
from playwright.sync_api import sync_playwright
import daily_profiles, studio_collect as sc, studio_daily as sd
from sheet_metrics_sync import read_video_full
import spike_sources

CH = "UCIimxP275YufOXXIlu9y9Lg"
VIDS = ["pTmVyc6Z2W4", "vy7ucq5Zy64", "ctRisa4AEH4", "qfg_YVoo9RA", "6woJHXK_x7M",
        "QGzofxom8Gk", "sAeKtLlVEaI", "axi49gJn9bs"]
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
        print(f"{'#':>2} {'video':14}{'read':>7}{'daily':>7}{'TONG':>8}  ok", flush=True)
        for n, vid in enumerate(VIDS, 1):
            h = (datetime.datetime.now(datetime.timezone.utc) - meta[vid]).total_seconds() / 3600
            t = time.time()
            r = read_video_full(page, vid)
            t1 = time.time() - t
            t = time.time()
            d = sd.collect_daily(page, vid, sc.DEEP, float(r.get("views") or 0) or 100.0, h, r.get("views"))
            t2 = time.time() - t
            rows.append((t1, t2, bool(r.get("ok"))))
            print(f"{n:>2} {vid:14}{t1:>6.1f}s{t2:>6.1f}s{t1+t2:>7.1f}s  {r.get('ok')}", flush=True)
        page.close()

tot = time.time() - t0
n = len(VIDS)
ok = [a + b for a, b, o in rows if o]
avg = sum(a + b for a, b, _ in rows) / n
print(f"\nmo profile: {t_open:.0f}s | {n} video: {tot:.0f}s")
print(f"trung binh/video: {avg:.1f}s | thanh cong {len(ok)}/{n}")
if ok:
    print(f"trung binh khi THANH CONG: {sum(ok)/len(ok):.1f}s")
est = 11 * t_open + 96 * avg
print(f"\n=> 96 video, 11 nhom: {est:.0f}s = {est/60:.0f} phut = {est/3600:.1f} gio")
