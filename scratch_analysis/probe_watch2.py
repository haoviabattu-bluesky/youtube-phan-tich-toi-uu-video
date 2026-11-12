# -*- coding: utf-8 -*-
"""Do panel goi y ben phai (layout moi yt-lockup-view-model) tren trang watch."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = sys.argv[1]
VID = sys.argv[2]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if VID:
        page.goto("https://www.youtube.com/watch?v=" + VID, wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)
    info = page.evaluate("""() => {
      const pick = (root) => {
        const out = [];
        const els = root.querySelectorAll('yt-lockup-view-model, ytd-compact-video-renderer, ytd-video-renderer, ytd-rich-item-renderer');
        for (const el of els) {
          const a = el.querySelector('a[href*="watch?v="]');
          if (!a) continue;
          const m = (a.getAttribute('href')||'').match(/[?&]v=([\\w-]{6,})/);
          if (!m) continue;
          const txt = el.innerText.split('\\n').map(s=>s.trim()).filter(Boolean);
          if (out.find(o=>o.id===m[1])) continue;
          out.push({id:m[1], lines:txt.slice(0,6)});
        }
        return out;
      };
      const side = document.querySelector('#secondary, ytd-watch-next-secondary-results-renderer');
      const prim = document.querySelector('#primary');
      return {
        has_secondary: !!side,
        side_count: side ? side.querySelectorAll('yt-lockup-view-model, ytd-compact-video-renderer').length : -1,
        side: side ? pick(side).slice(0,20) : [],
        primary: prim ? pick(prim).slice(0,5) : [],
        vw: window.innerWidth, vh: window.innerHeight,
        body_tags: Array.from(new Set(Array.from(document.querySelectorAll('#secondary *')).map(e=>e.tagName.toLowerCase()).filter(t=>t.includes('-')))).slice(0,40)
      };
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    page.screenshot(path=r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\probe_watch2.png")
    br.close()
