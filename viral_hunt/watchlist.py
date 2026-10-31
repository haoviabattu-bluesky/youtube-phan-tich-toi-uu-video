# -*- coding: utf-8 -*-
"""watchlist.py — danh sách KÊNH NGUỒN theo dõi, thay cho việc quét search mỗi ngày.

Vì sao (đo thật 2026-10-18): `search.list` = 100 unit/call và có hạn mức RIÊNG
("Search Queries per day") — quét 38 từ khoá là bấm nút tự huỷ, đã ăn HTTP 429 lúc 12:00.
Ngược lại `playlistItems.list` + `videos.list` = 1 unit/call và KHÔNG bị hạn mức search.

Cơ chế:
  * Mỗi kênh trong watchlist: đọc 50 video mới nhất của playlist uploads (1 unit)
    → lọc ≤5 ngày, view, sub → chấm điểm như cũ.
  * Kênh nào có video lọt qua lọc cứng (manga, <10k sub, đủ view) thì TỰ ĐỘNG vào watchlist
    vĩnh viễn ⇒ càng chạy càng nhiều nguồn, không phụ thuộc search.
  * Search chỉ dùng để MỞ RỘNG, ngân sách riêng (`--search-budget`, mặc định 6 call/ngày),
    từ khoá xoay vòng theo ngày nên mỗi ngày mở rộng một góc khác.
"""
import datetime
import os
import re
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "state", "viral_hunt.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    channel_id   TEXT PRIMARY KEY,
    title        TEXT,
    handle       TEXT,
    subs         INTEGER,
    lane         TEXT,
    manga_ratio  REAL,
    added_ts     INTEGER NOT NULL,
    added_by     TEXT,
    last_checked INTEGER,
    hit_count    INTEGER DEFAULT 0,
    miss_count   INTEGER DEFAULT 0,
    active       INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS kw_cursor (
    lane  TEXT PRIMARY KEY,
    pos   INTEGER DEFAULT 0,
    day   TEXT
);
"""


def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.executescript(SCHEMA)
    c.row_factory = sqlite3.Row
    return c


def upsert(conn, channel_id, title, subs, lane, manga_ratio, added_by, handle=""):
    cur = conn.execute("SELECT channel_id FROM channels WHERE channel_id=?", (channel_id,))
    if cur.fetchone():
        conn.execute("UPDATE channels SET subs=?, manga_ratio=MAX(COALESCE(manga_ratio,0),?),"
                     " lane=CASE WHEN lane IS NULL OR lane='' THEN ? ELSE lane END WHERE channel_id=?",
                     (subs, manga_ratio, lane, channel_id))
    else:
        conn.execute("INSERT INTO channels(channel_id,title,handle,subs,lane,manga_ratio,"
                     "added_ts,added_by) VALUES (?,?,?,?,?,?,?,?)",
                     (channel_id, title, handle, subs, lane, manga_ratio, int(time.time()), added_by))
    conn.commit()


def active(conn, lane=None):
    q = "SELECT * FROM channels WHERE active=1"
    args = []
    if lane:
        q += " AND (lane=? OR lane IS NULL OR lane='')"
        args.append(lane)
    return [dict(r) for r in conn.execute(q, args).fetchall()]


def touch(conn, channel_id, hit):
    if hit:
        conn.execute("UPDATE channels SET last_checked=?, hit_count=hit_count+1, miss_count=0 "
                     "WHERE channel_id=?", (int(time.time()), channel_id))
    else:
        conn.execute("UPDATE channels SET last_checked=?, miss_count=miss_count+1 "
                     "WHERE channel_id=?", (int(time.time()), channel_id))
        # kênh chết 45 ngày liền không ra video nào → tắt, đỡ tốn unit
        conn.execute("UPDATE channels SET active=0 WHERE channel_id=? AND miss_count>=45",
                     (channel_id,))
    conn.commit()


def stats(conn):
    r = conn.execute("SELECT COUNT(*) c, SUM(active) a FROM channels").fetchone()
    return {"channels": r["c"] or 0, "active": r["a"] or 0}


# ------------------------------------------------------------------ keyword cursor
def next_keywords(conn, lane, keywords, n, day):
    """Lấy n từ khoá kế tiếp của lane, xoay vòng qua các ngày (cursor lưu trong DB)."""
    if not keywords or n <= 0:
        return []
    row = conn.execute("SELECT pos FROM kw_cursor WHERE lane=?", (lane,)).fetchone()
    pos = row["pos"] if row else 0
    out = [keywords[(pos + i) % len(keywords)] for i in range(min(n, len(keywords)))]
    conn.execute("INSERT OR REPLACE INTO kw_cursor(lane,pos,day) VALUES (?,?,?)",
                 (lane, (pos + n) % len(keywords), day))
    conn.commit()
    return out


# ------------------------------------------------------------------ seed
def seed_from_sheet(conn, yt, tabs, log=print):
    """Nạp watchlist từ cột 'VIDEO GỐC' (cột T) của sheet: video mẫu anh đã chọn cho từng lane.
    videos.list 1 unit cho 50 id, channels.list 1 unit cho 50 id."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        log("  ! thiếu google-api-python-client — bỏ qua seed từ sheet")
        return 0
    SID = "1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU"
    CREDS = r"D:\CLAUDE\credentials\google-sheets-key.json"
    if not os.path.exists(CREDS):
        log(f"  ! không thấy {CREDS} — bỏ qua seed từ sheet")
        return 0
    creds = Credentials.from_service_account_file(
        CREDS, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    ranges = [f"'{t}'!T2:T200" for t in tabs]
    res = svc.spreadsheets().values().batchGet(spreadsheetId=SID, ranges=ranges).execute()
    # tab -> mã lane 1 ký tự (L-shakai-no-naze -> L, Lane-N -> N, M-teinengo-anaba -> M)
    lane_of_tab = {}
    for tab in tabs:
        if tab.startswith("Lane-"):
            lane_of_tab[tab] = tab.split("-", 1)[1].strip()[:1].upper()
        elif tab.startswith("L-"):
            lane_of_tab[tab] = "L"
        else:
            lane_of_tab[tab] = tab.split("-")[0].strip()[:1].upper()
    per_lane = {}
    for tab, vr in zip(tabs, res.get("valueRanges", [])):
        lane = lane_of_tab.get(tab, "")
        ids = []
        for r in vr.get("values", []):
            for m in re.finditer(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})",
                                 (r[0] if r else "") or ""):
                ids.append(m.group(1))
        per_lane[tab] = (lane, list(dict.fromkeys(ids)))
    all_ids = [i for _, (_, ids) in per_lane.items() for i in ids]
    if not all_ids:
        log("  ! cột VIDEO GỐC trống — không seed được")
        return 0
    vids = yt.videos(all_ids)
    ch_ids = list({(v.get("snippet") or {}).get("channelId") for v in vids} - {None})
    chans = {c["id"]: c for c in yt.channels(ch_ids)}
    lane_of_ch = {}
    for tab, (lane, ids) in per_lane.items():
        for v in vids:
            if v["id"] in ids:
                lane_of_ch[(v.get("snippet") or {}).get("channelId")] = lane
    n = 0
    for cid, c in chans.items():
        st = c.get("statistics") or {}
        subs = int(st.get("subscriberCount") or 0)
        ups = ((c.get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
        ratio = 0.0
        if ups:
            titles = yt.uploads_sample(cid, ups, 20)
            if titles:
                from lanes import MANGA_ANY
                ratio = sum(1 for t in titles if re.search(MANGA_ANY, t, re.I)) / len(titles)
        upsert(conn, cid, (c.get("snippet") or {}).get("title", ""), subs,
               lane_of_ch.get(cid, ""), ratio, "sheet_video_goc",
               (c.get("snippet") or {}).get("customUrl", ""))
        n += 1
    log(f"  seed từ sheet: {len(all_ids)} video mẫu → {n} kênh vào watchlist")
    return n
