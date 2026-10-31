# -*- coding: utf-8 -*-
r"""
SO LIEU THEO NGAY (CURRENT_HEALTH 24/48/72h) cho 1 video — theo YOUTUBE_24H_48H_72H_RECOVERY_SOP.txt.

Vi sao can: CTR lifetime KHONG noi video con song hay khong. Vet xe do 2026-09-23: Valentich
(itNs2a3zJmQ) CTR lifetime 2.6% "dat", nhung tu 17/09 moi ngay 1-3 impressions, 0 view.

Nguon: Studio Advanced mode, dimension=DAY (bang xep ngay moi nhat truoc). Hom nay Studio chua co
so ("still processing") -> "24h gan nhat" = ngay DU SO moi nhat co trong bang.
"""
import re, json, time, datetime, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import human_pace as hp

TABLE_URL = ("https://studio.youtube.com/video/{vid}/analytics/tab-reach_viewers/period-default/explore?"
             "entity_type=VIDEO&entity_id={vid}&time_period=4_weeks&explore_type=TABLE_AND_CHART"
             "&metric=VIDEO_THUMBNAIL_IMPRESSIONS&granularity=DAY"
             "&t_metrics=VIDEO_THUMBNAIL_IMPRESSIONS&t_metrics=VIDEO_THUMBNAIL_IMPRESSIONS_VTR"
             "&t_metrics=EXTERNAL_VIEWS&dimension=DAY&o_column=DAY"
             "&o_direction=ANALYTICS_ORDER_DIRECTION_DESC")

DATE_RE = re.compile(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}$")
MARK_CTR = 2.5  # luat anh chot: CTR 24h < 2.5% (hoac khong co) -> "CAN THAY DOI"
SKIP_VIEWS = 1000  # video > 1000 view lifetime: tam CHUA xet thay tieu de/thumbnail (anh chot 2026-09-23)

COLUMNS = ["last_data_day",
           "impressions_last_24h", "ctr_last_24h", "views_last_24h",
           "impressions_previous_24h", "ctr_previous_24h", "views_previous_24h",
           "impressions_last_48h", "ctr_last_48h", "views_last_48h",
           "impressions_last_72h", "ctr_last_72h", "views_last_72h",
           "peak_day_impressions", "distribution_change_pct", "current_distribution_status",
           "mark_needed",
           "packaging_version", "packaging_changed_at", "description_version",
           "post_change_impressions_24h", "post_change_ctr_24h",
           "post_change_impressions_48h", "post_change_ctr_48h",
           "daily_series"]


def _n(t):
    """'1,234' -> 1234.0 ; '2.5%' -> 2.5 ; '—' -> None"""
    t = (t or "").strip().replace(",", "").replace("%", "")
    try:
        return float(t)
    except ValueError:
        return None


def parse_table(parts):
    """Tu mang text DEEP -> {date: (impr, ctr, views)}. Cot theo thu tu t_metrics: impr, CTR, views.
    Moi dong: ngay, impr, ctr, views, %views (dong Total khong co %)."""
    if "Total" not in parts:
        return {}
    i = max(k for k, t in enumerate(parts) if t == "Total")
    rows, k = {}, i + 4
    while k < len(parts):
        t = parts[k].strip()
        if DATE_RE.match(t):
            d = datetime.datetime.strptime(t, "%b %d, %Y").date()
            vals = parts[k + 1:k + 4]
            rows[d] = (_n(vals[0]) or 0.0, _n(vals[1]), _n(vals[2]) or 0.0)
            k += 4
        else:
            k += 1
    return rows


RANGE_RE = re.compile(r"^([A-Z][a-z]{2})[\s\u00a0\u2009\u202f]+\d{1,2}[\s\u00a0\u2009\u202f]*[–\-][\s\u00a0\u2009\u202f]*(?:([A-Z][a-z]{2})[\s\u00a0\u2009\u202f]+)?(\d{1,2}),[\s\u00a0\u2009\u202f]*(\d{4})$")


def report_end_day(parts):
    """Ngay cuoi cua khoang bao cao ("Aug 26 – Sep 22, 2026" / "Sep 14 – 22, 2026").
    BAT BUOC dung ngay nay: ngay 0 impressions bi Studio BO KHOI BANG, lay max(rows) thi video
    im lang hom qua bi tinh "24h gan nhat" la hom kia (dinh that: k1zQl6xqSXY, 2026-09-23)."""
    for t in parts:
        m = RANGE_RE.match(t.strip())
        if m:
            mon = m.group(2) or m.group(1)
            return datetime.datetime.strptime("%s %s %s" % (mon, m.group(3), m.group(4)), "%b %d %Y").date()
    return None


def _window(rows, days):
    """Cong impressions/views; CTR = tong click uoc tinh / tong impressions (co trong so)."""
    imp = sum(rows.get(d, (0, None, 0))[0] for d in days)
    views = sum(rows.get(d, (0, None, 0))[2] for d in days)
    clicks = sum((rows[d][0] * (rows[d][1] or 0) / 100) for d in days if d in rows)
    ctr = round(clicks / imp * 100, 2) if imp else None
    return int(imp), ctr, int(views)


def status(lifetime_imp, last24, prev24, last48, change):
    """Trang thai distribution theo muc 4 + rule engine muc 20 cua SOP recovery."""
    if lifetime_imp < 100:
        return "NOT_TESTED"
    if lifetime_imp < 300:
        return "EARLY_TEST"
    if last48 <= 20:
        return "NEAR_DEAD"
    if change is None:
        return "STABLE" if last24 else "STALLED"
    if change <= -70:
        return "SHARP_DROP"
    if change <= -30:
        return "DECLINING"
    return "EXPANDING" if change >= 10 else "STABLE"


def collect_daily(page, vid, deep_js, lifetime_imp, hours_since_publish, lifetime_views=None):
    """Doc bang so theo ngay — bang CLICK nhu nguoi that (khong goto URL Advanced).

    Nguoi that: trong trang video da mo -> bam "Advanced mode" -> bam "Reach" (neu can)
    -> doi khoang thoi gian -> chon dimension "Ngay" -> doc bang.

    BAY (do that 2026-10-18): lan goto DAU vao bang theo ngay hay dung o trang TRANG
    (246 text, co chu "Total" nhung khong co dong nao; chi hien 1 khoi
    "Oops, something went wrong") — cho them 60s VAN KHONG ra. RELOAD thi 12s la co 23 dong.
    Vi vay phai reload khi rong, khong duoc chi tang thoi gian cho.

    Neu khong bam duoc Advanced mode (trang doi khac) -> tra NO_DAILY_DATA, KHONG goto URL.
    """
    import studio_human as sh
    hp.before_click()
    if not sh.click_label(page, "Advanced mode", log=None, why="Advanced mode"):
        out = {c: "" for c in COLUMNS}
        out["current_distribution_status"] = "NO_DAILY_DATA"
        return out
    sh.wait_url(page, "/explore", tries=15)
    hp.wander(page)

    parts, rows = [], {}
    for attempt in range(3):
        for _ in range(8):
            time.sleep(3 * random.uniform(0.8, 1.3))
            parts = page.evaluate(deep_js)
            rows = parse_table(parts)
            if rows:
                time.sleep(3)
                parts = page.evaluate(deep_js)
                rows = parse_table(parts) or rows
                break
        if rows:
            break
        hp.after_oops()             # trang trang/Oops -> doi lau nhu nguoi bo di lam viec khac
        page.reload(wait_until="domcontentloaded", timeout=90000)
    hp.wander(page)
    return summarize(rows, report_end_day(parts), lifetime_imp, hours_since_publish, lifetime_views)


def summarize(rows, end_day, lifetime_imp, hours_since_publish, lifetime_views=None):
    out = {c: "" for c in COLUMNS}
    if not rows:
        out["current_distribution_status"] = "NO_DAILY_DATA"
        return out

    last = max(end_day or max(rows), max(rows))
    day = lambda n: last - datetime.timedelta(days=n)
    l24, p24 = _window(rows, [last]), _window(rows, [day(1)])
    l48, l72 = _window(rows, [last, day(1)]), _window(rows, [last, day(1), day(2)])
    change = round((l24[0] - p24[0]) / p24[0] * 100, 1) if p24[0] else None

    out["last_data_day"] = last.isoformat()
    for pre, w in (("last_24h", l24), ("previous_24h", p24), ("last_48h", l48), ("last_72h", l72)):
        out["impressions_" + pre], out["ctr_" + pre], out["views_" + pre] = w
    out["peak_day_impressions"] = int(max(v[0] for v in rows.values()))
    out["distribution_change_pct"] = "" if change is None else change
    out["current_distribution_status"] = status(lifetime_imp or 0, l24[0], p24[0], l48[0], change)
    # Luat anh chot 2026-09-23 (video >= 48h):
    #   24h gan nhat 0 VIEW          -> THUMB        (chi cot G, tieu de E GIU NGUYEN)
    #   co view nhung CTR 24h < 2.5% -> TITLE+THUMB  (cot E + G); CTR "—" = 0
    #   tong view lifetime > 1000     -> BO_QUA_1000 (tam chua xet, anh se nhac khi can)
    ctr24 = l24[1] or 0.0
    old = hours_since_publish not in ("", None) and float(hours_since_publish) >= 48
    if lifetime_views and float(lifetime_views) > SKIP_VIEWS:
        out["mark_needed"] = "BO_QUA_1000"
    elif not old:
        out["mark_needed"] = "CHUA_48H"
    elif l24[2] == 0:
        out["mark_needed"] = "THUMB"
    else:
        out["mark_needed"] = "TITLE+THUMB" if ctr24 < MARK_CTR else "NO"
    out["daily_series"] = json.dumps({d.isoformat(): [int(v[0]), v[1], int(v[2])]
                                      for d, v in sorted(rows.items())}, separators=(",", ":"))
    return out
