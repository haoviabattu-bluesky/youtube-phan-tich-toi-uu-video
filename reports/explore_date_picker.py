# -*- coding: utf-8 -*-
r"""Do bo chon khoang thoi gian cua Studio (duong NGUOI THAT, khong URL epoch).

  py -3.13 reports/explore_date_picker.py --port 9222
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
CLICKABLE = """() => {
  const skip=new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']); const out=[];
  const walk=(root)=>{ for (const el of root.querySelectorAll('*')) {
    if (skip.has(el.tagName)) continue;
    if (el.shadowRoot) walk(el.shadowRoot);
    const tag=el.tagName.toLowerCase(), role=el.getAttribute?el.getAttribute('role')||'':'';
    const txt=(el.textContent||'').trim();
    if ((tag==='a'||tag==='button'||tag==='ytcp-button'||role==='button'||role==='tab'||role==='option'||tag==='paper-item') && txt && txt.length<60) {
      const r=el.getBoundingClientRect();
      if (r.width>2 && r.height>2) out.push({t:txt.slice(0,50), tag, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)});
    } } };
  walk(document); return out;
}"""

def click_label(page, label):
    r = page.evaluate(FIND, label)
    if not r: return False
    page.mouse.move(r["x"], r["y"], steps=12); time.sleep(0.4)
    page.mouse.click(r["x"], r["y"]); return True

ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=9222)
a = ap.parse_args()
ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5))["webSocketDebuggerUrl"]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    page = br.contexts[0].new_page(); page.bring_to_front(); page.set_default_timeout(90000)

    page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
    for _ in range(15):
        time.sleep(2)
        if "/channel/" in page.url: break
    click_label(page, "Content")
    for _ in range(15):
        time.sleep(2)
        if "/videos/upload" in page.url: break
    rows = page.eval_on_selector_all("ytcp-video-row", """els => els.map(e => {
        const a=e.querySelector('a#video-title'); const r=a?a.getBoundingClientRect():null;
        return {id:a?(a.href.split('/video/')[1]||'').split('/')[0]:'', x:r?Math.round(r.x+r.width/2):0, y:r?Math.round(r.y+r.height/2):0}; })""")
    t = rows[0]
    page.mouse.move(t["x"], t["y"], steps=14); time.sleep(0.5); page.mouse.click(t["x"], t["y"])
    for _ in range(15):
        time.sleep(2)
        if "/edit" in page.url: break
    click_label(page, "Analytics")
    for _ in range(15):
        time.sleep(2)
        if "/analytics/" in page.url: break
    click_label(page, "Reach")
    for _ in range(20):
        time.sleep(2)
        parts = page.evaluate(DEEP)
        if any(x.strip()=="Thumbnail impressions" for x in parts): break
    print("Reach OK:", page.url[:120], flush=True)

    label = [x for x in parts if ("Now" in x or "—" in x or "–" in x) and len(x)<40]
    print("nhan ngay:", label[:5], flush=True)
    if label:
        click_label(page, label[0])
        time.sleep(3)
        parts2 = page.evaluate(DEEP)
        print("\n=== sau khi bam nhan ngay: ===", flush=True)
        opts = [x for x in parts2 if x in ("Since published","First 24 hours","Last 7 days","Last 28 days",
                "Last 90 days","Last 365 days","Since uploaded (lifetime)","Custom","Apply","Cancel")
                or "day" in x.lower() and len(x)<25]
        print("tuy chon:", opts[:20], flush=True)
        print("\nclickable trong popup:", [c for c in page.evaluate(CLICKABLE) if c["y"]<600][:25], flush=True)
    page.close()
