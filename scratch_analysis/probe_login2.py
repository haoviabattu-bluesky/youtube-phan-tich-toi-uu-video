# -*- coding: utf-8 -*-
"""Kiem tra sau: avatar, account name, ytcfg co day du, cookie SAPISID."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = sys.argv[1]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    info = page.evaluate("""() => {
      const d = (window.ytcfg && window.ytcfg.data_) || {};
      const names = [];
      try {
        const resp = window.ytInitialData || {};
        const hdr = resp.header || {};
        names.push(JSON.stringify(Object.keys(resp).slice(0,40)));
      } catch(e) { names.push('err '+e); }
      return {
        keys: Object.keys(d).filter(k=>/CHANNEL|HL|GL|SESSION|LOGGED|PAGE/i.test(k)),
        channel: d.CHANNEL_ID || null, hl: d.HL || null, gl: d.GL || null,
        session_index: d.SESSION_INDEX, visitor: d.VISITOR_DATA ? 'yes':'no',
        title: document.title, url: location.href,
        cookie: document.cookie.slice(0,300),
        avatar_html: (document.querySelector('#avatar-btn')||{}).outerHTML?.slice(0,400) || null,
        buttons: Array.from(document.querySelectorAll('ytd-topbar-menu-button-renderer, #buttons ytd-button-renderer')).slice(0,6).map(e=>e.textContent.trim().slice(0,40)),
        ytInitialKeys: names
      };
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    page.screenshot(path=r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\probe_yt.png")
    print("screenshot saved")
    br.close()
