# -*- coding: utf-8 -*-
"""Do UI: nut like + comment box (click simplebox roi doc DOM, KHONG go, KHONG gui)."""
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
    time.sleep(9)
    like = page.evaluate("""() => {
      const out = [];
      for (const sel of ['like-button-view-model button','segmented-like-dislike-button-view-model button',
                         '#segmented-like-button button','ytd-toggle-button-renderer#like-button button',
                         'button[aria-label*="like"]']) {
        const els = document.querySelectorAll(sel);
        els.forEach((b,i)=>out.push({sel:sel, i:i, vis:!!b.offsetWidth,
          aria:b.getAttribute('aria-label'), pressed:b.getAttribute('aria-pressed'),
          txt:(b.innerText||'').trim().slice(0,20)}));
      }
      return out;
    }""")
    print("LIKE:", json.dumps(like, ensure_ascii=False, indent=1))

    # cuon toi khu comment
    for _ in range(5):
        page.mouse.wheel(0, 800); time.sleep(1.2)
    time.sleep(3)
    # click vao simplebox
    box = page.query_selector("ytd-comment-simplebox-renderer #simplebox-placeholder, #simplebox-placeholder")
    print("simplebox placeholder found:", bool(box))
    if box:
        box.click()
        time.sleep(3)
    info = page.evaluate("""() => {
      const cb = document.querySelector('ytd-commentbox, ytd-comment-dialog-renderer');
      const ce = Array.from(document.querySelectorAll('#contenteditable-root')).map(e=>{
        const r = e.getBoundingClientRect();
        return {w:r.width, h:r.height, tag:e.tagName, aria:e.getAttribute('aria-label')};
      });
      const btn = Array.from(document.querySelectorAll('#submit-button, #submit-button button')).map(e=>{
        const r=e.getBoundingClientRect();
        return {tag:e.tagName, txt:(e.innerText||'').trim().slice(0,20), w:r.width, h:r.height, dis:e.disabled};
      });
      return {has_commentbox: !!cb, ce: ce, submit: btn,
              cb_tags: cb ? Array.from(new Set(Array.from(cb.querySelectorAll('*')).map(e=>e.tagName.toLowerCase()).filter(t=>t.includes('-')))).slice(0,40) : []};
    }""")
    print("COMMENTBOX:", json.dumps(info, ensure_ascii=False, indent=1))
    page.screenshot(path=r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\probe_cbox.png")
    br.close()
