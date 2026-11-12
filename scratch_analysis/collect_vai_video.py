# -*- coding: utf-8 -*-
"""Thu so Studio cho vai video cu the, di thang vao URL analytics (bo qua buoc list video)."""
import sys, os, json, time
sys.path.insert(0, 'tools')
os.environ.setdefault('PYTHONPATH', '')

from playwright.sync_api import sync_playwright
import studio_collect as sc

WS = sys.argv[1]
VIDS = sys.argv[2].split(',')

out = []
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(90000)
    for v in VIDS:
        print(f"[{v}] thu...", flush=True)
        try:
            row = sc.collect_video(page, v, log=lambda *x: print("   ", *x, flush=True))
            print("   impr={impressions} ctr={ctr} views={views} avd={avd_sec} apv={apv_pct} "
                  "browse={browse_pct} sugg={suggested_pct}".format(**row), flush=True)
            out.append(row)
        except Exception as e:
            print("   LOI:", str(e)[:300], flush=True)
        time.sleep(3)

print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
