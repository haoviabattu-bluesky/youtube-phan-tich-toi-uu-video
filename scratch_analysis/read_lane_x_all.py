# -*- coding: utf-8 -*-
r"""Doc Reach + Overview cho TAT CA video lane X (goto URL period-<start>,<end>).
Chi DOC. Dump text da loc (bo STYLE/SCRIPT, chi node hien) ra reports/may1_logon/lane_x_all.txt
va JSON tung video de phan tich sau.

  PYTHONPATH= py -3.13 scratch_analysis/read_lane_x_all.py
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
OUT = os.path.join(ROOT, "reports", "may1_logon", "lane_x_all.txt")
JSON_OUT = os.path.join(ROOT, "reports", "may1_logon", "lane_x_all.json")

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

KEYS = [
    "impression", "click-through", "views", "watch time", "average view duration",
    "average percentage viewed", "browse features", "suggested videos", "youtube search",
    "external", "direct", "other", "content suggesting", "shorts feed", "playlists",
    "channel pages", "notifications", "subscriptions",
]


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
    v = api.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute()
    out = []
    for it in v["items"]:
        out.append({
            "id": it["id"],
            "title": it["snippet"]["title"],
            "pub": it["snippet"]["publishedAt"],
            "dur": it["contentDetails"]["duration"],
            "views": int(it["statistics"].get("viewCount", 0)),
            "likes": int(it["statistics"].get("likeCount", 0) or 0),
            "comments": int(it["statistics"].get("commentCount", 0) or 0),
        })
    return out


def windows(lines, keys, span=2):
    seen = set()
    res = []
    low = [x.lower() for x in lines]
    for i, ln in enumerate(low):
        if any(k in ln for k in keys):
            a, b = max(0, i - span), min(len(lines), i + span + 1)
            key = (a, b)
            if key in seen:
                continue
            seen.add(key)
            res.append(" ¦ ".join(lines[a:b]))
    return res[:25]


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
                pub = int(time.mktime(time.strptime(v["pub"][:19], "%Y-%m-%dT%H:%M:%S")) * 1000)
                rec = {"meta": v, "reach": [], "overview": []}
                for tab in ("tab-reach_viewers", "tab-overview"):
                    url = (f"https://studio.youtube.com/video/{v['id']}/analytics/{tab}"
                           f"/period-{pub},{now}")
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=120000)
                    except Exception as exc:
                        log(f"    goto loi {tab}: {str(exc)[:70]}")
                    time.sleep(random.uniform(10, 13))
                    try:
                        lines = page.evaluate(DEEP)
                    except Exception as exc:
                        log(f"    doc loi: {str(exc)[:60]}")
                        continue
                    oops = any("Oops" in x for x in lines[:5])
                    log(f"  == {v['id']} {tab} oops={oops} lines={len(lines)}")
                    if oops:
                        continue
                    got = windows(lines, KEYS)
                    rec["reach" if tab.endswith("reach_viewers") else "overview"] = lines
                    for s in got:
                        log("     *", s[:200])
                    time.sleep(random.uniform(2, 4))
                data[v["id"]] = rec
                with open(JSON_OUT, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            page.close()
    log("XONG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
