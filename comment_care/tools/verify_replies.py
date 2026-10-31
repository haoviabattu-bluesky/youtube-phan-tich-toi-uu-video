"""verify_replies.py — đối chiếu reply đã đăng qua trình duyệt bằng YouTube Data API (API KEY công khai, không cần OAuth).

  py -3.13 E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\tools\\verify_replies.py --channel F

Lấy mọi reply row SENT / UNKNOWN_RECONCILE / SENDING chưa có youtube_reply_id → comments.list?parentId=<thread> → tìm reply của
CHÍNH KÊNH có nội dung khớp (YouTube tự chèn "@tên " ở đầu khi trả lời 1 reply → bỏ prefix đó khi so).
Thấy → ghi youtube_reply_id + SENT. Không thấy → giữ nguyên, in ✗ (API trễ vài phút; chạy lại sau 5–10 phút). KHÔNG BAO GIỜ đăng lại.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from comment_care.config import get_channel, load_settings, youtube_api_key  # noqa: E402
from comment_care.store import Store  # noqa: E402
from comment_care.yt_api import YT, YTError  # noqa: E402


def norm(t: str) -> str:
    t = re.sub(r"^\s*@\S+\s*", "", t or "")
    return re.sub(r"[\s　]", "", t)


def main():
    ap = argparse.ArgumentParser(description="Đối chiếu reply đã đăng bằng YouTube Data API")
    ap.add_argument("--channel", required=True, help="lane (F, L, N, O, P, Q)")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    s = load_settings()
    store = Store(s["paths"]["state_db"])
    ch = get_channel(a.channel)
    yt = YT(youtube_api_key(s), s["youtube_api"]["cost"])
    rows = store.q("""SELECT r.id, r.comment_id, r.draft_id, r.final_text, r.status, c.video_id FROM replies r
                      JOIN comments c ON c.comment_id=r.comment_id
                      WHERE r.channel_id=? AND r.status IN('SENT','UNKNOWN_RECONCILE','SENDING')
                        AND (r.youtube_reply_id IS NULL OR r.youtube_reply_id='') ORDER BY r.id""", ch.channel_id)
    if not rows:
        print(f"{ch.lane} {ch.channel_name}: không còn reply nào cần đối chiếu.")
        return 0
    used = {r["youtube_reply_id"] for r in store.q("SELECT youtube_reply_id FROM replies WHERE youtube_reply_id IS NOT NULL")}
    cache, ok, miss = {}, 0, 0
    for r in rows:
        parent = r["comment_id"].split(".")[0]
        url = f"https://www.youtube.com/watch?v={r['video_id']}&lc={r['comment_id']}"
        try:
            if parent not in cache:
                cache[parent] = yt.replies(parent, r["video_id"], ch.channel_id)
        except YTError as e:
            if e.kind == "quotaExceeded":
                print("✗ hết quota YouTube API hôm nay → dừng, chạy lại ngày mai")
                return 1
            print(f"✗ CHƯA THẤY  draft {r['draft_id']}  ({e.kind}: bình luận gốc có thể đã bị xoá)  {url}")
            miss += 1
            continue
        want = norm(r["final_text"])[:20]
        hit = next((x for x in cache[parent] if x["is_owner"] and x["comment_id"] not in used and norm(x["text"])[:20] == want), None)
        if hit:
            store.x("UPDATE replies SET status='SENT', youtube_reply_id=?, sent_at=COALESCE(sent_at, ?) WHERE id=?",
                    hit["comment_id"], hit["published_at"], r["id"])
            store.x("UPDATE drafts SET status='SENT' WHERE id=?", r["draft_id"])
            used.add(hit["comment_id"])
            ok += 1
            print(f"✓ ĐÃ THẤY   draft {r['draft_id']}  reply_id={hit['comment_id']}  (trước: {r['status']})")
        else:
            miss += 1
            print(f"✗ CHƯA THẤY  draft {r['draft_id']}  ({r['status']})  {url}")
    print(f"\n{ch.lane} {ch.channel_name}: ✓ {ok} · ✗ {miss} · quota {yt.quota_used} unit")
    if miss:
        print("✗ còn lại: đợi 5–10 phút chạy lại; vẫn chưa thấy → mở link xem tận mắt, ghi vào báo cáo. TUYỆT ĐỐI không đăng lại.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
