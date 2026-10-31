# -*- coding: utf-8 -*-
r"""Do DOM Studio theo duong NGUOI THAT (khong goto URL video).

  py -3.13 reports/explore_human_path.py --port 9222
"""
import sys, os, json, time, argparse, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from playwright.sync_api import sync_playwright

DEEP = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
  const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (skip.has(el.tagName)) continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (el.children.length === 0) { const t=(el.textContent||'').trim(); if (t && t.length<160) out.push(t); } } };
  walk(document); return out;
}"""

# Liet ke phan tu BAM DUOC (co role/link/button) trong shadow DOM, kem toa do
CLICKABLE = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
  const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (skip.has(el.tagName)) continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      const tag = el.tagName.toLowerCase();
      const role = el.getAttribute && (el.getAttribute('role')||'');
      const txt = (el.textContent||'').trim();
      const isClickable = (tag==='a'||tag==='button'||role==='button'||role==='link'||role==='tab'||tag==='ytcp-button');
      if (isClickable && txt && txt.length<90) {
        const r = el.getBoundingClientRect();
        if (r.width>1 && r.height>1) out.push({t:txt, tag:tag, role:role, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), w:Math.round(r.width)});
      } } };
  walk(document); return out;
}"""

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=9222)
a = ap.parse_args()
ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5))["webSocketDebuggerUrl"]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    ctx = br.contexts[0]
    page = ctx.new_page()
    page.bring_to_front()
    page.set_default_timeout(90000)

    print("=== 1. mo studio.youtube.com (root) ===", flush=True)
    page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
    for _ in range(15):
        time.sleep(2)
        if "/channel/" in page.url or "accounts.google" in page.url:
            break
    print("URL:", page.url[:120], flush=True)
    if "accounts.google" in page.url:
        print("CHUA LOGIN"); sys.exit(2)

    parts = page.evaluate(DEEP)
    print("so text:", len(parts), flush=True)
    print("NAV:", [t for t in parts if t in ("Dashboard","Content","Analytics","Comments","Subtitles","Copyright","Earn","Customization","Audio library")], flush=True)

    print("\n=== 2. bam 'Content' (menu trai) ===", flush=True)
    got = page.evaluate("""(label) => {
      let hit=null;
      const walk=(root)=>{ for (const el of root.querySelectorAll('*')) {
        if (el.shadowRoot) walk(el.shadowRoot);
        if (!hit && el.children.length===0 && (el.textContent||'').trim()===label) hit=el; } };
      walk(document);
      if(!hit) return null;
      const r=hit.getBoundingClientRect();
      return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), w:Math.round(r.width), h:Math.round(r.height)};
    }""", "Content")
    print("rect 'Content':", got, flush=True)
    if got:
        page.mouse.move(got["x"], got["y"], steps=12); time.sleep(0.4)
        page.mouse.click(got["x"], got["y"])
    for _ in range(15):
        time.sleep(2)
        if "/videos/upload" in page.url:
            break
    print("URL sau khi bam Content:", page.url[:140], flush=True)

    print("\n=== 3. danh sach video (ytcp-video-row) ===", flush=True)
    rows = page.eval_on_selector_all("ytcp-video-row", """els => els.map((e,i) => {
        const a = e.querySelector('a#video-title');
        const r = a ? a.getBoundingClientRect() : null;
        return {i, title: a ? a.innerText.trim() : '', id: a ? (a.href.split('/video/')[1]||'').split('/')[0] : '',
                x: r?Math.round(r.x+r.width/2):0, y: r?Math.round(r.y+r.height/2):0};
    })""")
    for r in rows[:5]:
        print("  ", r["i"], r["id"], r["title"][:45], f"@({r['x']},{r['y']})", flush=True)

    if rows:
        print("\n=== 4. click video dau tien (chuot that) ===", flush=True)
        t = rows[0]
        page.mouse.move(t["x"], t["y"], steps=14); time.sleep(0.5)
        page.mouse.click(t["x"], t["y"])
        for _ in range(15):
            time.sleep(2)
            if "/video/" in page.url and "/edit" in page.url:
                break
        print("URL sau click video:", page.url[:150], flush=True)
        parts = page.evaluate(DEEP)
        print("co 'Analytics' trong trang:", "Analytics" in parts, flush=True)
        print("text mau:", [x for x in parts if x in ("Details","Analytics","Comments","Editor","Video analytics")][:8], flush=True)
    page.close()
