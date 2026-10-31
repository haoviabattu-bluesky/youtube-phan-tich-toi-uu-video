# -*- coding: utf-8 -*-
r"""Do hop 'Custom' + kiem tra co chon duoc GIO khong (duong NGUOI THAT).

  py -3.13 reports/explore_custom2.py --port 9222
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
FIND = """(label) => {
  let hit=null;
  const walk=(root)=>{ for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (!hit && el.children.length===0 && (el.textContent||'').trim()===label) hit=el; } };
  walk(document);
  if(!hit) return null;
  const r=hit.getBoundingClientRect();
  return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), w:Math.round(r.width), h:Math.round(r.height)};
}"""
INPUTS = """() => {
  const skip=new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']); const out=[];
  const walk=(root)=>{ for (const el of root.querySelectorAll('*')) {
    if (skip.has(el.tagName)) continue;
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName==='INPUT'||el.tagName==='TEXTAREA') {
      const r=el.getBoundingClientRect();
      if (r.width>2&&r.height>2) out.push({type:el.getAttribute('type')||'', id:(el.id||'').slice(0,30),
        ph:(el.getAttribute('placeholder')||el.getAttribute('aria-label')||'').slice(0,40),
        val:(el.value||'').slice(0,30), x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)});
    } } };
  walk(document); return out;
}"""
CLICKABLE = """() => {
  const skip=new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']); const out=[];
  const walk=(root)=>{ for (const el of root.querySelectorAll('*')) {
    if (skip.has(el.tagName)) continue;
    if (el.shadowRoot) walk(el.shadowRoot);
    const tag=el.tagName.toLowerCase(), role=el.getAttribute?el.getAttribute('role')||'':'';
    const txt=(el.textContent||'').trim();
    if ((tag==='a'||tag==='button'||tag==='ytcp-button'||tag==='tp-yt-paper-item'||role==='button'||role==='option') && txt && txt.length<40) {
      const r=el.getBoundingClientRect();
      if (r.width>2&&r.height>2&&r.y>100) out.push({t:txt.slice(0,30), tag, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)});
    } } };
  walk(document); return out;
}"""

def click_label(page, label, wait=1.5):
    r = page.evaluate(FIND, label)
    if not r: return False
    page.mouse.move(r["x"], r["y"], steps=12); time.sleep(0.4)
    page.mouse.click(r["x"], r["y"]); time.sleep(wait); return True

def wait_for(page, pred, tries=20, gap=2):
    parts = []
    for _ in range(tries):
        time.sleep(gap)
        parts = page.evaluate(DEEP)
        if pred(parts): return parts
    return parts

ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=9222)
a = ap.parse_args()
ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5))["webSocketDebuggerUrl"]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    page = br.contexts[0].new_page(); page.bring_to_front(); page.set_default_timeout(90000)

    page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
    wait_for(page, lambda pt: "/channel/" in page.url, 15)
    print("1. channel:", page.url[-40:], flush=True)
    click_label(page, "Content", 3)
    wait_for(page, lambda pt: "/videos/upload" in page.url, 15)
    rows = page.eval_on_selector_all("ytcp-video-row", """els => els.map(e => {
        const a=e.querySelector('a#video-title'); const r=a?a.getBoundingClientRect():null;
        return {id:a?(a.href.split('/video/')[1]||'').split('/')[0]:'', x:r?Math.round(r.x+r.width/2):0, y:r?Math.round(r.y+r.height/2):0}; })""")
    print("2. video rows:", len(rows), flush=True)
    t = rows[0]
    page.mouse.move(t["x"], t["y"], steps=14); time.sleep(0.5); page.mouse.click(t["x"], t["y"])
    wait_for(page, lambda pt: "/edit" in page.url, 15)
    print("3. edit:", page.url[-30:], flush=True)
    click_label(page, "Analytics", 3)
    wait_for(page, lambda pt: "/analytics/" in page.url, 15)
    print("4. analytics:", page.url[-50:], flush=True)
    click_label(page, "Reach", 3)
    parts = wait_for(page, lambda pt: any(x.strip()=="Thumbnail impressions" for x in pt), 25)
    print("5. reach, co so:", any(x.strip()=="Thumbnail impressions" for x in parts), flush=True)

    lab = [x for x in parts if ("Now" in x or "—" in x) and len(x)<40]
    print("6. nhan ngay:", lab[:3], flush=True)
    if lab:
        click_label(page, lab[0], 3)
        print("7. bam Custom...", flush=True)
        ok = click_label(page, "Custom", 3)
        print("   Custom click:", ok, flush=True)
        parts2 = page.evaluate(DEEP)
        print("\n8. text hop:", [x for x in parts2 if len(x)<30][-40:], flush=True)
        print("\n9. INPUT:", page.evaluate(INPUTS)[:10], flush=True)
        print("\n10. clickable (y>150):", [c for c in page.evaluate(CLICKABLE) if c["y"]>150][:20], flush=True)
    page.close()
