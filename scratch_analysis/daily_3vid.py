# -*- coding: utf-8 -*-
"""Lay bang so theo NGAY cho vai video (de tinh CTR 24h gan nhat)."""
import sys, os, json, time
sys.path.insert(0, 'tools')

from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_daily as sd

WS = sys.argv[1]
CID = sys.argv[2]
VIDS = sys.argv[3].split(',')

res = {}
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(90000)
    page.goto(f"https://studio.youtube.com/channel/{CID}/videos/upload", wait_until="domcontentloaded")
    for _ in range(20):
        time.sleep(2)
        if page.evaluate("() => document.querySelectorAll('ytcp-video-row').length"):
            break
    rows = json.load(open('reports/collect_3vid.json', encoding='utf-8')) if os.path.exists('reports/collect_3vid.json') else []
    byid = {r['video_id']: r for r in rows}
    for v in VIDS:
        print(f"[{v}] daily...", flush=True)
        r = byid.get(v, {})
        try:
            d = sd.collect_daily(page, v, sc.DEEP,
                                 r.get('impressions') or 0,
                                 r.get('hours_since_publish') or 0,
                                 r.get('views') or 0)
            res[v] = d
            print("   ", json.dumps({k: d.get(k) for k in
                  ['last_data_day','impressions_last_24h','ctr_last_24h','views_last_24h',
                   'impressions_previous_24h','ctr_previous_24h','impressions_last_48h','ctr_last_48h',
                   'peak_day_impressions','current_distribution_status','mark_needed']},
                  ensure_ascii=False), flush=True)
        except Exception as e:
            print("   LOI:", str(e)[:250], flush=True)
        time.sleep(3)

open('reports/daily_3vid.json', 'w', encoding='utf-8').write(
    json.dumps(res, ensure_ascii=False, indent=1, default=str))
print("DA GHI reports/daily_3vid.json", len(res))
