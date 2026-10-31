# -*- coding: utf-8 -*-
"""analyze.py — chấm điểm 1 video nguồn theo công thức WIN của lane + sinh đề bài.

Hai tầng:
  score()  — thuần số, không LLM: lọc cứng (sub, định dạng manga, độ dài, kênh mình)
             rồi chấm điểm chủ đề / khuôn tiêu đề / tốc độ view.
  draft()  — 1 call LLM (gemini-3.8-flash qua router của h2dev) sinh đề bài tiếng Việt
             cho máy 1. Nếu LLM chết → trả khung xương từ lanes.draft_rule, KHÔNG bịa.
"""
import datetime
import json
import os
import re
import sys

from lanes import LANES, MANGA_TITLE, MANGA_ANY, SEMI_FORMAT, OWN_CHANNEL_IDS
from ytapi import parse_duration as _parse_duration

H2DEV_PIPELINE = r"E:\CLAUDE\YOUTUBE\h2dev\pipeline"

# Ngưỡng cứng của anh (2026-10-18)
HARD = {
    "max_days": 5,          # video mới đăng trong 5 ngày
    "min_views_A": 100_000,  # HẠNG A: đúng luật anh
    "min_views_B": 50_000,   # HẠNG B: nới 1 nửa, có nhãn rõ
    "min_views_C": 30_000,   # HẠNG C: chỉ để ngày nào cũng có đề
    "max_subs": 10_000,      # kênh < 10k sub
    "min_sec": 5 * 60,       # manga dài, không nhận shorts
    "max_sec": 45 * 60,
}

# THÁC NƯỚC NỚI NGƯỠNG (đo thật 2026-10-18: quét 392 video manga ≤7 ngày của cả thị trường,
# chỉ 1 video đạt đủ 100k + <10k sub + khớp ngách ⇒ nếu cứng thì phần lớn các ngày trắng).
#
# LUẬT CỨNG KHÔNG BAO GIỜ NỚI: kênh < 10.000 sub (anh chốt). Chỉ nới VIEW và TUỔI video.
# (Bản đầu 2026-10-18 có nới sub lên 30k/50k — SAI, đã sửa: kênh 17.600 sub lọt vào báo cáo.)
LADDER = [
    # (tên bậc, view tối thiểu, ngày tối đa, nhãn hiển thị)
    ("A", 100_000, 5, "A · đúng luật: >100k view, ≤5 ngày, <10k sub"),
    ("B", 50_000, 5, "B · nới view: ≥50k (giữ ≤5 ngày, <10k sub)"),
    ("C", 30_000, 5, "C · nới view sâu: ≥30k (giữ ≤5 ngày, <10k sub)"),
    ("D", 30_000, 7, "D · nới ngày: ≥30k, ≤7 ngày (giữ <10k sub)"),
    ("E", 15_000, 7, "E · nới rộng: ≥15k, ≤7 ngày (giữ <10k sub)"),
]
GRADE_BONUS = {"A": 8.0, "B": 5.0, "C": 3.0, "D": 2.0, "E": 1.0}


def _hits(patterns, text):
    n = 0
    for p in patterns:
        if re.search(p, text, re.I):
            n += 1
    return n


def score(video, channel, lane, now_ts, channel_manga_ratio=None):
    """Trả dict {ok, reason, grade, score, detail}. ok=False ⇒ loại hẳn.

    Bậc (grade) = bậc CAO NHẤT mà video đạt trong LADDER; lọc cứng dùng bậc thấp nhất
    (E) để không bỏ sót, rồi báo cáo ghi rõ video đã nới trục nào.
    """
    sn = video["snippet"]
    st = video.get("statistics") or {}
    cd = video.get("contentDetails") or {}
    title = sn.get("title", "")
    desc = sn.get("description", "") or ""
    views = int(st.get("viewCount") or 0)
    likes = int(st.get("likeCount") or 0)
    comments = int(st.get("commentCount") or 0)
    # độ dài: ưu tiên 'seconds' do run_daily gắn, không có thì parse ISO 8601
    sec = cd.get("seconds")
    if sec is None:
        sec = _parse_duration(cd.get("duration", ""))
    subs = int((channel.get("statistics") or {}).get("subscriberCount") or 0)
    ch_id = sn.get("channelId", "")
    pub_ts = cd.get("published_ts")
    if pub_ts is None:
        # web search KHÔNG cho publishedAt, chỉ cho "3 日前" (age_days). Nếu bỏ qua thì
        # pub_ts=now ⇒ hours=1 ⇒ view/giờ = đúng bằng view (đo thật 2026-10-19: 32.306 v/h
        # cho video 32.306 view). Ưu tiên age_days, chỉ dùng publishedAt khi có.
        ad = cd.get("age_days")
        if ad:
            hours = max(1.0, float(ad) * 24.0)
        else:
            try:
                pub_ts = datetime.datetime.strptime(sn.get("publishedAt", ""),
                                                    "%Y-%m-%dT%H:%M:%SZ") \
                    .replace(tzinfo=datetime.timezone.utc).timestamp()
                hours = max(1.0, (now_ts - pub_ts) / 3600.0)
            except ValueError:
                hours = 1.0
    else:
        hours = max(1.0, (now_ts - pub_ts) / 3600.0)
    days_old = hours / 24.0

    L = LANES[lane]
    out = {"video_id": video["id"], "ok": False, "reason": "", "detail": {}}

    # ---------------------------------------------------------------- lọc cứng
    if ch_id in OWN_CHANNEL_IDS:
        out["reason"] = "kênh của chính mình"
        return out
    if (video.get("status") or {}).get("privacyStatus") not in (None, "public"):
        out["reason"] = "không public"
        return out
    if not (HARD["min_sec"] <= sec <= HARD["max_sec"]):
        out["reason"] = f"độ dài {sec // 60} phút ngoài khoảng {HARD['min_sec'] // 60}–{HARD['max_sec'] // 60}"
        return out

    # bậc: bậc cao nhất mà video đạt (sub LUÔN phải < HARD["max_subs"] — luật cứng)
    grade, grade_label, gbonus = None, "", 0.0
    if subs >= HARD["max_subs"]:
        out["reason"] = f"kênh {subs:,} sub ≥ {HARD['max_subs']:,} (luật cứng, không nới)"
        return out
    for g, vmin, dmax, label in LADDER:
        if views >= vmin and days_old <= dmax:
            grade, grade_label = g, label
            gbonus = GRADE_BONUS[g]
            break
    if grade is None:
        worst = LADDER[-1]
        out["reason"] = (f"dưới bậc thấp nhất: {views:,} view / {days_old:.1f} ngày "
                         f"(sàn {worst[1]:,} view, ≤{worst[2]} ngày, <{HARD['max_subs']:,} sub)")
        return out

    manga_title = bool(re.search(MANGA_TITLE, title, re.I))
    manga_any = bool(re.search(MANGA_ANY, title + " " + desc, re.I))
    semi = bool(re.search(SEMI_FORMAT, title, re.I))
    ratio = channel_manga_ratio if channel_manga_ratio is not None else 0.0
    # định dạng: phải là manga (title hoặc kênh chủ yếu manga). ゆっくり解説 thuần ⇒ loại.
    if not manga_title and not (manga_any and ratio >= 0.5) and not ratio >= 0.6:
        out["reason"] = ("không phải manga/faceless manga"
                         + (" (chỉ là ゆっくり解説)" if semi else ""))
        return out

    # ---------------------------------------------------------------- chấm điểm
    d = {}
    # 1) chủ đề (title nặng gấp 2)
    win_t = _hits(L["topics_win"], title)
    win_d = _hits(L["topics_win"], desc)
    lose_t = _hits(L["topics_lose"], title)
    lose_d = _hits(L["topics_lose"], desc)
    soft = _hits(L["topics_soft"], title)
    d["topic_win"] = round(win_t * 2.0 + win_d * 0.5, 2)
    d["topic_lose"] = round(lose_t * 2.5 + lose_d * 0.5, 2)
    d["topic_soft"] = round(soft * 0.5, 2)

    # 2) khuôn tiêu đề
    d["title_pat"] = _hits(L["title_pat"], title) * 1.5

    # 3) định dạng
    d["format"] = 2.0 if manga_title else (1.0 if manga_any else 0.0)
    if ratio >= 0.7:
        d["format"] += 1.0
    if semi and not manga_title:
        d["format"] -= 1.0

    # 4) độ dài hợp kênh mình (16–26 phút) — ngoài khoảng chỉ trừ nhẹ
    mins = sec / 60.0
    d["length_fit"] = 1.0 if 10 <= mins <= 35 else 0.0

    # 5) tốc độ nổ: view/giờ, chuẩn hoá log10
    vph = views / hours
    d["velocity"] = round(min(6.0, max(0.0, (vph / 100.0) ** 0.5 * 1.2)), 2)   # 100 v/h→1.2, 1000→3.8, 3000→6
    # 6) tương tác
    like_rate = likes / views * 100 if views else 0
    cmt_rate = comments / views * 1000 if views else 0
    d["engagement"] = round(min(3.0, like_rate * 0.6 + cmt_rate * 0.4), 2)

    # 7) phạt nếu video nguồn quá giống 1 tập mình đã làm (trùng tiêu đề kênh mình) — bỏ qua ở đây,
    #    việc chống lặp làm bằng state video_id.

    base = (d["topic_win"] + d["title_pat"] + d["format"] + d["length_fit"]
            + d["velocity"] + d["engagement"] - d["topic_lose"] + d["topic_soft"])

    # Điều kiện NGÁCH: video nguồn phải chạm từ khoá LÕI của lane trong TIÊU ĐỀ, không thì
    # dù nổ to cũng không dùng được (bài học 2026-10-18: đề M nhận oan video "50代で結婚…
    # 年金と相続" chỉ vì có chữ 年金; đề M2 nhận video "trailer house" 106k view).
    core = L.get("core_win") or []
    core_hit = sum(1 for c in core if c in title)
    niche_ok = core_hit >= 1 and d["topic_lose"] < d["topic_win"]

    out.update({
        "ok": niche_ok, "grade": grade, "grade_label": grade_label,
        "score": round(base + gbonus, 2),
        "detail": d, "views": views, "subs": subs, "sec": sec,
        "likes": likes, "comments": comments, "hours": round(hours, 1),
        "days_old": round(days_old, 1),
        "views_per_hour": round(vph, 1), "mins": round(mins, 1),
        "title": title, "channel": sn.get("channelTitle", ""), "channel_id": ch_id,
        "published": sn.get("publishedAt", ""), "manga_ratio": round(ratio, 2),
        "grade_bonus": gbonus,
    })
    if not niche_ok:
        out["reason"] = ("lạc ngách: tiêu đề không có từ khoá lõi của lane "
                         f"(core_hit={core_hit}, lose={d['topic_lose']}, win={d['topic_win']})")
        return out
    if out["score"] < 6.0:
        out["ok"] = False
        out["reason"] = f"điểm quá thấp ({out['score']}) — lạc công thức WIN"
    return out


# ---------------------------------------------------------------------- LLM draft
def _llm():
    if H2DEV_PIPELINE not in sys.path:
        sys.path.insert(0, H2DEV_PIPELINE)
    # BẪY CHẾT NGƯỜI (đo thật 2026-10-20): Task Scheduler chạy bằng `pythonw.exe` ⇒
    # `sys.stdout` / `sys.stderr` là **None**. `llm_client.py` dòng đầu làm
    # `sys.stdout.reconfigure(encoding="utf-8")` ⇒ AttributeError ⇒ import llm_client CHẾT
    # ⇒ cả 8 đề bài rơi về "khung xương". Chạy tay bằng `py -3.13` không thấy lỗi này.
    import io
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is None:
            setattr(sys, name, io.TextIOWrapper(io.BytesIO(), encoding="utf-8",
                                                errors="replace", newline=""))
    import llm_client
    return llm_client


PROMPT = """Bạn là biên tập viên kênh YouTube manga faceless tiếng Nhật. Nhiệm vụ: từ MỘT video nguồn đang nổi, viết ĐỀ BÀI cho kênh của mình — KHÔNG copy, chỉ lấy cấu trúc và lý do thắng.

## KÊNH CỦA MÌNH — LANE {lane} ({channel})
Công thức WIN (bắt buộc bám):
{win_one_line}

Vùng chủ đề ĐƯỢC làm: {win_zone}
Vùng ĐÃ THUA (tránh): {lose_zone}

## VIDEO NGUỒN
Tiêu đề: {title}
Kênh: {src_channel} ({subs} sub)
Số liệu: {views} view trong {hours} giờ ({vph} view/giờ), {likes} like, {comments} bình luận, dài {mins} phút
Mô tả (có thể rỗng):
{desc}

## YÊU CẦU
1. Trả về DUY NHẤT một object JSON, không markdown, không giải thích ngoài JSON. Mọi giá trị bằng TIẾNG VIỆT, riêng tiêu đề/chữ thumbnail là TIẾNG NHẬT.
2. KHÔNG bịa số liệu. Chỉ dùng con số có trong tiêu đề/mô tả nguồn. Chỗ nào cần số mà nguồn không có thì ghi đúng chuỗi [SỐ CẦN KIỂM].
3. Khác video nguồn ít nhất 30%: đổi nhân vật, đổi nghề/bối cảnh, đổi cái kết — nhưng GIỮ cơ chế thắng.

Schema:
{{
  "vi_sao_thang": "1-2 câu: vì sao video nguồn nổ (theo số ở trên + công thức WIN của lane)",
  "de_bai": "1-2 câu: đề bài tập mới của mình (nhân vật + hoàn cảnh + cái giá)",
  "khac_nguon": "1 câu: khác video nguồn ở đâu (đổi gì, giữ gì)",
  "hook_3cau": "3 câu mở đầu 0-10s, tiếng Việt mô tả thoại tiếng Nhật sẽ dùng",
  "title_jp": "tiêu đề tiếng Nhật theo khuôn của lane, tối đa 45 ký tự",
  "thumbnail_jp": "chữ trên thumbnail tiếng Nhật, tối đa 14 ký tự, phải xuất hiện trong kịch bản",
  "so_lieu_can": ["các con số phải có trong kịch bản, ghi rõ số nào lấy từ nguồn, số nào cần kiểm"],
  "cau_hoi_cuoi": "câu hỏi mời bình luận (tiếng Nhật)",
  "rui_ro": "1 câu: rủi ro của đề này so với công thức WIN"
}}"""


def draft(item, lane, use_llm=True):
    """Sinh đề bài. Trả dict; luôn có khoá 'nguon' = 'llm' hoặc 'khung_xuong'."""
    L = LANES[lane]
    if use_llm:
        try:
            lc = _llm()
            p = PROMPT.format(
                lane=lane, channel=L["channel"], win_one_line=L["win_one_line"],
                win_zone="; ".join(L["win_zone"]), lose_zone="; ".join(L["lose_zone"]),
                title=item["title"], src_channel=item["channel"], subs=item["subs"],
                views=item["views"], hours=item["hours"], vph=item["views_per_hour"],
                likes=item["likes"], comments=item["comments"], mins=item["mins"],
                desc=(item.get("desc") or "")[:1200])
            r = lc.chat(p, task="short", max_tokens=1600, temperature=0.7,
                        timeout=180, verbose=False)
            txt = (r.text or "").strip()
            txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.M)
            m = re.search(r"\{.*\}", txt, flags=re.S)
            if m:
                obj = json.loads(m.group(0))
                obj["nguon"] = f"llm:{r.model}"
                return obj
        except Exception as e:                     # noqa: BLE001
            err = f"{type(e).__name__}: {str(e)[:120]}"
        else:
            err = "LLM trả về không có JSON"
    else:
        err = "tắt LLM (--no-llm)"

    # fallback: khung xương, KHÔNG bịa nội dung
    return {
        "nguon": "khung_xuong",
        "loi": err,
        "vi_sao_thang": (f"Nguồn: {item['views']:,} view / {item['hours']:.0f} giờ "
                         f"({item['views_per_hour']:,.0f} view/giờ), kênh {item['subs']:,} sub. "
                         f"Điểm khớp công thức lane {lane}: {item['score']}."),
        "de_bai": "[CHƯA SINH — LLM lỗi. Đọc công thức WIN của lane rồi tự chọn đề.]",
        "khac_nguon": "[CHƯA SINH]",
        "hook_3cau": "[CHƯA SINH]",
        "title_jp": "[CHƯA SINH]",
        "thumbnail_jp": "[CHƯA SINH]",
        "so_lieu_can": [],
        "cau_hoi_cuoi": "[CHƯA SINH]",
        "rui_ro": L["draft_rule"],
    }
