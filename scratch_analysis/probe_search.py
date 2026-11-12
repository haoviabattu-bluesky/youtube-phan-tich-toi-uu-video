# -*- coding: utf-8 -*-
"""Do ket qua tim kiem YouTube (id, tieu de, kenh, thoi luong) — KHONG xem, KHONG like."""
import sys, time, json, random
from urllib.parse import quote
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

WS = sys.argv[1]
KW = sys.argv[2] if len(sys.argv) > 2 else ""

JS_RESULTS = """(lim) => {
  const out = [];
  const els = document.querySelectorAll('ytd-video-renderer, ytd-rich-item-renderer');
  for (const el of els) {
    const a = el.querySelector('a#video-title, a#thumbnail[href*="watch"]');
    if (!a) continue;
    const href = a.getAttribute('href') || '';
    const m = href.match(/[?&]v=([\\w-]{6,})/);
    if (!m) continue;
    const t = (el.querySelector('#video-title')?.textContent || a.getAttribute('title') || '').trim();
    const ch = (el.querySelector('ytd-channel-name a, #channel-name a')?.textContent || '').trim();
    const meta = Array.from(el.querySelectorAll('#metadata-line span, .inline-metadata-item'))
        .map(s => (s.textContent||'').trim()).filter(Boolean);
    const badge = (el.querySelector('ytd-badge-supported-renderer, .badge-shape-wiz__text')?.textContent||'').trim();
    const dur = (el.querySelector('ytd-thumbnail-overlay-time-status-renderer #text, .ytd-thumbnail-overlay-time-status-renderer, badge-shape')?.textContent||'').trim();
    if (out.find(o => o.id === m[1])) continue;
    out.push({id: m[1], title: t, ch: ch, meta: meta, dur: dur, badge: badge});
    if (out.length >= lim) break;
  }
  return out;
}"""

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(WS)
    ctx = br.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(3)
    box = None
    for sel in ["input#search", "input[name='search_query']", "ytd-searchbox input"]:
        box = page.query_selector(sel)
        if box:
            break
    if box:
        box.click(); time.sleep(random.uniform(0.6, 1.2))
        page.keyboard.insert_text(KW)
        time.sleep(random.uniform(0.8, 1.4))
        page.keyboard.press("Enter")
    else:
        page.goto("https://www.youtube.com/results?search_query=" + quote(KW),
                  wait_until="domcontentloaded", timeout=90000)
    time.sleep(6)
    res = page.evaluate(JS_RESULTS, 10)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    br.close()
