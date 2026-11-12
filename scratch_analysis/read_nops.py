# -*- coding: utf-8 -*-
"""Doc N/O/P/Q bang DUONG NGUOI THAT (sheet_metrics_sync.read_video_full).
Khong goto URL video (goto -> Studio tra Oops hang loat)."""
import sys, os, json, time
sys.path.insert(0, 'tools')

from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_human as sh
import sheet_metrics_sync as sms

WS = sys.argv[1]
CID = sys.argv[2]
VIDS = sys.argv[3].split(',')
TAG = sys.argv[4] if len(sys.argv) > 4 else '3vid'

res = {}
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(90000)
    page.goto(f"https://studio.youtube.com/channel/{CID}/videos/upload",
              wait_until="domcontentloaded")
    for _ in range(25):
        time.sleep(2)
        if page.evaluate("() => document.querySelectorAll('ytcp-video-row').length"):
            break
    print("so dong:", page.evaluate("() => document.querySelectorAll('ytcp-video-row').length"), flush=True)

    for v in VIDS:
        print(f"[{v}] doc N/O/P/Q ...", flush=True)
        try:
            r = sms.read_video_full(page, v, log=lambda s: print("   ", s, flush=True))
            print("   =>", json.dumps({k: r.get(k) for k in
                  ['days', 'views', 'ctr_total', 'ctr_24h', 'imp_24h', 'ok']}, ensure_ascii=False), flush=True)
            res[v] = r
        except Exception as e:
            print("   LOI:", str(e)[:250], flush=True)
        time.sleep(3)

open(f'reports/sheet_read_{TAG}.json', 'w', encoding='utf-8').write(
    json.dumps(res, ensure_ascii=False, indent=1, default=str))
print("DA GHI", len(res))
