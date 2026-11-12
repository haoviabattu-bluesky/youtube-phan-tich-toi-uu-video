# -*- coding: utf-8 -*-
"""Kiem tra THAT xem comment da dang chua: mo video, sort Newest, doc toan bo text comment."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = "ws://localhost:60233/devtools/browser/b1e4d7fe-8a03-462d-b315-5918fe6b815a"
VID = sys.argv[1] if len(sys.argv) > 1 else "CR9KU_5djOg"
NEEDLE = "素晴らしい"

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=" + VID, wait_until="domcontentloaded", timeout=90000)
    time.sleep(10)
    # ten tai khoan dang nhap
    acct = page.evaluate("""() => {
      const el = document.querySelector('#avatar-btn, ytd-topbar-menu-button-renderer #avatar-btn');
      const img = el ? el.querySelector('img') : null;
      return {aria: el ? el.getAttribute('aria-label') : null, alt: img ? img.alt : null};
    }""")
    print("ACCOUNT:", json.dumps(acct, ensure_ascii=False))

    for _ in range(10):
        page.mouse.wheel(0, 900); time.sleep(1.2)
    time.sleep(4)

    # sort -> Newest first
    sorted_ok = page.evaluate("""() => {
      const btns = Array.from(document.querySelectorAll('yt-sort-filter-sub-menu-renderer tp-yt-paper-button, #sort-menu, yt-dropdown-menu #button'));
      for (const b of btns) { const r=b.getBoundingClientRect(); if (r.width>20) { b.click(); return true; } }
      return false;
    }""")
    time.sleep(2.5)
    newest = page.evaluate("""() => {
      const items = Array.from(document.querySelectorAll('tp-yt-paper-item, ytd-menu-service-item-renderer'));
      for (const it of items) {
        const t = (it.innerText||'').trim();
        if (/Newest/i.test(t)) { it.click(); return t; }
      }
      return null;
    }""")
    print("sort clicked:", sorted_ok, "| newest item:", newest)
    time.sleep(5)

    data = page.evaluate("""(needle) => {
      const els = document.querySelectorAll('ytd-comment-thread-renderer, ytd-comment-view-model');
      const out = [];
      let hit = null;
      for (const el of els) {
        const au = el.querySelector('#author-text');
        const tx = el.querySelector('#content-text');
        const a = au ? (au.textContent||'').trim() : '';
        const t = tx ? (tx.textContent||'').trim() : '';
        if (!t) continue;
        out.push({a: a, t: t.slice(0, 60)});
        if (t.includes(needle)) hit = {a: a, t: t};
      }
      return {count: out.length, first8: out.slice(0, 8), hit: hit};
    }""", NEEDLE)
    print("COMMENTS:", json.dumps(data, ensure_ascii=False, indent=1))
    page.screenshot(path=r"E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\scratch_analysis\verify_comment.png")
    br.close()
