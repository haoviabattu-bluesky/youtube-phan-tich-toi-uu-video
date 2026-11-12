# -*- coding: utf-8 -*-
"""Do UI binh luan YouTube (o nhap, nut gui) — khong gui gi."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = sys.argv[1]
VID = sys.argv[2]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=" + VID, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    # cuon xuong khu binh luan
    for _ in range(6):
        page.mouse.wheel(0, 900)
        time.sleep(1.5)
    time.sleep(4)
    info = page.evaluate("""() => {
      const out = {tags: [], simplebox: null, ce: [], buttons: []};
      out.tags = Array.from(new Set(Array.from(document.querySelectorAll('ytd-comments *'))
          .map(e=>e.tagName.toLowerCase()).filter(t=>t.includes('-')))).slice(0,60);
      const sb = document.querySelector('ytd-comment-simplebox-renderer, #simple-box, ytd-comments-header-renderer');
      out.simplebox = sb ? {tag: sb.tagName, text: (sb.innerText||'').slice(0,200)} : null;
      out.ce = Array.from(document.querySelectorAll('[contenteditable="true"], #contenteditable-root'))
          .map(e=>({tag:e.tagName, id:e.id, cls:(e.className||'').toString().slice(0,50),
                    ph:e.getAttribute('aria-label')||e.getAttribute('placeholder')||''})).slice(0,10);
      out.buttons = Array.from(document.querySelectorAll('ytd-commentbox #submit-button, #submit-button, ytd-button-renderer#submit-button button, tp-yt-paper-button#submit-button'))
          .map(e=>({tag:e.tagName, id:e.id, txt:(e.innerText||'').trim().slice(0,20), vis: !!e.offsetWidth}));
      out.comment_count = (document.querySelector('#count.ytd-comments-header-renderer .count-text, ytd-comments-header-renderer #count')
          ?.textContent || '').trim();
      return out;
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    page.screenshot(path=r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\probe_comment.png")
    br.close()
