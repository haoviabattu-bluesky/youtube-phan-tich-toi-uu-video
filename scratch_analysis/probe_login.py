# -*- coding: utf-8 -*-
"""Kiem tra profile GPM dang login YouTube nao (doc CHANNEL_ID + HL + ten kenh)."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:60233/devtools/browser/b1e4d7fe-8a03-462d-b315-5918fe6b815a"

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(5)
    info = page.evaluate("""() => {
      const d = (window.ytcfg && window.ytcfg.data_) || {};
      return {channel: d.CHANNEL_ID || null, hl: d.HL || null, gl: d.GL || null,
              logged_in: !!(d.CHANNEL_ID), url: location.href,
              title: document.title,
              avatar: !!document.querySelector('#avatar-btn'),
              account: (document.querySelector('#account-name, ytd-account-item-renderer #channel-title')
                        ?.textContent || '').trim()};
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    br.close()
