"""pipeline.py — orchestrator 1 kênh/1 run (spec mục K). Mỗi comment: prefilter → classify → policy → template|LLM → footer → rule QC → judge → gate."""
import json
import time
from pathlib import Path

from . import classifier, context, generator, judge as judge_mod, prefilter, report, sender
from .config import POLICY_DIR, TEMPLATES_DIR, load_channels, read_text, youtube_api_key
from .llm import LLM
from .policy import Policy
from .qc_rules import RuleQC
from .templates import Templates
from .yt_api import YT, YTError


def _tab(ch):
    return ch.sheet_tab or ch.lane


def fetch_channel(yt: YT, store, ch, max_threads, only_video=None) -> tuple[int, int, list[str]]:
    """Kéo video + comment thread về DB. → (n_videos, n_comments, errors)."""
    errs = []
    chinfo, ids = yt.uploads(ch.channel_id)
    api_name = chinfo["snippet"]["title"]
    if ch.channel_name and api_name != ch.channel_name:
        errs.append(f"tên kênh API '{api_name}' ≠ config '{ch.channel_name}' (vẫn chạy, kiểm lại channels.yaml)")
    if only_video:
        ids = [v for v in ids if v == only_video]
    n_c = 0
    for v in yt.videos(ids):
        store.upsert_video(v["video_id"], ch.channel_id, v["title"], v["description"][:1200], v["published_at"], v["comment_count"])
        if v["comment_count"] == 0:
            continue
        try:
            for top, reps in yt.threads(v["video_id"], ch.channel_id, max_threads):
                store.upsert_comment(top)
                for r in reps:
                    store.upsert_comment(r)
                n_c += 1 + len(reps)
        except YTError as e:
            if e.kind in ("commentsDisabled", "notFound"):
                errs.append(f"{v['video_id']}: {e.kind}")
            else:
                raise
    return len(ids), n_c, errs


def run(keys: list[str], mode: str | None, limit: int, only_video: str | None, dry_run: bool, cli_send: bool, settings, store,
        max_llm: int | None = None, log=print) -> list[dict]:
    chans = [c for c in load_channels() if (not keys and c.enabled) or any(k.lower() in (c.lane.lower(), c.channel_id.lower(), (c.sheet_tab or "").lower()) for k in keys)]
    if not chans:
        raise SystemExit("không có kênh nào khớp/enabled")
    pv, prv = settings["versions"]["policy_version"], settings["versions"]["prompt_version"]
    run_id = store.start_run(mode or "per-channel", [c.lane for c in chans], pv, prv)
    yt = YT(youtube_api_key(settings), settings["youtube_api"]["cost"])
    pol = Policy(POLICY_DIR / "policy_table.yaml")
    tpls = Templates(TEMPLATES_DIR / "templates.yaml")
    style = read_text(POLICY_DIR / "ja_style_guide.md")
    pdir = Path(settings["_prompts_dir"])
    sys_cls, sys_gen, sys_judge = read_text(pdir / "classify.system.md"), read_text(pdir / "generate.system.md"), read_text(pdir / "judge.system.md")
    all_names = [c.channel_name for c in load_channels()]
    llm = None
    summaries = []
    for ch in chans:
        m = mode or ch.mode
        ch_mode = ch if m == ch.mode else type(ch)(**{**ch.__dict__, "mode": m})
        store.upsert_channel(ch_mode, run_id)
        qc = RuleQC(POLICY_DIR / "blocklist_ja.txt", [n for n in all_names if n and n != ch.channel_name])
        items, errs = [], []
        log(f"\n=== {ch.lane} {ch.channel_name} ({ch.channel_id}) mode={m}")
        try:
            nv, nc, e2 = fetch_channel(yt, store, ch, settings["limits"]["max_threads_fetch_per_channel"], only_video)
            errs += e2
            log(f"  fetch: {nv} video, {nc} comment rows, quota={yt.quota_used}")
        except YTError as e:
            store.log_error(run_id, ch.channel_id, None, "fetch", e)
            log(f"  ✗ fetch lỗi {e} — bỏ kênh")
            summaries.append({"lane": ch.lane, "error": str(e)})
            continue
        pending = store.pending_comments(ch.channel_id, limit, only_video)
        log(f"  pending: {len(pending)} comment")
        if llm is None:
            llm = LLM(settings, store, run_id)
        n_llm = 0
        for c in pending:
            if max_llm is not None and n_llm >= max_llm:
                break
            it = process_one(c, ch_mode, m, store, run_id, llm, pol, tpls, qc, style, sys_cls, sys_gen, sys_judge, settings, dry_run, cli_send, log)
            n_llm += 1
            items.append(it)
        # DRAFT_REVIEW/UNRESOLVED là file tích luỹ: gộp thêm mọi draft/skip còn chờ anh từ các run trước (ưu tiên item của run này)
        seen = {i["comment_id"] for i in items}
        merged = items + [o for o in store.outstanding_items(ch.channel_id) if o["comment_id"] not in seen]
        translate_items(merged, store, llm or LLM(settings, store, run_id), log)
        paths = report.write_reports(_with_tab(ch_mode), run_id, m, merged, yt.quota_used, errs, Path(settings["paths"]["reports_dir"]))
        log(f"  report: {paths['report']}")
        if paths["n_unresolved"]:
            log(f"  Có {paths['n_unresolved']} bình luận chưa được trả lời. Xem tại:\n  {paths['unresolved']}")
        summaries.append({"lane": ch.lane, "items": len(items), "drafts": paths["n_drafts"], "unresolved": paths["n_unresolved"], "dir": paths["dir"]})
    store.finish_run(run_id, {"channels": summaries}, yt.quota_used)
    return summaries


def translate_items(items: list[dict], store, llm, log=print):
    """Bổ sung bản dịch tiếng Việt (comment / reply / lý do judge) cho item còn thiếu; lưu DB để không dịch lại."""
    todo = [i for i in items if not i.get("text_vi") or (i.get("final_text") and not i.get("reply_vi"))]
    if todo:
        log(f"  dịch tiếng Việt cho {len(todo)} comment/draft…")
    for i in todo:
        jr = "; ".join(i.get("judge_reasons") or [])
        d = llm.translate_vi(i.get("text", ""), i.get("final_text", "") or "", jr, comment_id=i["comment_id"])
        if d["comment_vi"] and not d["comment_vi"].startswith("(dịch lỗi"):
            store.set_comment_vi(i["comment_id"], d["comment_vi"])
        i["text_vi"] = d["comment_vi"]
        if i.get("draft_id"):
            store.set_draft_vi(i["draft_id"], d["reply_vi"], d["judge_vi"])
            i["reply_vi"], i["judge_vi"] = d["reply_vi"], d["judge_vi"]


def rebuild_reports(key: str, settings, store) -> dict:
    """`cc.py report --channel F`: dựng lại DRAFT_REVIEW/UNRESOLVED từ DB (chỉ gọi LLM để dịch phần còn thiếu)."""
    from .config import get_channel
    ch = get_channel(key)
    items = store.outstanding_items(ch.channel_id)
    translate_items(items, store, LLM(settings, store, None))
    return report.write_reports(_with_tab(ch), 0, "report-only", items, 0, [], Path(settings["paths"]["reports_dir"]))


def _with_tab(ch):
    class _C:  # report chỉ cần vài field + sheet_tab_or_lane
        pass
    o = _C()
    o.__dict__.update(ch.__dict__)
    o.sheet_tab_or_lane = _tab(ch)
    return o


def process_one(c, ch, mode, store, run_id, llm, pol, tpls, qc, style, sys_cls, sys_gen, sys_judge, settings, dry_run, cli_send, log) -> dict:
    kind = c.get("kind", "top")
    vrow = store.get_video(c["video_id"]) or {"video_id": c["video_id"], "title": "", "description_head": ""}
    it = {"comment_id": c["comment_id"], "video_id": c["video_id"], "video_title": vrow.get("title", ""), "author": c.get("author_display", ""),
          "text": c.get("text", ""), "kind": kind, "run_id": run_id}
    # ---- video context (bắt buộc đọc trước khi trả lời)
    if vrow.get("context_json") and vrow.get("context_level") not in (None, "NONE", "L1"):
        vc = context.VideoContext(**json.loads(vrow["context_json"]))
    else:
        vc = context.build(vrow, ch, settings)
        store.set_video_context(vc.video_id, vc.ep_dir, vc.level, vc.to_json())
    it.update(context_level=vc.level, ep_dir=vc.ep_dir)
    vtext = vc.to_prompt_text()
    top, reps = store.thread(c["parent_id"] or c["comment_id"])
    thread = classifier.thread_text(top, reps, c["comment_id"]) if (c["parent_id"] or reps) else ""
    # ---- prefilter
    label, why = prefilter.prefilter(c)
    cls = classifier.Classification()
    if label == "GRATITUDE_SHORT":
        cls.primary, cls.c_conf, cls.u_conf, cls.summary_ja, cls.model = "GRATITUDE_SIMPLE", 0.99, 0.99, "短い感謝", "prefilter"
    elif label is None:
        prev = store.latest_classification(c["comment_id"])
        try:
            if prev and prev.get("prompt_version") == settings["versions"]["prompt_version"] and not settings.get("_reclassify"):
                cls = classifier.from_row(prev)      # tái dùng kết quả run trước (tiết kiệm token, cùng prompt_version)
            else:
                cls = classifier.classify(llm, sys_cls, c, kind, thread, vtext)
                store.save_classification(c["comment_id"], run_id, cls, settings["versions"]["prompt_version"])
        except Exception as e:  # noqa: BLE001
            store.log_error(run_id, ch.channel_id, c["comment_id"], "classify", e)
            cls.notes = f"classify error {type(e).__name__}"
    it.update(category=cls.primary, secondary=cls.secondary, c_conf=cls.c_conf, u_conf=cls.u_conf, summary_ja=cls.summary_ja,
              key_detail_ja=cls.key_detail_ja, cls_model=cls.model, flags=cls.flags)
    # ---- policy
    dec = pol.decide(cls, kind, vc.level, store.bot_replies_in_thread(c["parent_id"] or c["comment_id"]), ch, label)
    store.save_decision(c["comment_id"], ch.channel_id, run_id, dec)
    it.update(decision=dec.decision, risk=dec.risk, generator=dec.generator, reason=dec.reason or why, footer_rule=dec.footer)
    log(f"  · {c['comment_id'][-8:]} [{cls.primary} c={cls.c_conf:.2f} u={cls.u_conf:.2f}] → {dec.decision}/{dec.generator} {dec.reason}  ctx={vc.level}")
    if dec.decision != "REPLY" or mode == "fetch_only":
        it["status"] = "NO_DRAFT"
        return it
    # ---- generate (template | LLM) + footer + rule QC + judge, regen ≤ N
    recent = store.recent_final_texts(c["video_id"])
    footer = tpls.footer(ch.footer_policy, dec.footer, c["video_id"], first_reply_of_video=not store.video_has_reply(c["video_id"]))
    feedback, out, combo, body, jr, fails = None, None, None, "", None, []
    max_try = 1 if dec.generator == "TEMPLATE" else 1 + int(settings["limits"]["judge_regen_max"])
    for attempt in range(1, max_try + 1):
        try:
            if dec.generator == "TEMPLATE":
                body, combo = tpls.render(dec.category, cls.key_detail_ja, store.recent_template_combos(c["video_id"]))
                fam = "template"
            else:
                body, out = generator.generate(llm, sys_gen, ch, style, vtext, cls, dec, c, thread, recent, feedback)
                fam = out.family
        except Exception as e:  # noqa: BLE001
            store.log_error(run_id, ch.channel_id, c["comment_id"], "generate", e)
            it.update(status="BLOCKED", qc_fails=[f"generate error {type(e).__name__}: {str(e)[:100]}"], decision="SKIP", reason="generate_error")
            return it
        fails = qc.check(body, footer, dec, tpls.all_footer_texts(), recent)
        if fails:
            feedback = "規則違反: " + ", ".join(fails)
            if dec.generator == "TEMPLATE":
                break
            continue
        if dec.generator == "TEMPLATE":
            jr = judge_mod.JudgeResult(passed=True, reply_conf=0.95, model="template", parse_ok=True)
            break
        try:
            jr = judge_mod.judge(llm, sys_judge, c, vtext, cls, body, footer, thread, fam)
            footer = judge_mod.soften(jr, footer)      # 9 FAIL → bỏ footer thay vì viết lại; 7 đơn lẻ → cảnh báo, không chặn
            if jr.passed and dec.double_judge:
                jr2 = judge_mod.judge(llm, sys_judge, c, vtext, cls, body, footer, thread, "sol" if jr.provider == "sol" else "gemini")
                footer = judge_mod.soften(jr2, footer)
                if not jr2.passed:
                    jr = jr2
        except Exception as e:  # noqa: BLE001
            store.log_error(run_id, ch.channel_id, c["comment_id"], "judge", e)
            jr = judge_mod.JudgeResult(reasons=[f"judge error {type(e).__name__}"])
        if jr.passed:
            break
        feedback = (jr.fix or "") + " / " + "; ".join(jr.reasons)
    final = (body + ("\n\n" + footer if footer else "")).strip()
    judge_pass = bool(jr and jr.passed and not fails)
    status = "GENERATED" if judge_pass else ("BLOCKED" if fails else "JUDGE_FAIL")
    gate = pol.gate(dec, cls, jr.reply_conf if jr else 0.0, judge_pass, ch, store.sent_today(ch.channel_id)) if judge_pass else "SKIP"
    if mode in ("draft_only", "shadow") and gate == "SEND":
        gate = "DRAFT" if mode == "draft_only" else "WOULD_SEND"
    did = store.save_draft(comment_id=c["comment_id"], channel_id=ch.channel_id, video_id=c["video_id"], run_id=run_id, attempt_no=attempt,
                           text_body=body, footer_text=footer, final_text=final, model=(out.model if out else "template"),
                           provider=(out.provider if out else "template"), prompt_version=settings["versions"]["prompt_version"],
                           rule_qc_json=json.dumps(fails, ensure_ascii=False), judge_json=json.dumps(jr.to_dict(), ensure_ascii=False) if jr else None,
                           judge_model=(jr.model if jr else None), reply_conf=(jr.reply_conf if jr else 0.0), status=status, gate=gate, template_combo=combo)
    it.update(draft_id=did, final_text=final, footer_text=footer, model=(out.model if out else "template"), status=status, gate=gate, qc_fails=fails,
              judge_pass=judge_pass, judge_fails=(jr.fails if jr else []), judge_reasons=(jr.reasons if jr else []), judge_model=(jr.model if jr else None),
              reply_conf=(jr.reply_conf if jr else 0.0), attempts=attempt)
    if not judge_pass:
        it["decision"] = "SKIP"
        it["reason"] = "qc_fail" if fails else "judge_fail"
        return it
    # ---- send (Phase 2b) — fail closed
    if gate == "SEND":
        ok, why = sender.can_send(ch, settings, cli_send, dry_run)
        if not ok:
            it["gate"] = "DRAFT"
            it["send_blocked"] = why
            return it
        try:
            sender.verify_identity(ch, settings)
            resp = sender.send_reply(store, ch, settings, c["comment_id"], did, final)
            store.x("UPDATE drafts SET status='SENT' WHERE id=?", did)
            it.update(status="SENT", youtube_reply_id=resp.get("id"))
            lo, hi = settings["limits"]["send_gap_seconds"]
            time.sleep(lo + (hi - lo) * 0.5)
        except Exception as e:  # noqa: BLE001
            store.log_error(run_id, ch.channel_id, c["comment_id"], "send", e)
            it.update(send_error=str(e)[:200])
    return it
