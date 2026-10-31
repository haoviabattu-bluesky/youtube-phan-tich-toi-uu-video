# -*- coding: utf-8 -*-
r"""Do tiep duong NGUOI THAT: click video -> Analytics -> Reach -> menu thoi gian.

  py -3.13 reports/explore_human_path2.py --port 9222
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

def click_label(page, label, log=print):
    r = page.evaluate(FIND, label)
    log(f"  tim '{label}': {r}")
    if not r:
        return False
    page.mouse.move(r["x"], r["y"], steps=12); time.sleep(0.4)
    page.mouse.click(r["x"], r["y"])
    return True

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=9222)
a = ap.parse_args()
ws = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5))["webSocketDebuggerUrl"]

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(ws)
    page = br.contexts[0].new_page()
    page.bring_to_front()
    page.set_default_timeout(90000)

    # Vao lai danh sach video roi click video dau (duong nguoi that)
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
        return {title:a?a.innerText.trim():'', id:a?(a.href.split('/video/')[1]||'').split('/')[0]:'',
                x:r?Math.round(r.x+r.width/2):0, y:r?Math.round(r.y+r.height/2):0}; })""")
    t = rows[0]; print("click video:", t["id"], t["title"][:40], flush=True)
    page.mouse.move(t["x"], t["y"], steps=14); time.sleep(0.5); page.mouse.click(t["x"], t["y"])
    for _ in range(15):
        time.sleep(2)
        if "/edit" in page.url: break
    print("URL edit:", page.url[:100], flush=True)

    print("\n=== bam tab 'Analytics' ===", flush=True)
    click_label(page, "Analytics")
    for _ in range(15):
        time.sleep(2)
        if "/analytics/" in page.url: break
    print("URL analytics:", page.url[:140], flush=True)
    parts = page.evaluate(DEEP)
    print("text:", [x for x in parts if x in ("Overview","Reach","Engagement","Audience","Revenue","Advanced mode","Show more")][:10], flush=True)

    print("\n=== bam tab 'Reach' ===", flush=True)
    click_label(page, "Reach")
    for _ in range(20):
        time.sleep(2)
        parts = page.evaluate(DEEP)
        if any(t.strip() == "Thumbnail impressions" for t in parts): break
    print("URL reach:", page.url[:160], flush=True)
    print("co 'Thumbnail impressions':", any(t.strip()=="Thumbnail impressions" for t in parts), flush=True)

    print("\n=== tim o chon khoang thoi gian (goc phai tren) ===", flush=True)
    # Studio hien nhan khoang ngay vd "Sep 24, 2026 – Now"
    cand = [x for x in parts if ("–" in x or "—" in x or "Now" in x) and len(x) < 60]
    print("ung vien nhan ngay:", cand[:8], flush=True)
    for c in cand[:3]:
        r = page.evaluate(FIND, c)
        print(f"  '{c}' -> {r}", flush=True)
    page.close()
