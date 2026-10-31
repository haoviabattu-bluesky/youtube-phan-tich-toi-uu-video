# -*- coding: utf-8 -*-
"""websearch.py — quét YouTube qua trang kết quả web, KHÔNG tốn quota API.

VÌ SAO (đo thật 2026-10-18): `search.list` = 100 unit/call **và** có hạn mức RIÊNG
"Search Queries per day" — quét 38 từ khoá là ăn HTTP 429, chết cả ngày. Trang
`youtube.com/results` + endpoint `youtubei/v1/search` trả cùng dữ liệu, **0 unit quota**.

PHÂN TRANG (bắt buộc — không phân trang chỉ được 20 video/từ khoá):
  Mỗi trang continuation trả thêm ~20 video. Tool lấy `pages` trang/từ khoá
  (mặc định 8 → ~160 video/từ khoá), nên 80 từ khoá ≈ 12.000 video thô.

BẪY ĐÃ TRẢ GIÁ:
  1. Trang kết quả có **6 `continuationCommand`**: 1 cái là phân trang thật (nằm ở
     `primaryContents/sectionListRenderer/contents[1]/continuationItemRenderer`), 5 cái
     còn lại là **chip lọc** (chipBar/chipCloudRenderer/chips[N]). Lấy sai token ⇒ nhận
     trang trộn sort lung tung (view 89, 582, 233…) mà KHÔNG báo lỗi — tưởng đã lấy đúng.
     Luôn chọn token theo ĐƯỜNG DẪN, không theo thứ tự.
  2. `ytInitialData` phải bóc bằng `re.search(r"ytInitialData\\s*=\\s*(\\{.*?\\});", html, re.S)`.
     Thiếu `re.S` là không khớp → tưởng "YouTube chặn".
  3. Không regex `"videoId":"..."` trên cả trang: nó bắt cả id trong
     `ytInitialPlayerResponse` và shelf khác, ra id rác. Phải đi bộ cây JSON tìm
     đúng key `videoRenderer`.
  4. `sp` phải URL-encode (`CAMSBAgDEAE%3D`). Để nguyên `=` thì YouTube bỏ filter, trả
     sort relevance — vẫn "có video" nên rất dễ tưởng đang lọc đúng.
  5. `publishedTimeText` tiếng Nhật: 秒/分/時間/日/週間/か月/年 — thiếu đơn vị nào thì video
     tuổi đó lọt qua lọc "≤5 ngày".
  6. Phân trang KHÔNG được lặp vô hạn: hết token hoặc trang không có video mới thì dừng.
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
SP_VIEW_WEEK = "CAMSBAgDEAE%3D"      # sort view count + this week + type video
SP_VIEW_MONTH = "CAMSBAgEEAE%3D"     # sort view count + this month + type video
YT = "https://www.youtube.com"


def _num(s):
    """'146,940回視聴' -> 146940 ; '1.2万回視聴' -> 12000 ; '視聴回数なし' -> 0"""
    if not s:
        return 0
    s = s.replace(",", "").replace("，", "")
    m = re.search(r"([\d.]+)\s*万", s)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"([\d.]+)", s)
    return int(float(m.group(1))) if m else 0


def age_days(txt):
    """'6 日前' -> 6.0 ; '1 時間前' -> 0.04 ; '2 週間前' -> 14 ; '3 か月前' -> 90 ; '2 年前' -> 730"""
    if not txt:
        return 9999.0
    t = txt.replace(" ", "")
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


def _paging_token(data):
    """Token phân trang THẬT — phải đi đúng ĐƯỜNG DẪN, không lấy theo thứ tự.

    Trang 1: `contents/twoColumnSearchResultsRenderer/primaryContents/sectionListRenderer/
    contents[1]/continuationItemRenderer`.
    Trang 2+: response KHÔNG có `contents` mà có `onResponseReceivedCommands[0]/
    appendContinuationItemsAction/continuationItems[1]/continuationItemRenderer`.
    Bỏ dạng thứ hai là phân trang dừng ở trang 2 (đo thật: 40 video thay vì 160).
    5 `continuationCommand` còn lại trong `header/searchHeaderRenderer/chipBar/...` là
    CHIP LỌC — lấy nhầm thì nhận trang trộn sort lung tung mà không báo lỗi.
    """
    def _tok_from_section_list(secs):
        for sec in secs or []:
            ci = sec.get("continuationItemRenderer")
            if ci:
                t = (ci.get("continuationEndpoint", {})
                       .get("continuationCommand", {}).get("token"))
                if t:
                    return t
        return None

    try:
        secs = (data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]
                ["sectionListRenderer"]["contents"])
        t = _tok_from_section_list(secs)
        if t:
            return t
    except (KeyError, TypeError):
        pass

    try:
        for cmd in data.get("onResponseReceivedCommands") or []:
            items = ((cmd.get("appendContinuationItemsAction") or {})
                     .get("continuationItems"))
            t = _tok_from_section_list(items)
            if t:
                return t
    except (KeyError, TypeError):
        pass
    return None


def _items(data):
    """videoRenderer -> dict chuẩn hoá."""
    renderers = []
    _walk(data, "videoRenderer", renderers)
    out, seen = [], set()
    for r in renderers:
        vid = r.get("videoId")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        title = "".join(x.get("text", "") for x in (r.get("title") or {}).get("runs", []))
        owner = "".join(x.get("text", "") for x in (r.get("ownerText") or {}).get("runs", []))
        pub = ((r.get("publishedTimeText") or {}).get("simpleText")
               or (r.get("publishedTimeText") or {}).get("runs", [{}])[0].get("text", ""))
        vt = ((r.get("viewCountText") or {}).get("simpleText")
              or (r.get("viewCountText") or {}).get("runs", [{}])[0].get("text", ""))
        out.append({
            "video_id": vid, "title": title, "channel": owner,
            "age_days": round(age_days(pub), 2), "age_text": pub,
            "views": _num(vt), "views_text": vt,
        })
    return out


def _fetch(url, data=None, timeout=25):
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": random.choice(UA_POOL),
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/json",
        **({"Content-Type": "application/json"} if data else {}),
    })
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def search_web(query, sp=SP_VIEW_WEEK, pages=8, timeout=25, retries=2, stop_after_age=None):
    """Quét `pages` trang kết quả (mỗi trang ~20 video). 0 unit quota.

    pages=1 → ~20 video (hành vi cũ). pages=8 → ~160 video/từ khoá.
    stop_after_age: trang nào có TOÀN BỘ video cũ hơn mốc này (ngày) thì dừng sớm.
    """
    url = YT + "/results?" + urllib.parse.urlencode({"search_query": query, "sp": sp})
    last = None
    for attempt in range(1, retries + 1):
        try:
            html = _fetch(url, timeout=timeout)
            m = re.search(r"ytInitialData\s*=\s*(\{.*?\});", html, re.S)
            if not m:
                last = "không thấy ytInitialData"
                time.sleep(2 * attempt)
                continue
            data = json.loads(m.group(1))
            api_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
            cv = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
            if not api_key:
                last = "không thấy INNERTUBE_API_KEY"
                continue
            api_key = api_key.group(1)
            cv = cv.group(1) if cv else "2.20240101.00.00"

            out = _items(data)
            token = _paging_token(data)
            page = 1
            while token and page < pages:
                body = {"context": {"client": {
                    "clientName": "WEB", "clientVersion": cv, "hl": "ja", "gl": "JP"}},
                    "continuation": token}
                try:
                    raw = _fetch(YT + "/youtubei/v1/search?key=" + api_key,
                                 data=json.dumps(body).encode(), timeout=timeout)
                    nxt = json.loads(raw)
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
                if stop_after_age is not None and all(x["age_days"] > stop_after_age
                                                      for x in more):
                    break
                time.sleep(0.15)
            return out
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last = f"{type(e).__name__} {e}"
            time.sleep(2 * attempt)
        except json.JSONDecodeError as e:
            last = f"JSON lỗi: {e}"
            time.sleep(2 * attempt)
    return {"_error": last} if last else []
