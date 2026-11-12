# -*- coding: utf-8 -*-
r"""Doc CTR 24h TRUOT (now-24h .. now) cho tung video lane X bang goto URL period-<ms>,<ms>.
Chi DOC, khong ghi sheet.

  PYTHONPATH= py -3.13 scratch_analysis/read_lane_x_24h.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))

from playwright.sync_api import sync_playwright   # noqa: E402

import daily_profiles as dp                      # noqa: E402
import studio_human as sh                        # noqa: E402
import spike_sources as ss                       # noqa: E402

MAIL = "theeuxanh1@gmail.com"
CID = "UC8BO9Ni37bUDbJrHez1zA7w"
OUT = os.path.join(ROOT, "reports", "may1_logon", "lane_x_24h.txt")
JSON_OUT = os.path.join(ROOT, "reports", "may1_logon", "lane_x_24h.json")

DEEP = """() => {
  const out = [];
  const walk = (node) => {
    for (const el of node.querySelectorAll('*')) {
      const tag = el.tagName;
      if (tag === 'STYLE' || tag === 'SCRIPT' || tag === 'NOSCRIPT' || tag === 'TEMPLATE') continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (!el.children.length) {
        const t = (el.textContent || '').trim();
        if (t && t.length < 140) {
          const r = el.getBoundingClientRect();
          if (r.width > 0 && r.height > 0) out.push(t);
        }
      }
    }
  };
  walk(document);
  return out;
}"""


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(" ".join(str(x) for x in a) + "\n")


def api_videos():
    api = ss.build("youtube", "v3", developerKey=ss.api_key(), cache_discovery=False)
    ch = api.channels().list(part="contentDetails", id=CID).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    its = api.playlistItems().list(part="contentDetails", playlistId=up, maxResults=25).execute()["items"]
    ids = [i["contentDetails"]["videoId"] for i in its]
    v = api.videos().list(part="snippet,statistics", id=",".join(ids)).execute()
    return [{"id": it["id"], "pub": it["snippet"]["publishedAt"],
             "views": int(it["statistics"].get("viewCount", 0))} for it in v["items"]]


def pick(lines, label):
    """Tra ve gia tri ngay sau nhan (bo qua o lap lai cua chinh nhan do)."""
    low = [x.strip().lower() for x in lines]
    for i, x in enumerate(low):
        if x == label.lower() or x.startswith(label.lower()):
            for j in range(i + 1, min(i + 4, len(lines))):
                val = lines[j].strip()
                if val.lower() == label.lower():
                    continue
                return val
    return None


def main() -> int:
    open(OUT, "w", encoding="utf-8").close()
    vids = api_videos()
    log(f"API: {len(vids)} video")
    data = {}
    g = {"engine": "gpm", "mail": MAIL, "tabs": ["X"]}
    with dp.open_group(g, log) as (ws, _l):
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            page = br.contexts[0].new_page()
            page.bring_to_front()
            page.set_default_timeout(120000)
            sh.maximize(page, log)
            for v in vids:
                now = int(time.time() * 1000)
                start = now - 24 * 3600 * 1000
                url = (f"https://studio.youtube.com/video/{v['id']}/analytics/tab-reach_viewers"
                       f"/period-{start},{now}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=120000)
                except Exception as exc:
                    log(f"    goto loi: {str(exc)[:70]}")
                time.sleep(random.uniform(9, 12))
                try:
                    lines = page.evaluate(DEEP)
                except Exception as exc:
                    log(f"    doc loi: {str(exc)[:60]}")
                    continue
                oops = any("Oops" in x for x in lines[:5])
                impr = pick(lines, "Thumbnail impressions")
                ctr = pick(lines, "Thumbnail click-through rate")
                views = pick(lines, "Views")
                log(f"  {v['id']} oops={oops} impr={impr} ctr={ctr} views={views}")
                data[v["id"]] = {"impr": impr, "ctr": ctr, "views24": views,
                                 "views_total": v["views"], "pub": v["pub"], "lines": lines}
                with open(JSON_OUT, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                time.sleep(random.uniform(2, 4))
            page.close()
    log("XONG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
