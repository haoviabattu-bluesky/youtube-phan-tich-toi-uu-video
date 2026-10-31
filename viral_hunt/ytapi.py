# -*- coding: utf-8 -*-
"""ytapi.py — YouTube Data API v3, tiết kiệm quota.

Quota (mặc định 10.000 unit/ngày cho cả project):
  search.list   = 100 unit / call   ← đắt nhất, đây là thứ phải canh
  videos.list   = 1 unit / call (tối đa 50 id)
  channels.list = 1 unit / call (tối đa 50 id)
  playlistItems = 1 unit / call (tối đa 50 item)

Chiến lược của tool: mỗi lane 8–10 từ khoá × 1 call search (order=viewCount,
publishedAfter=5 ngày) ⇒ ~40 call = 4.000 unit. Sau đó chỉ dùng videos/channels/
playlistItems (1 unit) để chấm điểm ⇒ tổng ~4.100 unit/ngày.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KEY_ENV = "YOUTUBE_API_KEY"
KEY_ENV_FILE = r"E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env"
API = "https://www.googleapis.com/youtube/v3/"
COST = {"search": 100, "videos": 1, "channels": 1, "playlistItems": 1}


class QuotaExceeded(RuntimeError):
    pass


def api_key():
    k = os.environ.get(KEY_ENV, "").strip()
    if not k and os.path.exists(KEY_ENV_FILE):
        for ln in open(KEY_ENV_FILE, encoding="utf-8").read().splitlines():
            if ln.startswith(KEY_ENV + "="):
                k = ln.split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        raise SystemExit(f"thiếu {KEY_ENV} (env hoặc {KEY_ENV_FILE})")
    return k


def parse_duration(iso):
    """PT22M1S -> giây. Trả 0 nếu không đọc được."""
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = [int(x or 0) for x in m.groups()]
    return d * 86400 + h * 3600 + mi * 60 + s


class YT:
    def __init__(self, key=None, budget=None):
        self.key = key or api_key()
        self.budget = budget            # None = không chặn
        self.units = 0
        self.calls = {"search": 0, "videos": 0, "channels": 0, "playlistItems": 0}
        self.errors = []

    # ------------------------------------------------------------------ core
    def _get(self, endpoint, params, tries=3):
        cost = COST[endpoint]
        if self.budget is not None and self.units + cost > self.budget:
            raise QuotaExceeded(
                f"hết ngân sách quota: đã dùng {self.units}/{self.budget} unit, "
                f"call {endpoint} cần {cost}")
        params = dict(params, key=self.key)
        url = API + endpoint + "?" + urllib.parse.urlencode(params)
        last = None
        for attempt in range(1, tries + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "viral-hunt/1.0"})
                with urllib.request.urlopen(req, timeout=40) as r:
                    data = json.loads(r.read().decode("utf-8"))
                self.units += cost
                self.calls[endpoint] += 1
                return data
            except urllib.error.HTTPError as e:
                body = e.read()[:400].decode("utf-8", "replace")
                last = f"HTTP {e.code} {body}"
                # 403 quotaExceeded / rateLimitExceeded: retry không cứu được
                if e.code in (400, 401):
                    break
                if e.code == 403 and ("quota" in body.lower() or "rateLimit" in body):
                    raise QuotaExceeded(body)
                time.sleep(2 * attempt)
            except Exception as e:                      # noqa: BLE001
                last = f"{type(e).__name__} {e}"
                time.sleep(2 * attempt)
        self.errors.append(f"{endpoint}: {last}")
        return {"items": [], "_error": last}

    # ------------------------------------------------------------------ reads
    def search(self, q, published_after, order="viewCount", max_results=50, region="JP"):
        """1 call = 100 unit. Trả list item search (id.videoId + snippet)."""
        d = self._get("search", {
            "part": "snippet", "q": q, "type": "video", "order": order,
            "maxResults": min(max_results, 50), "publishedAfter": published_after,
            "regionCode": region, "relevanceLanguage": "ja",
        })
        out = []
        for it in d.get("items", []):
            vid = (it.get("id") or {}).get("videoId")
            if vid:
                out.append({"video_id": vid, "snippet": it["snippet"], "keyword": q})
        return out

    def videos(self, ids):
        out = []
        ids = [i for i in dict.fromkeys(ids) if i]
        for i in range(0, len(ids), 50):
            d = self._get("videos", {
                "part": "snippet,statistics,contentDetails,status",
                "id": ",".join(ids[i:i + 50]), "maxResults": 50})
            out += d.get("items", [])
        return out

    def channels(self, ids):
        out = []
        ids = [i for i in dict.fromkeys(ids) if i]
        for i in range(0, len(ids), 50):
            d = self._get("channels", {
                "part": "snippet,statistics,contentDetails,brandingSettings",
                "id": ",".join(ids[i:i + 50]), "maxResults": 50})
            out += d.get("items", [])
        return out

    def uploads_sample(self, channel_id, uploads_playlist, n=30):
        """Lấy tối đa n tiêu đề video gần nhất của kênh (1 unit) — để đo tỉ lệ manga."""
        if not uploads_playlist:
            return []
        d = self._get("playlistItems", {
            "part": "snippet", "playlistId": uploads_playlist,
            "maxResults": min(n, 50)})
        return [(it.get("snippet") or {}).get("title", "") for it in d.get("items", [])]

    def playlist_items(self, playlist_id, n=50):
        """50 video mới nhất của playlist uploads (1 unit). Trả list snippet."""
        if not playlist_id:
            return []
        d = self._get("playlistItems", {
            "part": "snippet,contentDetails", "playlistId": playlist_id,
            "maxResults": min(n, 50)})
        return d.get("items", [])
