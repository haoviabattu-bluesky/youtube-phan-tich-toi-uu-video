# -*- coding: utf-8 -*-
"""Do thoi gian THAT cua dung duong di task 05:00: read_video_full lien tiep 5 video, 1 session."""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import daily_profiles
from sheet_metrics_sync import read_video_full

CH = "UCIimxP275YufOXXIlu9y9Lg"
VIDS = ["pTmVyc6Z2W4", "vy7ucq5Zy64", "ctRisa4AEH4", "qfg_YVoo9RA", "6woJHXK_x7M"]
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["F"]}

t0 = time.time()
times = []
with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    t_open = time.time() - t0
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page()
        page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(f"https://studio.youtube.com/channel/{CH}", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        print(f"mo profile + chuyen kenh: {t_open:.0f}s")
        for vid in VIDS:
            t = time.time()
            ok = False
            for attempt in range(2):
                r = read_video_full(page, vid)
                if r.get("ok"):
                    ok = True
                    break
            dt = time.time() - t
            times.append((vid, dt, ok))
            print(f"  {vid}: {dt:6.1f}s  ok={ok}  (lan thu {attempt+1})", flush=True)
        page.close()

print(f"\nTONG: {time.time()-t0:.0f}s cho {len(VIDS)} video")
ok_t = [d for _, d, o in times if o]
if ok_t:
    print(f"trung binh khi THANH CONG: {sum(ok_t)/len(ok_t):.1f}s/video")
print(f"cao nhat: {max(d for _, d, _ in times):.1f}s | thap nhat: {min(d for _, d, _ in times):.1f}s")
