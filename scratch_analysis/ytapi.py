# -*- coding: utf-8 -*-
"""Helper YouTube Data API v3 (doc key tu env hoac file .env cua TRENDING-RESEARCH)."""
import json, os, re, urllib.parse, urllib.request

ENV = r"E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env"
BASE = "https://www.googleapis.com/youtube/v3/"
_key = None


def key():
    global _key
    if _key:
        return _key
    k = os.environ.get("YOUTUBE_API_KEY")
    if not k and os.path.exists(ENV):
        for ln in open(ENV, encoding="utf-8", errors="replace"):
            m = re.match(r"\s*YOUTUBE_API_KEY\s*=\s*(\S+)", ln)
            if m:
                k = m.group(1).strip().strip('"').strip("'")
    if not k:
        raise SystemExit("KHONG CO YOUTUBE_API_KEY")
    _key = k
    return k


def get(path, **p):
    p["key"] = key()
    url = BASE + path + "?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)
