# -*- coding: utf-8 -*-
r"""ytweb.py — thay thế HOÀN TOÀN YouTube Data API, không tốn quota, không cần key.

VÌ SAO (đo thật 2026-10-18): project đã cạn quota 10.000 unit/ngày (HTTP 403
`exceeded your quota`) — `videos.list`/`channels.list` chết là tool không chạy được gì,
dù phần quét web vẫn tốt. Ba thứ tool cần đều lấy được từ web:

  view, tiêu đề, kênh, ngày đăng  → có sẵn trong `videoRenderer` của trang search
  độ dài video                  → `lengthText.simpleText` = "17:01"
  sub của kênh                  → `youtubei/v1/browse` → chuỗi `登録者20万人`
  like / bình luận               → KHÔNG có trên trang search; lấy qua `next` của watch page
                                   (tốn 1 request/video) ⇒ chỉ lấy cho video LỌT lọc cứng

BẪY:
  * Trang `/channel/<id>` và `/channel/<id>/about` KHÔNG chứa số sub trong HTML
    (`人の登録者` = 0 match) — phải gọi `youtubei/v1/browse`, số nằm dạng `登録者20万人`
    (regex `登録者([\\d.,]+[万]?)人`), không phải `subscriberCountText`.
  * `lengthText` có 2 dạng: `simpleText` = "17:01", hoặc chỉ `accessibility.label` =
    "17 分 1 秒". Đọc cả hai, không thì video dài 17 phút bị coi là 0 phút và bị loại.
  * `ownerText.runs[0].navigationEndpoint.browseEndpoint.browseId` = channelId; còn
    `canonicalBaseUrl` = handle (@xxx). Cần browseId cho browse API.
"""
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36",
]
YT = "https://www.youtube.com"
SP_VIEW_WEEK = "CAMSBAgDEAE%3D"
SP_VIEW_MONTH = "CAMSBAgEEAE%3D"


# ------------------------------------------------------------------ primitives
def _num(s):
    """'146,940回視聴' -> 146940 ; '1.2万' -> 12000 ; '20万' -> 200000"""
    if not s:
        return 0
    s = str(s).replace(",", "").replace("，", "").replace(" ", "")
    m = re.search(r"([\d.]+)\s*万", s)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"([\d.]+)", s)
    return int(float(m.group(1))) if m else 0


def dur_seconds(txt):
    """'17:01' -> 1021 ; '1:02:03' -> 3723 ; '17 分 1 秒' -> 1021"""
    if not txt:
        return 0
    t = str(txt).strip()
    m = re.match(r"^(\d+):(\d{2}):(\d{2})$", t)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    m = re.match(r"^(\d+):(\d{2})$", t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    h = re.search(r"(\d+)\s*時間", t)
    mi = re.search(r"(\d+)\s*分", t)
    se = re.search(r"(\d+)\s*秒", t)
    if h or mi or se:
        return (int(h.group(1)) if h else 0) * 3600 + \
               (int(mi.group(1)) if mi else 0) * 60 + \
               (int(se.group(1)) if se else 0)
    return 0


def age_days(txt):
    """'6 日前' -> 6.0 ; '1 時間前' -> 0.04 ; '2 週間前' -> 14 ; '3 か月前' -> 90 ; '2 年前' -> 730"""
    if not txt:
        return 9999.0
    t = str(txt).replace(" ", "")
    m = re.search(r"([\d.]+)", t)
    if not m:
        return 9999.0
    n = float(m.group(1))
    if "秒" in t:
        return n / 86400
    if "分" in t:
        return n / 1440
    if "時間" in t:
        return n / 24
    if "日" in t:
        return n
    if "週間" in t or "週" in t:
        return n * 7
    if "か月" in t or "ヶ月" in t or "カ月" in t:
        return n * 30
    if "年" in t:
        return n * 365
    return 9999.0


def _walk(node, key, out):
    if isinstance(node, dict):
        if key in node:
            out.append(node[key])
        for v in node.values():
            _walk(v, key, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, key, out)


def fetch(url, data=None, timeout=25):
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": random.choice(UA_POOL),
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/json",
        **({"Content-Type": "application/json"} if data else {}),
    })
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def initial_data(html):
    m = re.search(r"ytInitialData\s*=\s*(\{.*?\});", html, re.S)
    return json.loads(m.group(1)) if m else None


def keys_from(html):
    k = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    c = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
    return (k.group(1) if k else None), (c.group(1) if c else "2.20240101.00.00")


# ------------------------------------------------------------------ search
def _paging_token(data):
    """Token phân trang THẬT — đi đúng ĐƯỜNG DẪN, không lấy theo thứ tự.

    Trang 1: `contents/twoColumnSearchResultsRenderer/primaryContents/sectionListRenderer/
    contents[1]/continuationItemRenderer`.
    Trang 2+: response KHÔNG có `contents` mà có `onResponseReceivedCommands[0]/
    appendContinuationItemsAction/continuationItems[1]/continuationItemRenderer`.
    Bỏ dạng thứ hai là phân trang dừng ở trang 2 (đo thật: 40 video thay vì 160).
    5 `continuationCommand` còn lại trong `header/searchHeaderRenderer/chipBar/...` là
    CHIP LỌC — lấy nhầm thì nhận trang trộn sort lung tung mà không báo lỗi.
    """
    def _tok(secs):
        for sec in secs or []:
            ci = sec.get("continuationItemRenderer")
            if ci:
                t = (ci.get("continuationEndpoint", {})
                       .get("continuationCommand", {}).get("token"))
                if t:
                    return t
        return None

    try:
        t = _tok(data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]
                 ["sectionListRenderer"]["contents"])
        if t:
            return t
    except (KeyError, TypeError):
        pass
    try:
        for cmd in data.get("onResponseReceivedCommands") or []:
            t = _tok((cmd.get("appendContinuationItemsAction") or {}).get("continuationItems"))
            if t:
                return t
    except (KeyError, TypeError):
        pass
    return None


def _items(data):
    renderers = []
    _walk(data, "videoRenderer", renderers)
    out, seen = [], set()
    for r in renderers:
        vid = r.get("videoId")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        title = "".join(x.get("text", "") for x in (r.get("title") or {}).get("runs", []))
        ow = (r.get("ownerText") or {}).get("runs", [{}])[0]
        owner = ow.get("text", "")
        be = ((ow.get("navigationEndpoint") or {}).get("browseEndpoint") or {})
        cid = be.get("browseId", "")
        handle = be.get("canonicalBaseUrl", "")
        pub = ((r.get("publishedTimeText") or {}).get("simpleText")
               or (r.get("publishedTimeText") or {}).get("runs", [{}])[0].get("text", ""))
        vt = ((r.get("viewCountText") or {}).get("simpleText")
              or (r.get("viewCountText") or {}).get("runs", [{}])[0].get("text", ""))
        lt = (r.get("lengthText") or {})
        dur = lt.get("simpleText") or ((lt.get("accessibility") or {})
                                       .get("accessibilityData") or {}).get("label", "")
        out.append({
            "video_id": vid, "title": title, "channel": owner, "channel_id": cid,
            "handle": handle,
            "age_days": round(age_days(pub), 2), "age_text": pub,
            "views": _num(vt), "views_text": vt,
            "seconds": dur_seconds(dur), "dur_text": dur,
        })
    return out


def search(query, sp=SP_VIEW_MONTH, pages=12, timeout=25, retries=2):
    """Quét `pages` trang (~20 video/trang). 0 quota, không cần key."""
    url = YT + "/results?" + urllib.parse.urlencode({"search_query": query, "sp": sp})
    last = None
    for attempt in range(1, retries + 1):
        try:
            html = fetch(url, timeout=timeout)
            data = initial_data(html)
            if not data:
                last = "không thấy ytInitialData"
                time.sleep(2 * attempt)
                continue
            api_key, cv = keys_from(html)
            out = _items(data)
            token = _paging_token(data)
            page = 1
            while token and page < pages and api_key:
                body = {"context": {"client": {"clientName": "WEB", "clientVersion": cv,
                                               "hl": "ja", "gl": "JP"}},
                        "continuation": token}
                try:
                    nxt = json.loads(fetch(YT + "/youtubei/v1/search?key=" + api_key,
                                           data=json.dumps(body).encode(), timeout=timeout))
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                        json.JSONDecodeError) as e:
                    last = f"trang {page + 1}: {type(e).__name__} {e}"
                    break
                more = _items(nxt)
                if not more:
                    break
                have = {x["video_id"] for x in out}
                new = [x for x in more if x["video_id"] not in have]
                if not new:
                    break
                out += new
                page += 1
                token = _paging_token(nxt)
                time.sleep(0.1)
            return out
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last = f"{type(e).__name__} {e}"
            time.sleep(2 * attempt)
        except json.JSONDecodeError as e:
            last = f"JSON lỗi: {e}"
            time.sleep(2 * attempt)
    return {"_error": last} if last else []


# ------------------------------------------------------------------ channel sub
def channel_subs(channel_ids, cache, timeout=20, sleep=0.2):
    """{channel_id: subs}. 0 quota, không cần key API.

    THỨ TỰ ĐỌC (đo lại 2026-10-20, đã trả giá thật):
      1. **HTML `/channel/<id>?hl=ja`** — luôn có `チャンネル登録者数 71.1万人`, 1 request,
         nhẹ hơn browse (~1,2–2,4 MB so với ~5,3 MB). Đo 5/5 kênh OK.
      2. `youtubei/v1/browse` chỉ là phương án 2.

    BẪY ĐÃ GÂY LỖI THẬT 2026-10-20: bản trước đọc browse TRƯỚC. Browse bị 403/429 khi gọi
    nhiều ⇒ trả None ⇒ `run_daily` gán sub = 0 để "cho qua cổng <10k" ⇒ **kênh 711.000 sub
    lọt vào báo cáo như kênh 0 sub**. Không bao giờ được đọc browse trước.

      * `/channel/<id>` và `/channel/<id>/about` (bản cũ, KHÔNG `?hl=ja`) không có số sub.
      * `youtubei/v1/browse` (WEB) không có `subscriberCountText`, không có `X人の登録者`.
      * Đừng dùng regex '登録者 + so + 人' trần: khớp dương tính giả với mô tả kênh
        ("2026年はチャンネル登録者20万人を目標に" → ra 200.000 trong khi thật 173.000).
      * Client ANDROID/IOS/WEB_CREATOR/WEB_EMBEDDED_PLAYER đều trả HTTP 400 cho browse
        bằng key WEB; TVHTML5 trả 200 nhưng không có sub. Chỉ WEB dùng được.
    """
    todo = [c for c in dict.fromkeys(channel_ids) if c and c not in cache]
    if not todo:
        return cache
    api_key = cv = None
    for cid in todo:
        # ---- tầng 1: HTML trang kênh (rẻ nhất, ổn định nhất)
        got = None
        try:
            html = fetch(YT + "/channel/" + cid + "?hl=ja", timeout=timeout)
            m = re.search(r"チャンネル登録者数\s*([\d.,]+万?)人", html)
            if m:
                got = _num(m.group(1))
            if not api_key:
                api_key, cv = keys_from(html)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            pass
        if got:
            cache[cid] = got
            time.sleep(sleep)
            continue

        # ---- tầng 2: browse (chỉ khi HTML không có)
        if not api_key:
            try:
                html = fetch(YT + "/channel/" + cid, timeout=timeout)
                api_key, cv = keys_from(html)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                cache[cid] = None
                continue
        if not api_key:
            cache[cid] = None
            continue
        body = {"context": {"client": {"clientName": "WEB", "clientVersion": cv,
                                       "hl": "ja", "gl": "JP"}}, "browseId": cid}
        try:
            raw = fetch(YT + "/youtubei/v1/browse?key=" + api_key,
                        data=json.dumps(body).encode(), timeout=timeout)
            m = (re.search(r"チャンネル登録者数\s*([\d.,]+万?)人", raw)
                 or re.search(r'"subscriberCountText":\{"simpleText":"([^"]+)"', raw))
            cache[cid] = _num(m.group(1)) if m else None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            cache[cid] = None
        time.sleep(sleep)
    return cache


def channel_recent_titles(channel_id, n=30, timeout=25):
    """`n` tiêu đề video mới nhất của kênh, đọc trang `/videos`.

    BẪY 2026-10: trang này KHÔNG còn `richItemRenderer`/`videoRenderer` — video nằm trong
    `lockupViewModel` (`metadata.lockupMetadataViewModel.title.content`). Đi tìm renderer cũ
    ra 0 video mà KHÔNG báo lỗi.
    """
    try:
        html = fetch(YT + "/channel/" + channel_id + "/videos?hl=ja", timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return []
    data = initial_data(html)
    if not data:
        return []
    lks = []
    _walk(data, "lockupViewModel", lks)
    out = []
    for lk in lks:
        md = ((lk.get("metadata") or {}).get("lockupMetadataViewModel") or {})
        t = (md.get("title") or {}).get("content")
        if t:
            out.append(t)
        if len(out) >= n:
            break
    return out



# ------------------------------------------------------------------ likes/comments
def engagement(video_id, timeout=20):
    """like + comment qua trang watch (1 request). Không có cách rẻ hơn.
    Trả {'likes': int|None, 'comments': int|None}. Chỉ gọi cho video LỌT lọc cứng."""
    try:
        html = fetch(YT + "/watch?v=" + video_id, timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return {"likes": None, "comments": None}
    likes = None
    m = re.search(r'"likeCount":"?(\d+)', html) or \
        re.search(r'like this video along with ([\d,]+) other', html) or \
        re.search(r'"accessibilityText":"[^"]*?([\d,]+)\s*(?:人が)?高評価', html)
    if m:
        likes = _num(m.group(1))
    else:
        m = re.search(r'([\d.,]+万?)\s*件の高評価', html)
        if m:
            likes = _num(m.group(1))
    comments = None
    m = re.search(r'"commentCount":\{"simpleText":"([\d,]+)"', html) or \
        re.search(r'([\d,]+)\s*件のコメント', html)
    if m:
        comments = _num(m.group(1))
    return {"likes": likes, "comments": comments}
