# -*- coding: utf-8 -*-
r"""Test DUONG NGUOI THAT: click Content -> video -> Analytics -> Reach -> Custom ngay.

  py -3.13 reports/test_human_click.py --port 9222 --video MLHsJKhmw84
"""
import sys, os, json, time, argparse, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import human_pace as hp
import studio_human as sh
import sheet_metrics_sync as sc

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=9222)
ap.add_argument("--video", required=True)
ap.add_argument("--scale", type=float, default=1.0)
a = ap.parse_args()
os.environ["HUMAN_PACE_SCALE"] = str(a.scale)
import importlib; importlib.reload(hp)

ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5))["webSocketDebuggerUrl"]

def log(*x): print(time.strftime("%H:%M:%S"), *x, flush=True)

t0 = time.time()
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)

    ok = sh.open_studio(page, log);            log("open_studio:", ok, f"{time.time()-t0:.0f}s")
    ok = sh.open_content(page, log);           log("open_content:", ok, f"{time.time()-t0:.0f}s")
    ok = sh.click_video(page, a.video, log);   log("click_video:", ok, f"{time.time()-t0:.0f}s")
    ok = sh.click_tab(page, "Analytics", log); log("Analytics:", ok, f"{time.time()-t0:.0f}s")
    sh.wait_url(page, "/analytics/", 15)
    ok = sh.click_tab(page, "Reach", log);     log("Reach:", ok, f"{time.time()-t0:.0f}s")
    parts = sh.wait_text(page, ["Thumbnail impressions"], 25)
    has = any(t.strip()=="Thumbnail impressions" for t in parts)
    log("co so Reach:", has, f"{time.time()-t0:.0f}s")
    if has:
        log("  Views:", sc.after(parts,"Views",sc.num), "| CTR:", sc.pct_after(parts,"Thumbnail click-through rate"),
            "| imp:", sc.after(parts,"Thumbnail impressions",lambda t: None if "%" in t else sc.num(t), span=3))
    import datetime
    y = datetime.date.today()-datetime.timedelta(days=1)
    ok = sh.set_day_range(page, y, y, log);    log("set_day_range:", ok, f"{time.time()-t0:.0f}s")
    parts2 = sh.wait_text(page, ["Thumbnail impressions"], 20)
    if any(t.strip()=="Thumbnail impressions" for t in parts2):
        log("  NGAY", y, "-> CTR:", sc.pct_after(parts2,"Thumbnail click-through rate"),
            "| imp:", sc.after(parts2,"Thumbnail impressions",lambda t: None if "%" in t else sc.num(t), span=3))
    page.close()
print(f"\nTONG = {time.time()-t0:.0f}s")
