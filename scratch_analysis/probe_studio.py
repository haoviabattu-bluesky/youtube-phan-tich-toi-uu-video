# -*- coding: utf-8 -*-
"""Xem trang Studio dang dung o dau + chup anh + liet ke nhan bam duoc."""
import sys, time
from playwright.sync_api import sync_playwright

WS = sys.argv[1]
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    print("PAGES:", len(ctx.pages))
    for i, pg in enumerate(ctx.pages):
        print(f"  [{i}] {pg.url[:110]}")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    print("\nACTIVE:", page.url)
    page.screenshot(path="reports/studio_stuck.png")
    labels = page.evaluate("""() => {
      const out = [];
      for (const el of document.querySelectorAll('a,button,ytcp-button,tp-yt-paper-tab,[role=tab]')) {
        const t = (el.innerText||'').trim();
        if (t && t.length < 40) out.push(t);
      }
      return [...new Set(out)];
    }""")
    print("\nLABELS:", labels[:70])
    rows = page.evaluate("() => document.querySelectorAll('ytcp-video-row').length")
    print("\nytcp-video-row:", rows)
