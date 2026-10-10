"""yt_api.py — YouTube Data API v3 bằng API key (đọc công khai). Đếm quota. KHÔNG có insert ở đây (xem sender.py, Phase 2b).

Bẫy đã đo 2026-10-05: `commentThreads.list?allThreadsRelatedToChannelId=` trả 403 commentsDisabled nếu BẤT KỲ video nào của kênh tắt
comment / kênh bị đình chỉ → đi theo từng video (`videoId=`) cho chắc, 1 unit/100 thread.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.googleapis.com/youtube/v3/"


class YTError(RuntimeError):
    def __init__(self, kind, msg):
        super().__init__(f"{kind}: {msg}")
        self.kind = kind


class YT:
    def __init__(self, key, cost: dict, sleep=0.25):
        self.key, self.cost, self.sleep = key, cost, sleep
        self.quota_used = 0

    def _call(self, ep, **p):
        p["key"] = self.key
        url = BASE + ep + "?" + urllib.parse.urlencode(p)
        self.quota_used += self.cost.get(ep, 1)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=45) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                if "commentsDisabled" in body:
                    raise YTError("commentsDisabled", ep)
                if "quotaExceeded" in body or "dailyLimitExceeded" in body:
                    raise YTError("quotaExceeded", body[:200])
                if e.code == 404 or "videoNotFound" in body or "could not be found" in body:
                    raise YTError("notFound", ep)
                if e.code in (401, 403):
                    raise YTError("forbidden", body[:200])
                if attempt == 2:
                    raise YTError("http", f"{e.code} {body[:200]}")
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == 2:
                    raise YTError("network", str(e))
            time.sleep(2 * (attempt + 1))

    # ------------------------------------------------------------ channel / videos
    def channel(self, channel_id):
        d = self._call("channels", part="snippet,statistics,contentDetails", id=channel_id)
        items = d.get("items") or []
        if not items:
            raise YTError("channelNotFound", f"{channel_id} — API trả 0 kết quả (kênh ẩn/đình chỉ/sai id)")
        return items[0]

    def uploads(self, channel_id, max_videos=50):
        ch = self.channel(channel_id)
        pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        ids, tok = [], None
        while len(ids) < max_videos:
            p = dict(part="contentDetails", playlistId=pl, maxResults=50)
            if tok:
                p["pageToken"] = tok
            d = self._call("playlistItems", **p)
            ids += [i["contentDetails"]["videoId"] for i in d.get("items", [])]
            tok = d.get("nextPageToken")
            if not tok:
                break
        return ch, ids[:max_videos]

    def videos(self, ids):
        out = []
        for i in range(0, len(ids), 50):
            d = self._call("videos", part="snippet,statistics", id=",".join(ids[i:i + 50]))
            for it in d.get("items", []):
                s, st = it["snippet"], it.get("statistics", {})
                out.append({"video_id": it["id"], "title": s.get("title", ""), "description": s.get("description", ""),
                            "published_at": s.get("publishedAt"), "comment_count": int(st.get("commentCount", 0) or 0)})
        return out

    # ------------------------------------------------------------ comments
    @staticmethod
    def _norm(sn, cid, video_id, channel_id, parent_id=None, extra=None):
        a = (sn.get("authorChannelId") or {}).get("value")
        c = {"comment_id": cid, "parent_id": parent_id, "video_id": video_id, "channel_id": channel_id,
             "author_channel_id": a, "author_display": sn.get("authorDisplayName", ""), "text": sn.get("textOriginal") or sn.get("textDisplay", ""),
             "like_count": int(sn.get("likeCount", 0) or 0), "published_at": sn.get("publishedAt"), "updated_at": sn.get("updatedAt"),
             "is_owner": a == channel_id, "can_reply": True, "total_reply_count": 0, "raw": sn}
        if extra:
            c.update(extra)
        return c

    def threads(self, video_id, channel_id, max_threads=200):
        """Trả list (top_comment, [replies]) mới nhất trước. Replies kèm theo chỉ tối đa 5/thread (API); thread dài → gọi replies()."""
        out, tok = [], None
        while len(out) < max_threads:
            p = dict(part="snippet,replies", videoId=video_id, order="time", maxResults=100, textFormat="plainText")
            if tok:
                p["pageToken"] = tok
            d = self._call("commentThreads", **p)
            for it in d.get("items", []):
                sn = it["snippet"]
                top = self._norm(sn["topLevelComment"]["snippet"], it["id"], video_id, channel_id,
                                 extra={"can_reply": bool(sn.get("canReply", True)), "total_reply_count": int(sn.get("totalReplyCount", 0))})
                reps = [self._norm(r["snippet"], r["id"], video_id, channel_id, parent_id=it["id"])
                        for r in (it.get("replies") or {}).get("comments", [])]
                if top["total_reply_count"] > len(reps):
                    reps = self.replies(it["id"], video_id, channel_id)
                out.append((top, reps))
            tok = d.get("nextPageToken")
            if not tok:
                break
            time.sleep(self.sleep)
        return out[:max_threads]

    def replies(self, parent_id, video_id, channel_id):
        out, tok = [], None
        while True:
            p = dict(part="snippet", parentId=parent_id, maxResults=100, textFormat="plainText")
            if tok:
                p["pageToken"] = tok
            d = self._call("comments", **p)
            out += [self._norm(r["snippet"], r["id"], video_id, channel_id, parent_id=parent_id) for r in d.get("items", [])]
            tok = d.get("nextPageToken")
            if not tok:
                return out
