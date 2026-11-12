# -*- coding: utf-8 -*-
"""Lay CTR + impressions cua dung 24h TRUOT (now-24h..now) bang URL period-<ms>,<ms>."""
import sys, os, json, time, datetime
sys.path.insert(0, 'tools')

from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_human as sh

WS = sys.argv[1]
VIDS = sys.argv[2].split(',')

now = datetime.datetime.now()
end_ms = int(now.timestamp() * 1000)
start_ms = int((now - datetime.timedelta(hours=24)).timestamp() * 1000)

res = {}
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(90000)
    for v in VIDS:
        url = (f"https://studio.youtube.com/video/{v}/analytics/tab-reach_viewers/"
               f"period-{start_ms},{end_ms}")
        print(f"[{v}] {url[-40:]}", flush=True)
        try:
            page.goto(url, wait_until="domcontentloaded")
            parts = sh.wait_text(page, ["Thumbnail impressions"], tries=25)
            j = " | ".join(parts)
            if "Oops" in j:
                print("   OOPS", flush=True); continue
            imp = sc.after(parts, "Thumbnail impressions", sc.num)
            ctr = sc.pct_after(parts, "Thumbnail click-through rate")
            vw = sc.after(parts, "Views", sc.num)
            print(f"   impr24={imp} ctr24={ctr} views24={vw}", flush=True)
            res[v] = {"impr24": imp, "ctr24": ctr, "views24": vw}
        except Exception as e:
            print("   LOI:", str(e)[:200], flush=True)
        time.sleep(3)

open('reports/ctr24_3vid.json', 'w', encoding='utf-8').write(
    json.dumps(res, ensure_ascii=False, indent=1))
print("DA GHI", len(res))
