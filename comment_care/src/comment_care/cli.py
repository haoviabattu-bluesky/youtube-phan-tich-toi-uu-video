"""cli.py — lệnh: run · fetch · channels · audit · review · reconcile.

  py -3.13 E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\cc.py run --channel F --mode draft_only [--only-video ID] [--limit 50] [--dry-run]
  py -3.13 ...\\cc.py channels                       # kiểm config + token OAuth có/không
  py -3.13 ...\\cc.py audit --comment-id Ugx...      # vì sao comment này được xử lý như vậy
  py -3.13 ...\\cc.py review --file <DRAFT_REVIEW.txt>
"""
import argparse
import json
import sys

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
    pb = sub.add_parser("post-browser", help="ĐĂNG reply đã APPROVED bằng trình duyệt profile GPM, gõ chậm như người (anh chốt 2026-10-05)")
    pb.add_argument("--channel", required=True)
    pb.add_argument("--draft-ids", help="vd 1,4,8 — mặc định mọi draft APPROVED/EDITED chưa gửi của kênh")
    pb.add_argument("--dry-run", action="store_true", help="mở trình duyệt, tìm comment, KHÔNG gõ/gửi")
    pb.add_argument("--keep-open", action="store_true", help="giữ profile GPM mở sau khi xong (mặc định TẮT để người khác dùng — anh chốt 2026-10-08)")
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
        for line in review.apply(store, args.file):
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
        res = browser_poster.run(store, ch, rows, keep_open=args.keep_open, dry_run=args.dry_run)
        print(json.dumps([{k: v for k, v in r.items() if k in ('draft_id', 'comment_id', 'status', 'author_seen', 'error')} for r in res], ensure_ascii=False, indent=1))
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


if __name__ == "__main__":
    sys.exit(main())
