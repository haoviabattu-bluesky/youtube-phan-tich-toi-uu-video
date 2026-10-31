"""report.py — COMMENT_REPORT.txt · DRAFT_REVIEW.txt · UNRESOLVED_COMMENTS.txt · HIGH_RISK.txt · reply_log.jsonl (spec mục Q/R, brief 9/10/43/70)."""
import json
import time
from collections import Counter
from pathlib import Path


def comment_url(video_id, comment_id):
    return f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"


def _hdr(title):
    return f"{'=' * 78}\n{title}\n{'=' * 78}\n"


def write_reports(ch, run_id, mode, items: list[dict], quota_used: int, errors: list[str], out_root: Path, date_str=None) -> dict:
    date_str = date_str or time.strftime("%Y-%m-%d")
    out = Path(out_root) / date_str / ch.sheet_tab_or_lane
    out.mkdir(parents=True, exist_ok=True)
    cats = Counter(i.get("category", "?") for i in items)
    dec = Counter(i.get("decision", "?") for i in items)
    gates = Counter(i.get("gate", "-") for i in items)
    unresolved = [i for i in items if i.get("decision") in ("SKIP", "ESCALATE") or i.get("status") in ("JUDGE_FAIL", "BLOCKED")]
    # Draft judge-fail vẫn đưa vào DRAFT_REVIEW (ACTION=NEEDS_HUMAN_REVIEW) để anh thấy và hiệu chỉnh judge; đồng thời nằm trong UNRESOLVED
    drafts = [i for i in items if i.get("final_text") and i.get("status") in ("GENERATED", "SENT", "APPROVED", "JUDGE_FAIL")]
    high = [i for i in items if i.get("risk") == "HIGH" or i.get("decision") == "ESCALATE"]

    # ---------------- COMMENT_REPORT
    L = [_hdr(f"COMMENT CARE REPORT — {ch.channel_name} ({ch.handle}) — run #{run_id} — {time.strftime('%Y-%m-%d %H:%M')}"),
         f"MODE: {mode}   QUOTA USED: {quota_used} unit", f"Channel: {ch.channel_id}   Lane: {ch.lane}",
         f"Videos checked: {len({i.get('video_id') for i in items})}", f"Comments processed: {len(items)}",
         f"Replied (SENT): {sum(1 for i in items if i.get('status') == 'SENT')}", f"Drafted: {len(drafts)}",
         f"Skipped: {dec.get('SKIP', 0)}   Escalated: {dec.get('ESCALATE', 0)}   No reply needed: {dec.get('NO_REPLY_NEEDED', 0)}   Already handled: {dec.get('ALREADY_HANDLED', 0)}",
         f"Unresolved: {len(unresolved)}   Errors: {len(errors)}", "", "By category:"]
    L += [f"  {k:24} {v}" for k, v in cats.most_common()]
    L += ["", "By gate:"] + [f"  {k:10} {v}" for k, v in gates.most_common()]
    L += ["", "Context level per video:"]
    seen = {}
    for i in items:
        seen.setdefault(i.get("video_id"), (i.get("context_level"), i.get("video_title", "")[:50], i.get("ep_dir")))
    L += [f"  {v} {lv:4} {t} ← {ep or '(không map được thư mục tập)'}" for v, (lv, t, ep) in seen.items()]
    if high:
        L += ["", "High-risk comments:"] + [f"  {i['comment_id']} [{i.get('category')}] {i.get('text', '')[:90].replace(chr(10), ' ')}" for i in high]
    if errors:
        L += ["", "Errors (5 đầu):"] + [f"  {e}" for e in errors[:5]]
    L += ["", f"Unresolved file: {out / 'UNRESOLVED_COMMENTS.txt'}", f"Draft review file: {out / 'DRAFT_REVIEW.txt'}", ""]
    (out / "COMMENT_REPORT.txt").write_text("\n".join(L), encoding="utf-8")

    # ---------------- DRAFT_REVIEW (anh ghi YOUR_DECISION: APPROVE | EDIT: <text> | REJECT | SKIP)
    D = [_hdr(f"DRAFT REVIEW — {ch.channel_name} — run #{run_id}"),
         "Cách chấm: ở mỗi block, sửa dòng `YOUR_DECISION:` thành APPROVE | EDIT: <câu anh sửa> | REJECT | SKIP rồi chạy",
         f"  py -3.13 E:\\CLAUDE\\YOUTUBE\\PHAN_TICH_TOI_UU_VIDEO\\comment_care\\cc.py review --file \"{out / 'DRAFT_REVIEW.txt'}\"", ""]
    for i in drafts:
        D += [f"DRAFT_ID: {i['draft_id']}", f"VIDEO: {i.get('video_title', '')[:70]}  ({i['video_id']})  context={i.get('context_level')}",
              f"COMMENT_URL: {comment_url(i['video_id'], i['comment_id'])}", f"AUTHOR: {i.get('author', '')}", "COMMENT (tiếng Nhật):", i.get("text", "").strip(),
              "COMMENT (dịch tiếng Việt):", (i.get("text_vi") or "(chưa dịch)").strip(), "",
              f"CATEGORY: {i.get('category')}  (secondary {i.get('secondary')})  RISK: {i.get('risk')}  GENERATOR: {i.get('generator')}  MODEL: {i.get('model')}",
              f"SUMMARY: {i.get('summary_ja', '')}  KEY_DETAIL: {i.get('key_detail_ja', '')}",
              f"CONFIDENCE: classify={i.get('c_conf', 0):.2f} understand={i.get('u_conf', 0):.2f} reply(judge)={i.get('reply_conf', 0):.2f}  JUDGE: {i.get('judge_model')} {'PASS' if i.get('judge_pass') else 'FAIL ' + str(i.get('judge_fails'))}",
              f"ACTION: {('NEEDS_HUMAN_REVIEW — judge FAIL: ' + '; '.join(i.get('judge_reasons') or [])[:300]) if i.get('status') == 'JUDGE_FAIL' else ('WOULD_REPLY' if i.get('gate') in ('SEND', 'DRAFT', 'WOULD_SEND') else i.get('gate'))}  (gate={i.get('gate')}, footer={'yes' if i.get('footer_text') else 'no'})",
              *([f"JUDGE NHẬN XÉT (dịch): {i.get('judge_vi')}"] if i.get("judge_vi") else []),
              "PROPOSED REPLY (tiếng Nhật — đây là câu sẽ đăng):", i["final_text"], "",
              "PROPOSED REPLY (dịch tiếng Việt để anh hiểu, KHÔNG đăng):", (i.get("reply_vi") or "(chưa dịch)").strip(), "",
              "YOUR_DECISION: ", "-" * 78, ""]
    (out / "DRAFT_REVIEW.txt").write_text("\n".join(D), encoding="utf-8")

    # ---------------- UNRESOLVED (format brief mục 9)
    U = [_hdr(f"UNRESOLVED COMMENTS — {ch.channel_name} — {date_str}"), f"Có {len(unresolved)} bình luận chưa được trả lời.", ""]
    for i in unresolved:
        U += [f"CHANNEL: {ch.channel_name} ({ch.channel_id})", f"VIDEO: {i['video_id']}", f"VIDEO_TITLE: {i.get('video_title', '')}",
              f"VIDEO_URL: https://www.youtube.com/watch?v={i['video_id']}", "", f"COMMENT_ID: {i['comment_id']}",
              f"COMMENT_URL: {comment_url(i['video_id'], i['comment_id'])}", f"AUTHOR: {i.get('author', '')}", "COMMENT (tiếng Nhật):", i.get("text", "").strip(),
              "COMMENT (dịch tiếng Việt):", (i.get("text_vi") or "(chưa dịch)").strip(), "",
              f"REASON_NOT_REPLIED: {i.get('decision')} — {i.get('reason', '')}" + (f" — QC: {i.get('qc_fails')}" if i.get("qc_fails") else "")
              + (f" — JUDGE: {i.get('judge_fails')} {i.get('judge_reasons')}" if i.get("judge_fails") else ""),
              f"CATEGORY: {i.get('category')}  SUMMARY: {i.get('summary_ja', '')}", "", f"MODEL: {i.get('model') or i.get('cls_model', '')}",
              f"CONFIDENCE: classify={i.get('c_conf', 0):.2f} understand={i.get('u_conf', 0):.2f}", "-" * 78, ""]
    (out / "UNRESOLVED_COMMENTS.txt").write_text("\n".join(U), encoding="utf-8")

    # ---------------- HIGH_RISK + reply_log
    H = [_hdr(f"HIGH RISK — {ch.channel_name} — {date_str}")]
    for i in high:
        H += [f"{i['comment_id']} [{i.get('category')}] {i.get('decision')} {comment_url(i['video_id'], i['comment_id'])}", i.get("text", "").strip(), "-" * 40]
    (out / "HIGH_RISK.txt").write_text("\n".join(H), encoding="utf-8")
    with (out / "reply_log.jsonl").open("a", encoding="utf-8") as f:
        for i in items:
            f.write(json.dumps({k: v for k, v in i.items() if k not in ("thread",)}, ensure_ascii=False) + "\n")
    return {"dir": str(out), "report": str(out / "COMMENT_REPORT.txt"), "drafts": str(out / "DRAFT_REVIEW.txt"),
            "unresolved": str(out / "UNRESOLVED_COMMENTS.txt"), "n_unresolved": len(unresolved), "n_drafts": len(drafts)}
