# -*- coding: utf-8 -*-
"""Liet ke video upload moi nhat cua 2 kenh Lane-P / Lane-GEO + stats (Data API v3)."""
import json, re, sys, urllib.request, urllib.parse, os

ENV = r"E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env"
key = os.environ.get("YOUTUBE_API_KEY")
if not key and os.path.exists(ENV):
    for ln in open(ENV, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*YOUTUBE_API_KEY\s*=\s*(\S+)", ln)
        if m:
            key = m.group(1).strip().strip('"').strip("'")
if not key:
    sys.exit("KHONG CO API KEY")

BASE = "https://www.googleapis.com/youtube/v3/"


def get(path, **p):
    p["key"] = key
    url = BASE + path + "?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def channel_id(handle):
    for p in ("forHandle", "forUsername"):
        try:
            d = get("channels", part="id,snippet,contentDetails", **{p: handle})
            if d.get("items"):
                return d["items"][0]
        except Exception as e:
            print("  ", p, "loi", e)
    return None


for label, handle in (("Lane-P", "@nihon-kigyo-watch"), ("Lane-GEO", "@ai-kaimei-lab")):
    ch = channel_id(handle)
    if not ch:
        print(label, handle, "KHONG TIM THAY KENH")
        continue
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    print("=" * 90)
    print(f"{label} {handle} id={ch['id']} ten={ch['snippet']['title']}")
    items, tok = [], None
    while True:
        d = get("playlistItems", part="snippet,contentDetails", playlistId=up, maxResults="50", **({"pageToken": tok} if tok else {}))
        items += d.get("items", [])
        tok = d.get("nextPageToken")
        if not tok or len(items) >= 50:
            break
    vid = [i["contentDetails"]["videoId"] for i in items]
    stats = get("videos", part="snippet,statistics,status", id=",".join(vid[:50]))
    sm = {v["id"]: v for v in stats["items"]}
    for i in items[:15]:
        v = sm.get(i["contentDetails"]["videoId"], {})
        st = v.get("statistics", {})
        print(f"  {i['contentDetails']['videoId']}  {i['contentDetails'].get('videoPublishedAt','?')}  view={st.get('viewCount','?'):>8}  {v.get('snippet',{}).get('title','')[:70]}")
