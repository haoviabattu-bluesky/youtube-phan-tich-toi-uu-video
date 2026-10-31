# -*- coding: utf-8 -*-
"""enrich.py — làm GIÀU dữ liệu bằng YouTube Data API v3, web chỉ là DỰ PHÒNG.

VÌ SAO CẦN (đo thật 2026-10-20): bản web-only để lại 3 lỗi thật trong báo cáo 03:00:
  1. `channel_subs` đọc browse trước → 403 khi gọi nhiều → sub=None → run_daily gán 0
     ⇒ **kênh 711.000 sub lọt vào báo cáo như kênh 0 sub**.
  2. Trang search chỉ cho "5 日前" (làm tròn) ⇒ tuổi video sai tới gần 1 ngày; video 5,8
     ngày lọt qua luật "≤5 ngày".
  3. like/comment/duration không có trên trang search.

API v3 trả ĐÚNG cả ba thứ trên, và RẺ: `videos.list` = 1 unit/50 id, `channels.list` =
1 unit/50 kênh, `playlistItems.list` = 1 unit/kênh. Quét 824 video + 800 kênh ≈ 33 unit
(trần 10.000/ngày). `search.list` (100 unit/call) KHÔNG dùng — đó là thứ từng làm cạn quota.

Nếu API chết (403 quotaExceeded / 429 / mất mạng) thì `available()` trả False và run_daily
quay về đường web cũ — nhưng đường web cũng đã được sửa: đọc HTML trang kênh TRƯỚC browse,
và kênh không xác minh được sub thì LOẠI HẲN chứ không đoán 0.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ytapi  # noqa: E402

# Ngưỡng dừng gọi API: nếu 1 call đầu đã 403 quotaExceeded thì đừng cố thêm 30 call nữa.
_API = {"ok": None, "units": 0, "error": ""}


def _client():
    if "_yt" not in _API:
        _API["_yt"] = ytapi.YT()
    return _API["_yt"]


def available():
    """API còn dùng được không. Gọi 1 lần rồi cache."""
    if _API["ok"] is not None:
        return _API["ok"]
    try:
        yt = _client()
        d = yt._get("videos", {"part": "id", "id": "dQw4w9WgXcQ"})
        if d.get("_error"):
            _API["ok"] = False
            _API["error"] = str(d["_error"])[:200]
        else:
            _API["ok"] = True
    except ytapi.QuotaExceeded as e:
        _API["ok"] = False
        _API["error"] = f"quotaExceeded: {str(e)[:160]}"
    except BaseException as e:                                # noqa: BLE001
        _API["ok"] = False
        _API["error"] = f"{type(e).__name__}: {str(e)[:160]}"
    return _API["ok"]


def status():
    return {"ok": _API["ok"], "units": _API["units"], "error": _API["error"]}


def videos(video_ids):
    """{video_id: item videos.list}. Rỗng nếu API chết."""
    if not available():
        return {}
    yt = _client()
    before = yt.units
    items = yt.videos(list(video_ids))
    _API["units"] += yt.units - before
    return {it["id"]: it for it in items}


def channels(channel_ids):
    """{channel_id: item channels.list}. Rỗng nếu API chết."""
    if not available():
        return {}
    yt = _client()
    before = yt.units
    items = yt.channels(list(channel_ids))
    _API["units"] += yt.units - before
    return {it["id"]: it for it in items}


def manga_ratio(channel_item, n=20):
    """Tỉ lệ tiêu đề manga trong `n` video mới nhất, qua playlistItems (1 unit).

    Trả None nếu không đọc được (kênh ẩn playlist / API chết) — KHÔNG đoán.
    """
    if not channel_item:
        return None
    ups = (((channel_item.get("contentDetails") or {}).get("relatedPlaylists") or {})
           .get("uploads"))
    if not ups or not available():
        return None
    yt = _client()
    before = yt.units
    titles = yt.uploads_sample(channel_item["id"], ups, n)
    _API["units"] += yt.units - before
    if not titles:
        return None
    import re
    from lanes import MANGA_ANY
    return sum(1 for t in titles if re.search(MANGA_ANY, t, re.I)) / len(titles)
