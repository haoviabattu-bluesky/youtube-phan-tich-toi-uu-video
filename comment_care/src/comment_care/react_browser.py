"""react_browser.py — LIKE + THẢ TIM bình luận của khách (HUONG_DAN_HERMES 2026-10-22 mục 6).

Luật chọn:
- LIKE  : mọi bình luận của khách, TRỪ nhóm nhạy cảm/rác (anh chốt 2026-10-15: không like/tim câu chính trị/giới/mỉa mai —
          like lên đó = kênh đồng tình) và bình luận em hiểu không chắc (low_confidence / sensitive_fallback).
- TIM   : chỉ bình luận tích cực (khen, cảm ơn, đồng tình, kể chuyện, xin chủ đề) đã hiểu chắc.
- KHÔNG BAO GIỜ dislike. Nút đang bật sẵn thì không bấm (bấm lại là gỡ) — reactions.react đã chặn.
- Đã like/tim xong (bảng reactions DONE/ALREADY) thì lần sau bỏ qua.
"""
import random
import time

NO_LIKE = {"HOSTILE", "POLITICAL_SOCIAL", "CRISIS", "SPAM_PROMO", "UNCLEAR", "OFF_TOPIC", "VIEWER_TO_VIEWER"}
HEART = {"PRAISE", "GRATITUDE_SIMPLE", "AGREEMENT", "EXPERIENCE_SHARING", "REQUEST"}
UNSURE_REASONS = ("low_confidence", "sensitive_fallback", "can_fact_check")
GOOD = ("DONE", "ALREADY")

_INFO = """SELECT c.comment_id, c.video_id, c.text, cl.primary_cat category, d.reason,
       r.like_status, r.heart_status
FROM comments c
LEFT JOIN classifications cl ON cl.id=(SELECT MAX(id) FROM classifications WHERE comment_id=c.comment_id)
LEFT JOIN decisions d ON d.id=(SELECT MAX(id) FROM decisions WHERE comment_id=c.comment_id)
LEFT JOIN reactions r ON r.comment_id=c.comment_id
"""


def wants(row) -> tuple[bool, bool]:
    """→ (like?, heart?) cho 1 bình luận đã phân loại. Chưa phân loại → không đụng."""
    cat, why = row.get("category"), row.get("reason") or ""
    if not cat or cat in NO_LIKE or why.startswith(UNSURE_REASONS):
        return False, False
    like = row.get("like_status") not in GOOD
    heart = cat in HEART and row.get("heart_status") not in GOOD
    return like, heart


def auto_ids(store, drafts) -> tuple[set, set]:
    """Cho post-browser: draft nào kèm like / tim (khi không truyền --like/--heart)."""
    like, heart = set(), set()
    for d in drafts:
        row = store.one(_INFO + "WHERE c.comment_id=?", d["comment_id"])
        if not row:
            continue
        lk, ht = wants(row)
        if lk:
            like.add(d["draft_id"])
        if ht:
            heart.add(d["draft_id"])
    return like, heart


def candidates(store, ch, days=14, limit=30) -> list[dict]:
    """Bình luận của khách trong `days` ngày còn cần like/tim (mới nhất trước)."""
    rows = store.q(_INFO + "WHERE c.channel_id=? AND c.is_owner=0 AND c.deleted_at IS NULL AND c.published_at >= ? "
                           "ORDER BY c.video_id, c.published_at DESC", ch.channel_id,
                   time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - days * 86400)))
    out = []
    for r in rows:
        lk, ht = wants(r)
        if lk or ht:
            out.append({**r, "like": lk, "heart": ht})
    return out[:limit]


def run(store, ch, items, log=print, dry_run=False, cdp_port=None, keep_open=False) -> list[dict]:
    from .browser_poster import _mouse_click, open_comment, pause, session
    from .reactions import react
    res = []
    with session(ch, log, keep_open, cdp_port) as page:
        for i, it in enumerate(items):
            if i:
                pause(20, 60, log, "nghỉ giữa 2 bình luận")
            thread, target = open_comment(page, it["video_id"], it["comment_id"], it["text"], log)
            if thread is None:
                log(f"    ✗ {it['comment_id'][-8:]} không thấy bình luận (có thể khách đã xoá)")
                res.append({"comment_id": it["comment_id"], "status": "NOT_FOUND"})
                continue
            rx = react(page, target, _mouse_click, log, like=it["like"], heart=it["heart"], dry_run=dry_run)
            if not dry_run:
                store.save_reaction(ch.channel_id, it["comment_id"], rx)
            res.append({"comment_id": it["comment_id"], "status": "OK", "reactions": rx})
            time.sleep(random.uniform(1, 3))
    return res
