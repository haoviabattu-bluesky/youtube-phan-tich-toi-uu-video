"""cli.py — lệnh: run · fetch · channels · audit · review · reconcile.

  py -3.13 E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\cc.py run --channel F --mode draft_only [--only-video ID] [--limit 50] [--dry-run]
  py -3.13 ...\\cc.py channels                       # kiểm config + token OAuth có/không
  py -3.13 ...\\cc.py audit --comment-id Ugx...      # vì sao comment này được xử lý như vậy
  py -3.13 ...\\cc.py review --file <DRAFT_REVIEW.txt>
  py -3.13 ...\\cc.py post-browser --channel F            # đăng + tự like/tim (08–22 giờ Nhật)
  py -3.13 ...\\cc.py react-browser --channel F [--list]  # chỉ like/tim, không reply
  py -3.13 ...\\cc.py thank --channel F --comment-ids Ugx..,Ugy..   # bình luận trong UNRESOLVED → chỉ cảm ơn
"""
import argparse
import json
import sys
import time

from . import pipeline, review
from .config import load_channels, load_settings
from .store import Store


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cc.py", description="YouTube Comment Care (policy-driven, draft-first)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="fetch → classify → policy → draft → QC → report (gửi chỉ khi 3 kill switch bật)")
    r.add_argument("--channel", action="append", default=[], help="lane (F) / channel_id / tên tab; lặp lại được; bỏ trống = mọi kênh enabled")
    r.add_argument("--mode", choices=["fetch_only", "draft_only", "shadow", "auto_low", "auto_full"], help="ghi đè mode của channels.yaml cho run này")
    r.add_argument("--only-video", help="chỉ 1 video_id")
    r.add_argument("--limit", type=int, default=None, help="số comment pending tối đa / kênh (mặc định settings.limits.max_comments_llm_per_run)")
    r.add_argument("--dry-run", action="store_true", help="fetch/analyze/draft thật nhưng 0 comment được gửi")
    r.add_argument("--send", action="store_true", help="cờ thứ 3 cho phép gửi (cần env COMMENT_CARE_AUTO_REPLY=1 + mode auto_*)")
    r.add_argument("--reclassify", action="store_true", help="phân loại lại dù đã có kết quả cũ cùng prompt_version")
    f = sub.add_parser("fetch", help="chỉ kéo comment về DB, không LLM")
    f.add_argument("--channel", action="append", default=[])
    f.add_argument("--only-video")
    sub.add_parser("channels", help="liệt kê kênh trong config + trạng thái token OAuth")
    rp = sub.add_parser("report", help="dựng lại DRAFT_REVIEW/UNRESOLVED tích luỹ từ DB (không fetch, không LLM)")
    rp.add_argument("--channel", required=True)
    a = sub.add_parser("audit", help="trace comment → classification → decision → draft → reply")
    a.add_argument("--comment-id", required=True)
    v = sub.add_parser("review", help="áp YOUR_DECISION trong DRAFT_REVIEW.txt vào DB")
    v.add_argument("--file", required=True)
    v.add_argument("--force", action="store_true", help="áp câu EDIT dù sai luật reply ngắn (chỉ khi anh bảo)")
    pb = sub.add_parser("post-browser", help="ĐĂNG reply đã APPROVED bằng trình duyệt profile GPM, gõ chậm như người (anh chốt 2026-10-05)")
    pb.add_argument("--channel", required=True)
    pb.add_argument("--draft-ids", help="vd 1,4,8 — mặc định mọi draft APPROVED/EDITED chưa gửi của kênh")
    pb.add_argument("--dry-run", action="store_true", help="mở trình duyệt, tìm comment, KHÔNG gõ/gửi")
    pb.add_argument("--cdp-port", type=int, help="KHÔNG qua GPM: attach Chrome đang mở ở cổng này (vd 9222 = HAOVIABATTU_PROFILE, lane A/M)")
    pb.add_argument("--like", default="", help="draft id cần LIKE comment gốc, vd 1,2,3 (bỏ trống = tự chọn theo luật react_browser)")
    pb.add_argument("--heart", default="", help="draft id cần THẢ TIM comment gốc, vd 1,3 (bỏ trống = tự chọn)")
    pb.add_argument("--no-react", action="store_true", help="không like/tim gì cả")
    pb.add_argument("--ignore-hours", action="store_true", help="đăng cả ngoài 08–22 giờ Nhật (chỉ khi anh bảo)")
    pb.add_argument("--keep-open", action="store_true", help="giữ profile GPM mở sau khi xong (mặc định TẮT để người khác dùng — anh chốt 2026-10-08)")
    rb = sub.add_parser("react-browser", help="chỉ LIKE/THẢ TIM bình luận của khách (không reply) qua profile GPM")
    rb.add_argument("--channel", required=True)
    rb.add_argument("--list", action="store_true", help="chỉ in danh sách sẽ like/tim, không mở trình duyệt")
    rb.add_argument("--days", type=int, default=14)
    rb.add_argument("--limit", type=int, default=30)
    rb.add_argument("--dry-run", action="store_true")
    rb.add_argument("--cdp-port", type=int)
    rb.add_argument("--keep-open", action="store_true")
    rb.add_argument("--ignore-hours", action="store_true")
    th = sub.add_parser("thank", help="bình luận trong UNRESOLVED (mơ hồ/hỏi chế độ…) → tạo reply CHỈ CẢM ƠN đã duyệt, chờ post-browser")
    th.add_argument("--channel", required=True)
    th.add_argument("--comment-ids", required=True, help="vd UgxAAA,UgyBBB")
    th.add_argument("--text", default="コメントありがとうございます。", help="mặc định コメントありがとうございます。")
    ap_ = sub.add_parser("approve", help="đánh dấu draft APPROVED theo lời duyệt của anh (ghi note)")
    ap_.add_argument("--draft-ids", required=True)
    ap_.add_argument("--note", default="anh duyệt")
    rc = sub.add_parser("reconcile", help="đối soát reply SENDING/UNKNOWN với YouTube (cần OAuth)")
    rc.add_argument("--channel", required=True)
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    try:
        return _dispatch(args)
    except Exception as e:  # PostBlocked (GPM tắt/bận, sai kênh…) → 1 dòng rõ ràng thay vì traceback
        from .browser_poster import PostBlocked
        if isinstance(e, PostBlocked):
            print(f"✗ DỪNG: {e}")
            return 3
        raise


def _dispatch(args):
    settings = load_settings()
    store = Store(settings["paths"]["state_db"])
    if args.cmd == "channels":
        for c in load_channels():
            tok = c.oauth_token_path(settings)
            print(f"{c.lane:7} {c.channel_id} enabled={c.enabled!s:5} mode={c.mode:10} footer={c.footer_policy:2} token={'CÓ' if tok.exists() else 'chưa'}  {c.channel_name} {c.note[:60]}")
        return 0
    if args.cmd == "report":
        print(json.dumps(pipeline.rebuild_reports(args.channel, settings, store), ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "audit":
        print(json.dumps(store.audit(args.comment_id), ensure_ascii=False, indent=1, default=str))
        return 0
    if args.cmd == "review":
        for line in review.apply(store, args.file, force=args.force):
            print(line)
        return 0
    if args.cmd == "approve":
        for did in [int(x) for x in args.draft_ids.split(",") if x.strip()]:
            print(f"draft {did}: {store.review_apply(did, 'APPROVE', note=args.note)}")
        return 0
    if args.cmd == "post-browser":
        from . import browser_poster
        from .config import get_channel
        ch = get_channel(args.channel)
        ids = [int(x) for x in args.draft_ids.split(",")] if args.draft_ids else None
        q = ("SELECT f.id draft_id, f.comment_id, f.video_id, f.final_text, c.text FROM drafts f JOIN comments c ON c.comment_id=f.comment_id "
             "WHERE f.channel_id=? AND f.status IN('APPROVED','EDITED') ")
        rows = store.q(q + (f"AND f.id IN ({','.join('?' * len(ids))}) " if ids else "") + "ORDER BY f.video_id, f.id", ch.channel_id, *(ids or []))
        if not rows:
            print("không có draft APPROVED/EDITED nào để đăng (chạy `approve --draft-ids` hoặc `review` trước)")
            return 1
        print(f"{len(rows)} draft sẽ {'được kiểm (dry-run)' if args.dry_run else 'ĐĂNG'} trên kênh {ch.channel_name} qua profile {ch.mail}")
        ids_of = lambda s: {int(x) for x in s.split(",") if x.strip()}  # noqa: E731
        if not (args.dry_run or args.ignore_hours or _in_hours(settings)):
            return 2
        like, heart = ids_of(args.like), ids_of(args.heart)
        if not args.no_react and not (like or heart):
            from .react_browser import auto_ids
            like, heart = auto_ids(store, rows)
        if args.no_react:
            like, heart = set(), set()
        print(f"like {len(like)} · tim {len(heart)} (draft id like={sorted(like)} tim={sorted(heart)})")
        res = browser_poster.run(store, ch, rows, keep_open=args.keep_open, dry_run=args.dry_run, cdp_port=args.cdp_port,
                                 like_ids=like, heart_ids=heart)
        print(json.dumps([{k: v for k, v in r.items() if k in ('draft_id', 'comment_id', 'status', 'author_seen', 'error', 'reactions')} for r in res], ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "react-browser":
        from . import react_browser
        from .config import get_channel
        ch = get_channel(args.channel)
        items = react_browser.candidates(store, ch, args.days, args.limit)
        print(f"{len(items)} bình luận cần like/tim trên {ch.channel_name} ({args.days} ngày gần nhất)")
        for it in items:
            print(f"  {it['comment_id']}  like={'Y' if it['like'] else '-'} tim={'Y' if it['heart'] else '-'}  [{it['category']}] {(it['text'] or '')[:50].replace(chr(10), ' ')}")
        if args.list or not items:
            return 0
        if not (args.dry_run or args.ignore_hours or _in_hours(settings)):
            return 2
        res = react_browser.run(store, ch, items, dry_run=args.dry_run, cdp_port=args.cdp_port, keep_open=args.keep_open)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "thank":
        from .config import get_channel
        from .reply_rules import final_fails
        ch = get_channel(args.channel)
        bad = final_fails(args.text)
        if bad:
            print(f"✗ câu cảm ơn sai luật: {bad}")
            return 1
        for cid in [x.strip() for x in args.comment_ids.split(",") if x.strip()]:
            c = store.one("SELECT * FROM comments WHERE comment_id=? AND channel_id=?", cid, ch.channel_id)
            if not c:
                print(f"{cid}: ✗ không có trong DB của kênh {ch.lane}")
                continue
            if c["is_owner"] or store.one("SELECT 1 FROM replies WHERE comment_id=?", cid) or store.one(
                    "SELECT 1 FROM drafts WHERE comment_id=? AND status IN('APPROVED','EDITED','SENT')", cid):
                print(f"{cid}: ↷ đã có reply/draft duyệt hoặc là bình luận của kênh → bỏ qua")
                continue
            did = store.save_draft(comment_id=cid, channel_id=ch.channel_id, video_id=c["video_id"], run_id=None, attempt_no=1,
                                   text_body=args.text, footer_text="", final_text=args.text, model="manual_thanks", provider="manual",
                                   prompt_version=settings["versions"]["prompt_version"], rule_qc_json="[]", judge_json=None, judge_model=None,
                                   reply_conf=1.0, status="GENERATED", gate="DRAFT", template_combo="THANKS:manual")
            print(f"{cid}: draft {did} → {store.review_apply(did, 'APPROVE', note='thank (chỉ cảm ơn)')}")
        return 0
    if args.cmd == "reconcile":
        from . import sender
        from .config import get_channel
        for n in sender.reconcile(store, get_channel(args.channel), settings):
            print(n)
        return 0
    if args.cmd == "fetch":
        from .config import get_channel, youtube_api_key
        from .yt_api import YT
        yt = YT(youtube_api_key(settings), settings["youtube_api"]["cost"])
        for k in (args.channel or [c.lane for c in load_channels() if c.enabled]):
            ch = get_channel(k)
            nv, nc, errs = pipeline.fetch_channel(yt, store, ch, settings["limits"]["max_threads_fetch_per_channel"], args.only_video)
            print(f"{ch.lane}: {nv} video, {nc} comment rows, pending={len(store.pending_comments(ch.channel_id, 999))}, quota={yt.quota_used}, errs={errs}")
        return 0
    limit = args.limit or int(settings["limits"]["max_comments_llm_per_run"])
    settings["_reclassify"] = bool(getattr(args, "reclassify", False))
    res = pipeline.run(args.channel, args.mode, limit, args.only_video, args.dry_run, args.send, settings, store)
    print("\n" + json.dumps(res, ensure_ascii=False, indent=1))
    return 0


def _in_hours(settings) -> bool:
    """Chỉ đăng/like trong khung giờ Nhật settings.limits.send_hours_jst (mặc định 08–22)."""
    lo, hi = settings["limits"]["send_hours_jst"]
    h = time.gmtime(time.time() + 9 * 3600).tm_hour
    if lo <= h < hi:
        return True
    print(f"⏸ bây giờ {h}h giờ Nhật — ngoài khung {lo}–{hi}h → không đăng. Để sáng chạy lại (hoặc --ignore-hours nếu anh bảo).")
    return False


if __name__ == "__main__":
    sys.exit(main())
