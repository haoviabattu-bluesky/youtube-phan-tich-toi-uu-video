# -*- coding: utf-8 -*-
"""run_daily.py — tìm video nguồn đang nổ cho lane L / N / O / M, 2 đề/lane/ngày.

KHÔNG DÙNG YOUTUBE DATA API (bản 2026-10-18 tối). Lý do: project đã cạn 10.000 unit/ngày
(HTTP 403 `exceeded your quota`) → mọi lệnh videos.list/channels.list đều chết. Toàn bộ dữ
liệu lấy từ web (`ytweb.py`), 0 quota, không cần key:

    view, tiêu đề, kênh, channelId, ngày đăng, ĐỘ DÀI  ← trang search (videoRenderer)
    sub của kênh                                    ← youtubei/v1/browse (チャンネル登録者数)
    like / bình luận                                 ← trang watch (chỉ video lọt lọc cứng)

Quy mô: 120 từ khoá × 12 trang × filter tháng ≈ 6000–10000 video thô/lần, chạy 12 luồng,
khoảng 1–2 phút (đo thật: 40 từ khoá = 2003 unique trong 17s).

Chạy tay:
  py -3.13 run_daily.py
  py -3.13 run_daily.py --lane L,N --no-llm
  py -3.13 run_daily.py --dry-run
  py -3.13 run_daily.py --min-views 100000 --days 5     # ngưỡng cứng đúng luật anh
  py -3.13 run_daily.py --search-budget 40              # quét ít từ khoá (test nhanh)
  py -3.13 run_daily.py --pages 6 --threads 12

Lịch: Task Scheduler 'ViralHunt0300' (create_task.ps1).
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import analyze                     # noqa: E402
import enrich                      # noqa: E402
import report                      # noqa: E402
import sheet_note                  # noqa: E402
import state                       # noqa: E402
import translate                   # noqa: E402
import watchlist                   # noqa: E402
import ytweb                       # noqa: E402
from lanes import LANES, MANGA_ANY  # noqa: E402

ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(HERE, "config.json")
LOG_PATH = os.path.join(HERE, "state", "run_last.log")
DEFAULT_LANES = ["L", "N", "O", "M"]
SHEET_TABS = {"L": "L-shakai-no-naze", "N": "Lane-N", "O": "Lane-O", "M": "M-teinengo-anaba"}


def load_cfg():
    if os.path.exists(CONFIG):
        return json.load(open(CONFIG, encoding="utf-8"))
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", default=",".join(DEFAULT_LANES))
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--min-views", type=int, default=None)
    ap.add_argument("--per-lane", type=int, default=2)
    ap.add_argument("--search-budget", type=int, default=None,
                    help="số TỪ KHOÁ tối đa (mỗi từ khoá ~70–200 video, 0 quota)")
    ap.add_argument("--pages", type=int, default=None,
                    help="số trang kết quả mỗi từ khoá (~20 video/trang)")
    ap.add_argument("--threads", type=int, default=None, help="số luồng quét song song")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-api", action="store_true",
                    help="ép KHÔNG dùng YouTube Data API, chỉ dùng đường web (để test dự phòng)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    cfg = load_cfg()
    lanes = [x.strip() for x in a.lane.split(",") if x.strip() in LANES]
    if not lanes:
        sys.exit(f"lane không hợp lệ. Chọn trong {list(LANES)}")
    days = a.days or cfg.get("max_days", analyze.HARD["max_days"])
    analyze.HARD["max_days"] = days
    analyze.HARD["max_subs"] = cfg.get("max_subs", analyze.HARD["max_subs"])
    if a.min_views:
        analyze.HARD["min_views_A"] = a.min_views
    sbudget = a.search_budget if a.search_budget is not None else cfg.get("search_budget", 120)
    pages = a.pages if a.pages is not None else cfg.get("pages", 12)
    threads = a.threads if a.threads is not None else cfg.get("threads", 12)

    def log(msg):
        # Task Scheduler chạy `pythonw.exe` ⇒ KHÔNG có stdout ⇒ mọi dòng log biến mất,
        # không cách nào biết đêm đó tool chết ở đâu. Luôn ghi thêm file.
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as fh:
                fh.write(f"{datetime.datetime.now():%H:%M:%S} {msg}\n")
        except OSError:
            pass
        if not a.quiet:
            print(msg, flush=True)

    open(LOG_PATH, "w", encoding="utf-8").close()
    log(f"=== viral_hunt {datetime.date.today().isoformat()} · "
        f"python={sys.executable} · argv={sys.argv[1:]} ===")

    t0 = time.time()
    day = datetime.date.today().isoformat()
    conn = state.connect()
    conn.executescript(watchlist.SCHEMA)

    log(f"=== viral_hunt {day} · lane {','.join(lanes)} · ≤{days} ngày · "
        f"{sbudget} từ khoá × {pages} trang × {threads} luồng · 0 quota API ===")

    # ---------------------------------------------------------- 1. quét web
    jobs = []
    for lane in lanes:
        kws = watchlist.next_keywords(conn, lane, LANES[lane]["keywords"], sbudget // len(lanes), day)
        for kw in kws:
            jobs.append((lane, kw))
    log(f"  {len(jobs)} từ khoá cần quét")

    def _one(job):
        lane, kw = job
        # KHÔNG dùng stop_after_age: sort theo view nên trang 2+ hay toàn video cũ,
        # dừng sớm là mất phần lớn video mới nằm sâu trong trang.
        return lane, kw, ytweb.search(kw, sp=ytweb.SP_VIEW_MONTH, pages=pages)

    raw = {}          # video_id -> item
    kw_err = 0
    with ThreadPoolExecutor(max_workers=threads) as pool:
        for lane, kw, res in pool.map(_one, jobs):
            if isinstance(res, dict):
                kw_err += 1
                log(f"  「{kw}」 LỖI: {res.get('_error')}")
                continue
            hit = [x for x in res if x["age_days"] <= days]
            log(f"  「{kw}」 {len(res):>4} video → {len(hit):>3} ≤{days} ngày (lane {lane})")
            for x in hit:
                x["lane_hint"] = lane
                raw.setdefault(x["video_id"], x)
    log(f"  quét xong: {len(raw)} video thô ≤{days} ngày · lỗi {kw_err} từ khoá · "
        f"{time.time() - t0:.0f}s")

    # ------------------------------------ 2. xác minh bằng YouTube Data API (1 unit/50 id)
    # Đường CHÍNH (2026-10-20): API trả publishedAt CHÍNH XÁC, view/like/comment, độ dài,
    # sub kênh — đúng những thứ trang web làm tròn hoặc không có. Chi phí: 824 video ≈ 17
    # call videos.list + 800 kênh ≈ 16 call channels.list = ~33 unit (trần 10.000/ngày).
    # KHÔNG dùng search.list (100 unit/call) — đó là thứ từng làm cạn quota.
    cids = list({x["channel_id"] for x in raw.values() if x.get("channel_id")})
    subs_cache = {}
    api_on = False if a.no_api else enrich.available()
    if a.no_api:
        enrich._API["ok"] = False
        enrich._API["error"] = "tắt bằng --no-api"
    t_sub = time.time()
    if api_on:
        log(f"  xác minh bằng YouTube Data API: {len(raw)} video · {len(cids)} kênh…")
        vd = enrich.videos(list(raw.keys()))
        chd = enrich.channels(cids)
        n_v = n_c = 0
        for vid, x in raw.items():
            it = vd.get(vid)
            if not it:
                continue
            st = it.get("statistics") or {}
            cd = it.get("contentDetails") or {}
            sn = it.get("snippet") or {}
            x["views"] = int(st.get("viewCount") or x["views"])
            x["likes"] = int(st.get("likeCount") or 0)
            x["comments"] = int(st.get("commentCount") or 0)
            sec = analyze._parse_duration(cd.get("duration", ""))
            if sec:
                x["seconds"] = sec
            pub = sn.get("publishedAt") or ""
            if pub:
                try:
                    ts = datetime.datetime.strptime(pub, "%Y-%m-%dT%H:%M:%SZ") \
                        .replace(tzinfo=datetime.timezone.utc).timestamp()
                    x["age_days"] = round((time.time() - ts) / 86400.0, 2)
                    x["published"] = pub
                except ValueError:
                    pass
            if sn.get("title"):
                x["title"] = sn["title"]
            n_v += 1
        for cid, it in chd.items():
            st = it.get("statistics") or {}
            if st.get("hiddenSubscriberCount"):
                subs_cache[cid] = None
            else:
                subs_cache[cid] = int(st.get("subscriberCount") or 0)
            n_c += 1
        log(f"  API: {n_v}/{len(raw)} video · {n_c}/{len(cids)} kênh · "
            f"{enrich.status()['units']} unit · {time.time() - t_sub:.0f}s")
        # kênh API không trả (đã xoá / sai id) → thử web, vẫn không được thì None (bị loại)
        missing = [c for c in cids if c not in subs_cache]
    else:
        missing = cids
        log(f"  !! YouTube Data API KHÔNG dùng được ({enrich.status()['error'][:120]}) "
            f"→ chuyển sang đường web")

    # ---- dự phòng web: HTML trang kênh TRƯỚC, browse sau (xem ytweb.channel_subs)
    if missing:
        log(f"  lấy sub bằng web cho {len(missing)} kênh ({threads} luồng)…")
        batches = [missing[i::threads] for i in range(threads)]
        with ThreadPoolExecutor(max_workers=threads) as pool:
            for part in pool.map(lambda b: ytweb.channel_subs(b, {}, sleep=0.02), batches):
                subs_cache.update(part)
    n_ok = sum(1 for v in subs_cache.values() if v is not None)
    log(f"  sub: {n_ok}/{len(subs_cache)} kênh xác minh được "
        f"({time.time() - t_sub:.0f}s)")
    n_unknown = len(subs_cache) - n_ok
    if n_unknown:
        log(f"  !! {n_unknown} kênh KHÔNG đọc được sub → LOẠI HẲN (luật cứng <10k sub, "
            f"không xác minh được thì không được đoán 0)")
    for x in raw.values():
        x["subs"] = subs_cache.get(x.get("channel_id"))

    # ------------------------------------------------- 2b. tỉ lệ manga THẬT của kênh
    # Bản trước đoán ratio = 1.0 nếu tiêu đề có chữ 漫画, ngược lại 0.3 — đoán mò.
    # Hệ quả: video không có chữ 漫画 trong tiêu đề bị loại oan, còn kênh không phải manga
    # chỉ cần 1 tiêu đề có chữ 漫画 là qua. Đo thật bằng 20 tiêu đề gần nhất của kênh.
    # Chỉ đo cho kênh có video ĐÃ QUA cổng sub/view/tuổi ⇒ số request nhỏ (~100 kênh).
    need_ratio = set()
    for x in raw.values():
        if x.get("subs") is None:
            continue
        if x["subs"] >= analyze.HARD["max_subs"]:
            continue
        if x["views"] < analyze.LADDER[-1][1] or x["age_days"] > days:
            continue
        if not (analyze.HARD["min_sec"] <= x["seconds"] <= analyze.HARD["max_sec"]):
            continue
        if x.get("channel_id"):
            need_ratio.add(x["channel_id"])
    log(f"  đo tỉ lệ manga thật cho {len(need_ratio)} kênh ứng viên…")
    t_r = time.time()
    ratio_cache = {}
    if api_on:
        # playlistItems = 1 unit/kênh
        for cid in need_ratio:
            ratio_cache[cid] = enrich.manga_ratio(chd.get(cid), n=20)
    rest = [c for c in need_ratio if ratio_cache.get(c) is None]
    if rest:
        log(f"  {len(rest)} kênh đo tỉ lệ manga bằng web ({threads} luồng)…")

        def _ratio_batch(batch):
            out = {}
            for cid in batch:
                ts = ytweb.channel_recent_titles(cid, n=20)
                out[cid] = (sum(1 for t in ts if re.search(MANGA_ANY, t, re.I)) / len(ts)) \
                    if ts else None
            return out

        rb = [rest[i::threads] for i in range(threads)]
        with ThreadPoolExecutor(max_workers=threads) as pool:
            for part in pool.map(_ratio_batch, rb):
                ratio_cache.update(part)
    log(f"  tỉ lệ manga: {sum(1 for v in ratio_cache.values() if v is not None)}"
        f"/{len(ratio_cache)} kênh đo được ({time.time() - t_r:.0f}s)")


    # ---------------------------------------------------------- 3. chấm điểm
    scored = {lane: [] for lane in lanes}
    rejects = {}
    for x in raw.values():
        subs = x.get("subs")
        if subs is None:
            # LUẬT CỨNG: kênh phải <10k sub. Không đọc được sub thì KHÔNG được coi là 0 —
            # đó đúng là lỗi đã để kênh 711.000 sub lọt vào báo cáo 2026-10-20.
            rejects["sub không xác minh được (loại)"] = \
                rejects.get("sub không xác minh được (loại)", 0) + 1
            continue
        v = {"id": x["video_id"],
             "snippet": {"title": x["title"], "channelId": x["channel_id"],
                         "channelTitle": x["channel"], "description": "",
                         "publishedAt": x.get("published") or ""},
             "statistics": {"viewCount": x["views"],
                            "likeCount": x.get("likes") or 0,
                            "commentCount": x.get("comments") or 0},
             "contentDetails": {"seconds": x["seconds"], "age_days": x["age_days"]},
             "status": {"privacyStatus": "public"}}
        ch = {"statistics": {"subscriberCount": subs}}
        # tỉ lệ manga của kênh = ĐO THẬT từ 20 tiêu đề gần nhất. Không đo được ⇒ 0.0
        # (cổng định dạng sẽ dựa vào chữ 漫画 trong tiêu đề video, không đoán bừa).
        ratio = ratio_cache.get(x.get("channel_id"))
        if ratio is None:
            ratio = 1.0 if re.search(MANGA_ANY, x["title"], re.I) else 0.0
        for lane in lanes:
            s = analyze.score(v, ch, lane, time.time(), channel_manga_ratio=ratio)
            s["lane"] = lane
            s["desc"] = ""
            s["web"] = x
            if s["ok"]:
                scored[lane].append(s)
            else:
                k = re.sub(r"[\d,\.]+", "N", s["reason"])[:55]
                rejects[k] = rejects.get(k, 0) + 1

    if rejects:
        log("  lý do loại: " + " · ".join(f"{k} ×{v}" for k, v in
                                        sorted(rejects.items(), key=lambda z: -z[1])[:8]))

    # tự học kênh mới
    added = set()
    wl = {r["channel_id"]: r for r in watchlist.active(conn)}
    for lane in lanes:
        for s in scored[lane]:
            cid = s["channel_id"]
            if cid and cid not in wl and cid not in added:
                watchlist.upsert(conn, cid, s["channel"], s["subs"], lane,
                                 s.get("manga_ratio", 0), "auto_learn")
                added.add(cid)
    if added:
        log(f"  tự học: +{len(added)} kênh mới vào watchlist")

    for lane in lanes:
        scored[lane].sort(key=lambda z: -z["score"])
        log(f"  lane {lane}: {len(scored[lane])} video qua lọc, top "
            + (", ".join(f"{z['score']}({z['grade']})" for z in scored[lane][:4]) or "—"))

    # ---------------------------------------------------------- 4. chống lặp
    done = state.already_reported(conn, [z["video_id"] for l in lanes for z in scored[l]])
    for lane in lanes:
        before = len(scored[lane])
        scored[lane] = [z for z in scored[lane] if z["video_id"] not in done]
        if before != len(scored[lane]):
            log(f"  lane {lane}: loại {before - len(scored[lane])} video đã báo cáo")

    # ---------------------------------------------------------- 5. chọn 2/lane
    lanes_result, chosen = {}, set()
    for lane in lanes:
        picked = []
        for z in scored[lane]:
            if len(picked) >= a.per_lane:
                break
            if z["video_id"] in chosen:
                continue
            picked.append(z)
            chosen.add(z["video_id"])
        lanes_result[lane] = {"picked": picked, "borrowed": False}

    for lane in lanes:
        need = a.per_lane - len(lanes_result[lane]["picked"])
        if need <= 0:
            continue
        pool, seen_local = [], {z["video_id"] for z in lanes_result[lane]["picked"]}
        for other in lanes:
            if other == lane:
                continue
            for z in scored[other]:
                if z["video_id"] in seen_local:
                    continue
                alt = analyze.score({"id": z["video_id"],
                                     "snippet": {"title": z["title"], "channelId": z["channel_id"],
                                                 "channelTitle": z["channel"], "description": "",
                                                 "publishedAt": ""},
                                     "statistics": {"viewCount": z["views"]},
                                     "contentDetails": {"seconds": z["sec"],
                                                        "age_days": z.get("days_old")},
                                     "status": {"privacyStatus": "public"}},
                                    {"statistics": {"subscriberCount": z["subs"]}},
                                    lane, time.time(),
                                    channel_manga_ratio=z.get("manga_ratio", 0))
                if alt.get("ok") and alt["score"] >= 6.0:
                    alt["lane"] = lane
                    alt["borrowed_from"] = other
                    alt["desc"] = ""
                    alt["web"] = z.get("web", {})
                    pool.append(alt)
                    seen_local.add(z["video_id"])
        pool.sort(key=lambda z: (z["video_id"] in chosen, -z["score"]))
        # BẪY ĐÃ GÂY LỖI THẬT 2026-10-20: `pool[:need]` KHÔNG kiểm lại `chosen` lần nữa.
        # Video `y8iPHPXVWtI` đã được lane N lấy, nhưng vòng mượn của lane M vẫn nhặt lại
        # (pool chỉ có 1 phần tử nên `pool[:1]` lấy luôn) ⇒ 1 video nguồn sinh 2 đề.
        # Đã thấy trong báo cáo VIRAL_2026-10-20_lan2: 7 đề nhưng chỉ 6 video unique.
        added_here = 0
        for z in pool:
            if added_here >= need:
                break
            if z["video_id"] in chosen:
                continue
            lanes_result[lane]["picked"].append(z)
            lanes_result[lane]["borrowed"] = True
            chosen.add(z["video_id"])
            added_here += 1

    for lane in lanes:
        picked = lanes_result[lane]["picked"]
        lanes_result[lane].update({
            "scanned": len(raw), "candidates": len(scored[lane]),
            "note": "" if picked else ("Không có video nào khớp công thức lane này trong "
                                       f"{days} ngày — thực tế thị trường, không phải lỗi tool. "
                                       "Xem mục 2 để biết video đang nổ ngoài ngách."),
        })

    # ---------------------------------------------------------- 6. đề bài
    for lane in lanes:
        for p in lanes_result[lane]["picked"]:
            if a.no_llm:
                p["draft"] = analyze.draft(p, lane, use_llm=False)
            else:
                try:
                    p["draft"] = analyze.draft(p, lane, use_llm=True)
                    log(f"  đề {lane}/{p['video_id']}: {p['draft'].get('nguon')}")
                except Exception as e:                        # noqa: BLE001
                    p["draft"] = analyze.draft(p, lane, use_llm=False)
                    log(f"  !! draft {lane}/{p['video_id']}: {type(e).__name__} {e}")

    # ---------------------------------------------------------- 7. xuất
    # LUẬT 2026-10-19: MỌI chuỗi tiếng Nhật trong báo cáo phải có bản dịch Việt.
    # Gom hết chuỗi cần dịch rồi dịch 1 lượt (theo lô), trước khi dựng HTML.
    to_tr = []
    for lane in lanes:
        L = LANES[lane]
        to_tr += [L["channel"], L["handle"]]
        for p in lanes_result[lane]["picked"]:
            to_tr += [p.get("title", ""), p.get("channel", "")]
            d = p.get("draft") or {}
            to_tr += [d.get("title_jp", ""), d.get("thumbnail_jp", ""), d.get("cau_hoi_cuoi", "")]
    # BẪY 2026-10-19: bảng xếp hạng mục 2 in tiêu đề của MỌI ứng viên đã chấm (không chỉ 8 đề
    # được chọn). Không đưa chúng vào đây thì báo cáo còn tiếng Nhật trần — đã bị anh bắt lỗi.
    for lane in lanes:
        for z in scored[lane][:12]:
            to_tr.append(z.get("title", ""))
    log(f"  dịch {len([x for x in set(to_tr) if x and translate.has_jp(x)])} chuỗi tiếng Nhật…")
    translations = translate.translate_many(to_tr)
    terr = translations.pop("_error", None)
    if terr:
        log(f"  !! dịch lỗi: {terr}")
    n_tr = sum(1 for k, v in translations.items() if v and v != k)
    log(f"  dịch xong: {n_tr} chuỗi có bản Việt")

    all_scored = []
    for lane in lanes:
        for z in scored[lane][:12]:
            all_scored.append({**{k: z[k] for k in ("video_id", "lane", "grade", "score",
                                                    "views", "views_per_hour", "subs",
                                                    "mins", "title")},
                               "chosen": z["video_id"] in chosen})
    meta = {"units": enrich.status()["units"] if api_on else 0,
            "api": enrich.status(),
            "errors": [], "finished": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "all_scored": all_scored, "history": state.recent_days(conn, 14),
            "watchlist": watchlist.stats(conn), "scanned": len(raw),
            "keywords": len(jobs), "kw_errors": kw_err,
            "threads": threads, "pages": pages,
            "script_path": os.path.abspath(__file__),
            "translations": translations}
    paths = cfg.get("paths") or {}
    results_dir = paths.get("results_dir", r"E:\CLAUDE\YOUTUBE\FlowHandoff_local\results")
    reports_dir = paths.get("reports_dir", os.path.join(ROOT, "reports", "viral_hunt"))

    if a.dry_run:
        txt = report.build(day, lanes_result, meta)
        log(f"  [dry-run] HTML {len(txt):,} ký tự — không ghi file, không ghi state")
        p_local = p_sync = p_jobs = None
    else:
        # Đường dẫn ĐẦY ĐỦ phải có TRƯỚC khi dựng HTML (luật 2026-10-19: không cắt gọn).
        # Tên file do report.write quyết định (_lan2 nếu đã có bản trong ngày) nên tính trước.
        import report as _rp
        p_sync_pre = _rp.next_free_path(results_dir, f"VIRAL_{day}", ".html") if os.path.isdir(results_dir) else None
        p_local_pre = _rp.next_free_path(os.path.join(reports_dir, day), f"VIRAL_{day}", ".html")
        meta["paths"] = {
            "Báo cáo — mở từ MÁY 1": sheet_note.path_for_may1(p_sync_pre),
            "Báo cáo — trên MÁY 2 (máy chạy tool)": p_sync_pre or "(không ghi được — thư mục results không tồn tại)",
            "Bản máy đọc (jobs.json) — máy 2": os.path.splitext(p_local_pre)[0] + ".jobs.json",
        }
        p_local, p_sync, p_jobs = report.write(day, lanes_result, meta, results_dir, reports_dir)
        for lane in lanes:
            state.mark_reported(conn, [{**p, "day": day} for p in lanes_result[lane]["picked"]])
        state.mark_seen(conn, [(z["video_id"], z["lane"], z["title"])
                               for l in lanes for z in scored[l]])
        state.log_run(conn, day, True, len(raw),
                      sum(len(v["picked"]) for v in lanes_result.values()), 0,
                      f"keywords={len(jobs)} threads={threads}")

        # ---- LUẬT 2026-10-19: đường dẫn báo cáo -> tab NOTE ô C21 (khoá cố định, đè mỗi ngày)
        # Ghi đường dẫn NHÌN TỪ MÁY 1 (E:\CLAUDE\YOUTUBE\h2dev\FlowHandoff_local\results\...),
        # vì anh mở file trên máy 1. Máy 2 ghi file thật ở E:\CLAUDE\YOUTUBE\FlowHandoff_local\results.
        try:
            local_target = p_sync or p_local
            may1_target = sheet_note.path_for_may1(local_target)
            ok, msg = sheet_note.write_report_path(may1_target)
            log(("  NOTE!C21: " if ok else "  !! NOTE!C21 LỖI: ") + msg)
            log(f"    (file thật trên máy 2: {local_target})")
            meta["note_cell"] = {"ok": ok, "msg": msg,
                                 "path_may1": may1_target, "path_may2": local_target}
        except Exception as e:                                # noqa: BLE001
            log(f"  !! NOTE!C21 LỖI KHÔNG GHI ĐƯỢC: {type(e).__name__} {e}")
            meta["note_cell"] = {"ok": False, "msg": f"{type(e).__name__}: {e}"}

    tot = sum(len(v["picked"]) for v in lanes_result.values())
    log(f"--- XONG: {tot} đề / {len(lanes)} lane · quét {len(raw)} video · "
        f"{len(jobs)} từ khoá · {meta.get('units', 0)} unit quota · {time.time() - t0:.0f}s")
    for p in (p_sync, p_local, p_jobs):
        if p:
            log(f"    {p}")
    return 0 if tot else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                                          # noqa: BLE001
        print("LỖI KHÔNG MONG ĐỢI:\n" + traceback.format_exc())
        sys.exit(1)
