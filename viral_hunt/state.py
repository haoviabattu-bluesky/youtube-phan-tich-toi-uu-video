# -*- coding: utf-8 -*-
"""state.py — chống báo cáo lặp. SQLite 1 file, không cần service.

Luật (anh chốt 2026-10-18): video nào đã báo cáo rồi thì KHÔNG báo cáo lại.
  reported    — video_id đã từng xuất hiện trong 1 báo cáo ngày (giữ mãi).
  seen        — video_id đã quét thấy nhưng chưa được chọn (để đếm "đã xét N video").
  runs        — log mỗi lần chạy: ngày, số ứng viên, số báo cáo, unit quota, lỗi.
"""
import json
import os
import sqlite3
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "state", "viral_hunt.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS reported (
    video_id TEXT PRIMARY KEY,
    lane     TEXT NOT NULL,
    day      TEXT NOT NULL,
    title    TEXT,
    channel  TEXT,
    views    INTEGER,
    subs     INTEGER,
    score    REAL,
    grade    TEXT,
    ts       INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS seen (
    video_id TEXT PRIMARY KEY,
    lane     TEXT,
    first_ts INTEGER NOT NULL,
    title    TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    day      TEXT NOT NULL,
    ts       INTEGER NOT NULL,
    ok       INTEGER,
    candidates INTEGER,
    reported INTEGER,
    units    INTEGER,
    note     TEXT
);
"""


def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.executescript(SCHEMA)
    c.row_factory = sqlite3.Row
    return c


def already_reported(conn, video_ids):
    if not video_ids:
        return set()
    q = ",".join("?" * len(video_ids))
    rows = conn.execute(f"SELECT video_id FROM reported WHERE video_id IN ({q})",
                        list(video_ids)).fetchall()
    return {r["video_id"] for r in rows}


def mark_reported(conn, items):
    now = int(time.time())
    for it in items:
        conn.execute(
            "INSERT OR REPLACE INTO reported"
            "(video_id,lane,day,title,channel,views,subs,score,grade,ts)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (it["video_id"], it["lane"], it["day"], it.get("title"), it.get("channel"),
             it.get("views"), it.get("subs"), it.get("score"), it.get("grade"), now))
    conn.commit()


def mark_seen(conn, rows):
    now = int(time.time())
    for vid, lane, title in rows:
        conn.execute("INSERT OR IGNORE INTO seen(video_id,lane,first_ts,title) VALUES (?,?,?,?)",
                     (vid, lane, now, title))
    conn.commit()


def log_run(conn, day, ok, candidates, reported, units, note=""):
    conn.execute("INSERT INTO runs(day,ts,ok,candidates,reported,units,note) VALUES (?,?,?,?,?,?,?)",
                 (day, int(time.time()), 1 if ok else 0, candidates, reported, units, note))
    conn.commit()


def recent_days(conn, n=14):
    return [dict(r) for r in conn.execute(
        "SELECT day, COUNT(*) AS n, SUM(views) AS views FROM reported"
        " GROUP BY day ORDER BY day DESC LIMIT ?", (n,)).fetchall()]


def stats(conn):
    r = conn.execute("SELECT COUNT(*) c FROM reported").fetchone()
    s = conn.execute("SELECT COUNT(*) c FROM seen").fetchone()
    return {"reported_total": r["c"], "seen_total": s["c"]}
