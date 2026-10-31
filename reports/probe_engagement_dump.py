# -*- coding: utf-8 -*-
"""Probe 2: dump text Engagement tab + vung header bang theo ngay de tim nhan khoang ngay."""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright
import studio_collect as sc
import studio_daily as sd

VID = sys.argv[1] if len(sys.argv) > 1 else "nNlqnf28Kak"
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = br.contexts[0].new_page()
    page.bring_to_front(); page.set_default_timeout(90000)

    page.goto(f"https://studio.youtube.com/video/{VID}/analytics/tab-engagement/period-default",
              wait_until="domcontentloaded", timeout=90000)
    time.sleep(10)
    parts = page.evaluate(sc.DEEP)
    print("N_PARTS:", len(parts))
    json.dump(parts, open("reports/probe_engagement_parts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("---- first 120 ----")
    for i, t in enumerate(parts[:120]):
        print(i, repr(t[:110]))
    print("---- keyword hits ----")
    for kw in ("watching", "retention", "%", "duration", "Typical"):
        hits = [(i, t) for i, t in enumerate(parts) if kw in t]
        print(kw, "->", hits[:6])

    page.goto(sd.TABLE_URL.format(vid=VID), wait_until="domcontentloaded", timeout=90000)
    time.sleep(12)
    parts2 = page.evaluate(sc.DEEP)
    json.dump(parts2, open("reports/probe_table_parts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    i = max((k for k, t in enumerate(parts2) if t == "Total"), default=None)
    print("TOTAL_IDX:", i)
    if i:
        print("AROUND TOTAL:", parts2[max(0, i - 40):i + 6])
    print("date-ish:", [t for t in parts2 if any(m in t for m in ("–", "-", "2026"))][:12])
    page.close()
