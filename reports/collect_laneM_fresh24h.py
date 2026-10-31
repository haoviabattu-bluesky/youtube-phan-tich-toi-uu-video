# -*- coding: utf-8 -*-
"""Doc lai N/O/P/Q moi (rolling 24h now-24h..now) cho 12 video lane M, ghi JSON.
Dung read_video_full cua sheet_metrics_sync (period-<start_ms>,<end_ms>) -> KHONG ghi sheet."""
import sys, os, json, time, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
from sheet_metrics_sync import read_video_full

VIDS = ["0gshT0RitS0", "rsdKmuD-y-4", "nNlqnf28Kak", "cGZVfCjdRlE", "s8rmYRsePdk", "fRp-ynO-DJs",
        "lbJMkB5Vus0", "9Bn6J3RtCJ4", "axCH-36CNxI", "VFdj45ytUaI", "6rM_7jwLs2k", "7hnpdufAVHg"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laneM_fresh_24h.json")

res = {}
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)
    for vid in VIDS:
        r = None
        for _ in range(2):
            try:
                r = read_video_full(page, vid)
                if r and r.get("ok"):
                    break
            except Exception as e:
                print(vid, "LOI", str(e)[:100], flush=True)
        res[vid] = r or {"ok": False}
        print(vid, json.dumps(res[vid], ensure_ascii=False), flush=True)
        time.sleep(2)
    page.close()

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("GHI", OUT)
