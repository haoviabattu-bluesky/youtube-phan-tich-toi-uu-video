"""store.py — SQLite state (spec mục O). Mọi bảng có channel_id để không trộn kênh; idempotency_key = channel_id:comment_id."""
import json
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels(channel_id TEXT PRIMARY KEY, lane TEXT, channel_name TEXT, handle TEXT, sheet_tab TEXT,
  mode TEXT, footer_policy TEXT, watermark_updated_at TEXT, identity_verified_at TEXT, last_run_id INTEGER);
CREATE TABLE IF NOT EXISTS videos(video_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL, title TEXT, description_head TEXT,
  published_at TEXT, comment_count INTEGER, ep_dir TEXT, context_level TEXT, context_json TEXT, context_cached_at TEXT);
CREATE TABLE IF NOT EXISTS comments(comment_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL, video_id TEXT NOT NULL, parent_id TEXT,
  author_channel_id TEXT, author_display TEXT, text TEXT, like_count INTEGER, published_at TEXT, updated_at TEXT,
  is_owner INTEGER DEFAULT 0, is_reply INTEGER DEFAULT 0, can_reply INTEGER DEFAULT 1, total_reply_count INTEGER DEFAULT 0,
  discovered_at TEXT, deleted_at TEXT, raw_json TEXT);
CREATE INDEX IF NOT EXISTS ix_comments_parent ON comments(parent_id);
CREATE INDEX IF NOT EXISTS ix_comments_video ON comments(channel_id, video_id);
CREATE TABLE IF NOT EXISTS classifications(id INTEGER PRIMARY KEY, comment_id TEXT NOT NULL, run_id INTEGER, primary_cat TEXT,
  secondary_cats TEXT, flags_json TEXT, summary_ja TEXT, key_detail_ja TEXT, viewer_intent TEXT, classification_conf REAL,
  understanding_conf REAL, model TEXT, provider TEXT, prompt_version TEXT, notes TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, comment_id TEXT NOT NULL, channel_id TEXT NOT NULL, run_id INTEGER,
  decision TEXT, risk TEXT, generator_kind TEXT, footer_rule TEXT, policy_version TEXT, reason TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS drafts(id INTEGER PRIMARY KEY, comment_id TEXT NOT NULL, channel_id TEXT NOT NULL, video_id TEXT, run_id INTEGER,
  attempt_no INTEGER, text_body TEXT, footer_text TEXT, final_text TEXT, model TEXT, provider TEXT, prompt_version TEXT,
  rule_qc_json TEXT, judge_json TEXT, judge_model TEXT, reply_conf REAL, status TEXT, gate TEXT, template_combo TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS replies(id INTEGER PRIMARY KEY, channel_id TEXT NOT NULL, comment_id TEXT NOT NULL, draft_id INTEGER,
  idempotency_key TEXT UNIQUE, final_text TEXT, status TEXT, youtube_reply_id TEXT, sent_at TEXT, api_response_json TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS runs(run_id INTEGER PRIMARY KEY, started_at TEXT, finished_at TEXT, mode TEXT, channels_json TEXT,
  counts_json TEXT, quota_used INTEGER DEFAULT 0, policy_version TEXT, prompt_version TEXT);
CREATE TABLE IF NOT EXISTS errors(id INTEGER PRIMARY KEY, run_id INTEGER, channel_id TEXT, comment_id TEXT, stage TEXT, error_type TEXT,
  message TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS llm_calls(id INTEGER PRIMARY KEY, run_id INTEGER, comment_id TEXT, stage TEXT, provider TEXT, model TEXT,
  tokens_in INTEGER, tokens_out INTEGER, elapsed_s REAL, ok INTEGER, created_at TEXT);
CREATE TABLE IF NOT EXISTS review_queue(draft_id INTEGER PRIMARY KEY, queued_at TEXT, decided_at TEXT, decision TEXT, edited_text TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS reactions(comment_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL, like_status TEXT, heart_status TEXT, at TEXT);
"""


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        # cột thêm sau (bản dịch tiếng Việt để anh chấm) — ALTER an toàn với DB cũ
        for sql in ("ALTER TABLE comments ADD COLUMN text_vi TEXT", "ALTER TABLE drafts ADD COLUMN reply_vi TEXT",
                    "ALTER TABLE drafts ADD COLUMN judge_vi TEXT"):
            try:
                self.db.execute(sql)
            except sqlite3.OperationalError:
                pass
        self.db.commit()

    def set_comment_vi(self, comment_id, vi):
        self.x("UPDATE comments SET text_vi=? WHERE comment_id=?", vi, comment_id)

    def set_draft_vi(self, draft_id, reply_vi, judge_vi):
        self.x("UPDATE drafts SET reply_vi=?,judge_vi=? WHERE id=?", reply_vi, judge_vi, draft_id)

    # ---------------------------------------------------------------- helpers
    def q(self, sql, *a):
        return [dict(r) for r in self.db.execute(sql, a).fetchall()]

    def one(self, sql, *a):
        r = self.db.execute(sql, a).fetchone()
        return dict(r) if r else None

    def x(self, sql, *a):
        cur = self.db.execute(sql, a)
        self.db.commit()
        return cur.lastrowid

    # ---------------------------------------------------------------- channels / videos
    def upsert_channel(self, c, run_id):
        self.x("INSERT INTO channels(channel_id,lane,channel_name,handle,sheet_tab,mode,footer_policy,last_run_id) VALUES(?,?,?,?,?,?,?,?) "
               "ON CONFLICT(channel_id) DO UPDATE SET lane=excluded.lane,channel_name=excluded.channel_name,handle=excluded.handle,"
               "sheet_tab=excluded.sheet_tab,mode=excluded.mode,footer_policy=excluded.footer_policy,last_run_id=excluded.last_run_id",
               c.channel_id, c.lane, c.channel_name, c.handle, c.sheet_tab, c.mode, c.footer_policy, run_id)

    def upsert_video(self, video_id, channel_id, title, description_head, published_at, comment_count):
        self.x("INSERT INTO videos(video_id,channel_id,title,description_head,published_at,comment_count) VALUES(?,?,?,?,?,?) "
               "ON CONFLICT(video_id) DO UPDATE SET title=excluded.title,description_head=excluded.description_head,"
               "published_at=excluded.published_at,comment_count=excluded.comment_count",
               video_id, channel_id, title, description_head, published_at, comment_count)

    def set_video_context(self, video_id, ep_dir, level, context_json):
        self.x("UPDATE videos SET ep_dir=?,context_level=?,context_json=?,context_cached_at=? WHERE video_id=?",
               ep_dir, level, context_json, now(), video_id)

    def get_video(self, video_id):
        return self.one("SELECT * FROM videos WHERE video_id=?", video_id)

    # ---------------------------------------------------------------- comments
    def upsert_comment(self, c: dict):
        self.x("INSERT INTO comments(comment_id,channel_id,video_id,parent_id,author_channel_id,author_display,text,like_count,"
               "published_at,updated_at,is_owner,is_reply,can_reply,total_reply_count,discovered_at,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
               "ON CONFLICT(comment_id) DO UPDATE SET text=excluded.text,like_count=excluded.like_count,updated_at=excluded.updated_at,"
               "can_reply=excluded.can_reply,total_reply_count=excluded.total_reply_count,raw_json=excluded.raw_json",
               c["comment_id"], c["channel_id"], c["video_id"], c.get("parent_id"), c.get("author_channel_id"), c.get("author_display"),
               c.get("text"), c.get("like_count", 0), c.get("published_at"), c.get("updated_at"), int(c.get("is_owner", False)),
               int(bool(c.get("parent_id"))), int(c.get("can_reply", True)), c.get("total_reply_count", 0), now(),
               json.dumps(c.get("raw", {}), ensure_ascii=False))

    def thread(self, thread_id):
        """Top-level + mọi reply, theo thời gian."""
        top = self.one("SELECT * FROM comments WHERE comment_id=?", thread_id)
        reps = self.q("SELECT * FROM comments WHERE parent_id=? ORDER BY published_at", thread_id)
        return top, reps

    # Một comment coi là "đã xử lý xong" khi: có decision khác REPLY, HOẶC đã có draft dùng được/đã chấm.
    # Decision REPLY mà chưa có draft (vd run fetch_only trước đó) → vẫn pending để run draft_only soạn tiếp.
    _DONE = """(EXISTS(SELECT 1 FROM decisions d WHERE d.comment_id={a}.comment_id AND d.decision<>'REPLY')
                OR EXISTS(SELECT 1 FROM drafts f WHERE f.comment_id={a}.comment_id AND f.status IN('GENERATED','APPROVED','EDITED','SENT','REJECTED','SKIPPED')))"""

    def pending_comments(self, channel_id, limit=50, only_video=None):
        """Ứng viên cần xử lý (spec mục E): top-level chưa có owner reply · follow-up của viewer sau owner reply ·
        viewer trả lời câu hỏi ghim của chính kênh (owner top-level) mà kênh chưa đáp lại."""
        vid = " AND c.video_id=? " if only_video else ""
        args = [channel_id] + ([only_video] if only_video else [])
        top = self.q(f"""SELECT c.*, 'top' AS kind FROM comments c WHERE c.channel_id=? {vid} AND c.parent_id IS NULL AND c.is_owner=0
            AND c.deleted_at IS NULL
            AND NOT EXISTS(SELECT 1 FROM comments r WHERE r.parent_id=c.comment_id AND r.is_owner=1)
            AND NOT {self._DONE.format(a='c')} ORDER BY c.published_at DESC""", *args)
        fol = self.q(f"""SELECT c.*, 'follow_up' AS kind FROM comments c JOIN comments t ON t.comment_id=c.parent_id
            WHERE c.channel_id=? {vid} AND c.is_owner=0 AND c.deleted_at IS NULL AND t.is_owner=0
            AND EXISTS(SELECT 1 FROM comments o WHERE o.parent_id=c.parent_id AND o.is_owner=1 AND o.published_at < c.published_at)
            AND c.published_at = (SELECT MAX(z.published_at) FROM comments z WHERE z.parent_id=c.parent_id)
            AND NOT {self._DONE.format(a='c')} ORDER BY c.published_at DESC""", *args)
        ans = self.q(f"""SELECT c.*, 'answer' AS kind FROM comments c JOIN comments t ON t.comment_id=c.parent_id
            WHERE c.channel_id=? {vid} AND c.is_owner=0 AND c.deleted_at IS NULL AND t.is_owner=1
            AND NOT EXISTS(SELECT 1 FROM comments o WHERE o.parent_id=c.parent_id AND o.is_owner=1 AND o.published_at > c.published_at)
            AND NOT {self._DONE.format(a='c')} ORDER BY c.published_at DESC""", *args)
        return (top + ans + fol)[:limit]

    def outstanding_items(self, channel_id, days=30) -> list[dict]:
        """Mọi comment còn chờ anh (draft GENERATED/JUDGE_FAIL chưa chấm + SKIP/ESCALATE chưa có draft) → item dict cho report.
        Dùng để DRAFT_REVIEW/UNRESOLVED là file TÍCH LUỸ của kênh, không chỉ của run vừa chạy."""
        rows = self.q("""
            SELECT c.comment_id, c.video_id, v.title video_title, v.context_level, v.ep_dir, c.author_display author, c.text, c.text_vi,
                   f.reply_vi, f.judge_vi,
                   cl.primary_cat category, cl.secondary_cats, cl.summary_ja, cl.key_detail_ja, cl.classification_conf c_conf,
                   cl.understanding_conf u_conf, cl.model cls_model, d.decision, d.risk, d.generator_kind generator, d.reason,
                   f.id draft_id, f.final_text, f.footer_text, f.model, f.status, f.gate, f.rule_qc_json, f.judge_json, f.judge_model, f.reply_conf, f.run_id
            FROM comments c JOIN videos v ON v.video_id=c.video_id
            LEFT JOIN classifications cl ON cl.id=(SELECT MAX(id) FROM classifications WHERE comment_id=c.comment_id)
            LEFT JOIN decisions d ON d.id=(SELECT MAX(id) FROM decisions WHERE comment_id=c.comment_id)
            LEFT JOIN drafts f ON f.id=(SELECT MAX(id) FROM drafts WHERE comment_id=c.comment_id)
            WHERE c.channel_id=? AND d.id IS NOT NULL AND d.created_at >= datetime('now', ?)
              AND ((f.status IN('GENERATED','JUDGE_FAIL','BLOCKED') AND NOT EXISTS(SELECT 1 FROM review_queue r WHERE r.draft_id=f.id))
                   OR (f.id IS NULL AND d.decision IN('SKIP','ESCALATE')))
            ORDER BY c.published_at DESC""", channel_id, f"-{int(days)} days")
        out = []
        for r in rows:
            j = json.loads(r.pop("judge_json") or "{}")
            r["secondary"] = json.loads(r.pop("secondary_cats") or "[]")
            r["qc_fails"] = json.loads(r.pop("rule_qc_json") or "[]")
            r.update(judge_pass=bool(j.get("passed")), judge_fails=j.get("fails", []), judge_reasons=j.get("reasons", []),
                     c_conf=float(r.get("c_conf") or 0), u_conf=float(r.get("u_conf") or 0), reply_conf=float(r.get("reply_conf") or 0),
                     status=r.get("status") or "NO_DRAFT", gate=r.get("gate") or "-")
            out.append(r)
        return out

    def latest_classification(self, comment_id):
        return self.one("SELECT * FROM classifications WHERE comment_id=? ORDER BY id DESC LIMIT 1", comment_id)

    def bot_replies_in_thread(self, thread_id):
        return self.one("SELECT COUNT(*) n FROM replies WHERE status IN('SENT','SENDING') AND comment_id IN "
                        "(SELECT comment_id FROM comments WHERE comment_id=? OR parent_id=?)", thread_id, thread_id)["n"]

    # ---------------------------------------------------------------- pipeline rows
    def save_classification(self, comment_id, run_id, cls, prompt_version):
        return self.x("INSERT INTO classifications(comment_id,run_id,primary_cat,secondary_cats,flags_json,summary_ja,key_detail_ja,"
                      "viewer_intent,classification_conf,understanding_conf,model,provider,prompt_version,notes,created_at) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", comment_id, run_id, cls.primary, json.dumps(cls.secondary, ensure_ascii=False),
                      json.dumps(cls.flags, ensure_ascii=False), cls.summary_ja, cls.key_detail_ja, cls.viewer_intent, cls.c_conf,
                      cls.u_conf, cls.model, cls.provider, prompt_version, cls.notes, now())

    def save_decision(self, comment_id, channel_id, run_id, dec):
        return self.x("INSERT INTO decisions(comment_id,channel_id,run_id,decision,risk,generator_kind,footer_rule,policy_version,reason,created_at)"
                      " VALUES(?,?,?,?,?,?,?,?,?,?)", comment_id, channel_id, run_id, dec.decision, dec.risk, dec.generator,
                      dec.footer, dec.policy_version, dec.reason, now())

    def save_draft(self, **k):
        cols = ["comment_id", "channel_id", "video_id", "run_id", "attempt_no", "text_body", "footer_text", "final_text", "model",
                "provider", "prompt_version", "rule_qc_json", "judge_json", "judge_model", "reply_conf", "status", "gate", "template_combo"]
        vals = [k.get(c) for c in cols]
        return self.x(f"INSERT INTO drafts({','.join(cols)},created_at) VALUES({','.join('?' * len(cols))},?)", *vals, now())

    def recent_final_texts(self, video_id, n=30):
        return [r["final_text"] for r in self.q("SELECT final_text FROM drafts WHERE video_id=? AND status IN('APPROVED','EDITED','GENERATED') "
                                               "ORDER BY id DESC LIMIT ?", video_id, n)]

    def recent_template_combos(self, video_id, n=20):
        return [r["template_combo"] for r in self.q("SELECT template_combo FROM drafts WHERE video_id=? AND template_combo IS NOT NULL "
                                                   "ORDER BY id DESC LIMIT ?", video_id, n)]

    def video_has_reply(self, video_id):
        return bool(self.one("SELECT 1 FROM drafts WHERE video_id=? AND status IN('GENERATED','APPROVED','EDITED') LIMIT 1", video_id)
                    or self.one("SELECT 1 FROM comments WHERE video_id=? AND is_owner=1 AND parent_id IS NOT NULL LIMIT 1", video_id))

    def sent_today(self, channel_id):
        return self.one("SELECT COUNT(*) n FROM replies WHERE channel_id=? AND status='SENT' AND sent_at>=date('now')", channel_id)["n"]

    # ---------------------------------------------------------------- runs / errors / llm
    def start_run(self, mode, channels, policy_version, prompt_version):
        return self.x("INSERT INTO runs(started_at,mode,channels_json,policy_version,prompt_version) VALUES(?,?,?,?,?)",
                      now(), mode, json.dumps(channels), policy_version, prompt_version)

    def finish_run(self, run_id, counts, quota):
        self.x("UPDATE runs SET finished_at=?,counts_json=?,quota_used=? WHERE run_id=?", now(), json.dumps(counts, ensure_ascii=False), quota, run_id)

    def log_error(self, run_id, channel_id, comment_id, stage, err):
        self.x("INSERT INTO errors(run_id,channel_id,comment_id,stage,error_type,message,created_at) VALUES(?,?,?,?,?,?,?)",
               run_id, channel_id, comment_id, stage, type(err).__name__, str(err)[:500], now())

    def log_llm(self, run_id, comment_id, stage, out, ok=True):
        u = out.usage or {}
        self.x("INSERT INTO llm_calls(run_id,comment_id,stage,provider,model,tokens_in,tokens_out,elapsed_s,ok,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
               run_id, comment_id, stage, out.provider, out.model, u.get("prompt_tokens"), u.get("completion_tokens"), out.elapsed, int(ok), now())

    # ---------------------------------------------------------------- review / audit
    def review_apply(self, draft_id, decision, edited_text=None, note=None):
        st = {"APPROVE": "APPROVED", "EDIT": "EDITED", "REJECT": "REJECTED", "SKIP": "SKIPPED"}[decision]
        d = self.one("SELECT * FROM drafts WHERE id=?", draft_id)
        if not d:
            raise KeyError(f"draft {draft_id} không tồn tại")
        final = edited_text if decision == "EDIT" and edited_text else d["final_text"]
        self.x("UPDATE drafts SET status=?,final_text=? WHERE id=?", st, final, draft_id)
        self.x("INSERT INTO review_queue(draft_id,queued_at,decided_at,decision,edited_text,note) VALUES(?,?,?,?,?,?) "
               "ON CONFLICT(draft_id) DO UPDATE SET decided_at=excluded.decided_at,decision=excluded.decision,"
               "edited_text=excluded.edited_text,note=excluded.note", draft_id, d["created_at"], now(), decision, edited_text, note)
        return st

    # ---------------------------------------------------------------- like / tim (2026-10-22)
    def save_reaction(self, channel_id, comment_id, rx: dict):
        """Ghi kết quả like/tim; giữ trạng thái tốt nhất đã có (DONE/ALREADY không bị ghi đè bằng FAILED/OFF)."""
        good = ("DONE", "ALREADY")
        old = self.one("SELECT like_status, heart_status FROM reactions WHERE comment_id=?", comment_id) or {}
        lk = old.get("like_status") if old.get("like_status") in good else rx.get("like")
        ht = old.get("heart_status") if old.get("heart_status") in good else rx.get("heart")
        self.x("INSERT INTO reactions(comment_id,channel_id,like_status,heart_status,at) VALUES(?,?,?,?,?) ON CONFLICT(comment_id) DO UPDATE SET "
               "like_status=excluded.like_status,heart_status=excluded.heart_status,at=excluded.at", comment_id, channel_id, lk, ht, now())

    def audit(self, comment_id):
        return {
            "comment": self.one("SELECT * FROM comments WHERE comment_id=?", comment_id),
            "classifications": self.q("SELECT * FROM classifications WHERE comment_id=? ORDER BY id", comment_id),
            "decisions": self.q("SELECT * FROM decisions WHERE comment_id=? ORDER BY id", comment_id),
            "drafts": self.q("SELECT * FROM drafts WHERE comment_id=? ORDER BY id", comment_id),
            "replies": self.q("SELECT * FROM replies WHERE comment_id=? ORDER BY id", comment_id),
            "review": self.q("SELECT r.* FROM review_queue r JOIN drafts d ON d.id=r.draft_id WHERE d.comment_id=?", comment_id),
            "reactions": self.q("SELECT * FROM reactions WHERE comment_id=?", comment_id),
        }
