# -*- coding: utf-8 -*-
"""Tim traceback that cua loi "'float' object has no attribute 'strip'" trong studio_daily."""
import sys, os, time, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc, studio_daily as sd, daily_profiles

VID = sys.argv[1] if len(sys.argv) > 1 else "vy7ucq5Zy64"
g = {"engine": "gpm", "mail": "VirgiliTraino95@gmail.com", "tabs": ["x"]}
with daily_profiles.open_group(g, lambda *a: print(*a, flush=True)) as (ws, _):
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        page = br.contexts[0].new_page(); page.bring_to_front(); page.set_default_timeout(90000)
        page.goto(sd.TABLE_URL.format(vid=VID), wait_until="domcontentloaded", timeout=90000)
        parts, rows = [], {}
        for _ in range(20):
            time.sleep(3)
            parts = page.evaluate(sc.DEEP)
            rows = sd.parse_table(parts)
            if rows:
                break
        print("PARSE:", len(rows), "END:", sd.report_end_day(parts))
        print("non-str parts:", [t for t in parts if not isinstance(t, str)][:5])
        try:
            out = sd.summarize(rows, sd.report_end_day(parts), 320800.0, 541.1, 24200.0)
            print("SUMMARIZE OK:", {k: out[k] for k in ("last_data_day", "ctr_last_24h", "mark_needed")})
        except Exception:
            traceback.print_exc()
        page.close()
