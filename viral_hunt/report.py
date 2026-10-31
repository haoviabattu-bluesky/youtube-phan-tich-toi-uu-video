# -*- coding: utf-8 -*-
"""report.py — dựng báo cáo HTML hằng ngày, cùng skin với BAO_CAO_WIN_LANE_*.html.

Ghi 3 nơi:
  E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results\\VIRAL_<YYYY-MM-DD>.html   ← Syncthing 'results'
      (sendonly máy 1 ⇒ tự sang máy 2 / h2dev đọc)
  reports\\viral_hunt\\<YYYY-MM-DD>\\VIRAL_<YYYY-MM-DD>.html                 ← lưu máy này
  reports\\viral_hunt\\<YYYY-MM-DD>\\jobs.json                               ← bản máy đọc, không cần parse HTML
"""
import html
import json
import os

from lanes import LANES
from analyze import LADDER

GRADE_LABEL = {
    "A": ("A · đúng luật", "w"),
    "B": ("B · nới view", "m"),
    "C": ("C · nới sub", "m"),
    "D": ("D · nới ngày", "m"),
    "E": ("E · nới rộng", "l"),
}

CSS = """
:root{--bg:#fbfaf7;--fg:#1f2328;--mut:#5b6470;--line:#e3e0d8;--card:#fff;--win:#1a7f37;--winbg:#e8f5ec;--lose:#b42318;--losebg:#fdecea;--mid:#9a6700;--midbg:#fff6dd;--acc:#2f5bd3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#16181c;--fg:#e6e6e6;--mut:#9aa3ad;--line:#2d3138;--card:#1d2026;--win:#4ac26b;--winbg:#14301d;--lose:#ff7b72;--losebg:#3a1a1a;--mid:#e3b341;--midbg:#352a10;--acc:#7aa2ff}}
:root[data-theme="dark"]{--bg:#16181c;--fg:#e6e6e6;--mut:#9aa3ad;--line:#2d3138;--card:#1d2026;--win:#4ac26b;--winbg:#14301d;--lose:#ff7b72;--losebg:#3a1a1a;--mid:#e3b341;--midbg:#352a10;--acc:#7aa2ff}
body{background:var(--bg);color:var(--fg);font:15px/1.65 system-ui,"Segoe UI","Yu Gothic UI","Meiryo",sans-serif;margin:0}
main{max-width:1080px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:20px;margin:36px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--line)}h3{font-size:16px;margin:22px 0 6px}
.sub{color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.tl{border-left:5px solid var(--win)}.tl.bad{border-left-color:var(--lose)}.tl.mid{border-left-color:var(--mid)}
.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card)}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--bg);font-weight:600;white-space:nowrap}
td.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.w{background:var(--winbg)}.l{background:var(--losebg)}.m{background:var(--midbg)}
.tag{display:inline-block;font-size:12px;font-weight:700;padding:1px 8px;border-radius:99px}
.tag.w{color:var(--win)}.tag.l{color:var(--lose)}.tag.m{color:var(--mid)}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:22px}.kpi span{color:var(--mut);font-size:12.5px}
.jp{font-family:"Yu Gothic UI","Meiryo",sans-serif}
.vi{color:var(--acc);font-style:italic}
code{background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:12.5px}
ul,ol{padding-left:22px}li{margin:3px 0}
.bar{height:10px;background:var(--acc);border-radius:3px;display:inline-block;vertical-align:middle}
.note{font-size:13px;color:var(--mut)}
a{color:var(--acc)}
"""


def _e(x):
    return html.escape("" if x is None else str(x))


def _jp(orig, tr):
    """In chuỗi Nhật kèm bản dịch Việt. LUẬT 2026-10-19: không được để tiếng Nhật trần.

    orig = bản gốc tiếng Nhật (máy 1 cần để đăng), tr = bản dịch Việt.
    Nếu thiếu bản dịch thì ghi rõ "[chưa dịch được]" — KHÔNG im lặng bỏ qua, KHÔNG bịa.
    """
    if not orig:
        return "—"
    if not tr or tr == orig:
        return f'<span class="jp">{_e(orig)}</span> <span class="tag l">chưa dịch được</span>'
    return (f'<span class="jp">{_e(orig)}</span>'
            f'<br><span class="vi">→ {_e(tr)}</span>')


def _handle(h, tr):
    """Handle kênh: @shakai-no-naze (romaji) giữ nguyên; @人生のつづき (có chữ Nhật) phải dịch."""
    if not h:
        return "—"
    import re as _re
    if not _re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", h):
        return f'<span class="jp">{_e(h)}</span>'
    return _jp(h, tr.get(h))


def _n(x, d=0):
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _grade_tag(g):
    lab, cls = GRADE_LABEL.get(g, ("?", "l"))
    return f'<span class="tag {cls}">{_e(lab)}</span>'


def _score_bar(s):
    w = max(4, min(160, int(float(s) * 8)))
    return f'<span class="bar" style="width:{w}px"></span> {_e(s)}'


def build(day, lanes_result, meta):
    """lanes_result: {lane: {"picked": [...], "scanned": int, "candidates": int, "note": str}}

    meta["translations"] = {chuỗi Nhật: nghĩa Việt} — LUẬT 2026-10-19: mọi chuỗi tiếng Nhật
    trong báo cáo PHẢI có bản dịch Việt. Không có bản dịch thì in "[chưa dịch được]", không bỏ qua.
    """
    tr = meta.get("translations") or {}
    tot = sum(len(v["picked"]) for v in lanes_result.values())
    # số video ĐÃ QUÉT = tổng id lấy từ watchlist + web search (meta), không cộng theo lane
    # (mỗi video được chấm cho nhiều lane nên cộng theo lane là sai — đã ghi "Quét 12 video"
    # trong khi thực tế 547).
    scanned = meta.get("scanned") or sum(v["scanned"] for v in lanes_result.values())
    units = meta.get("units", 0)
    nA = sum(1 for v in lanes_result.values() for p in v["picked"] if p["grade"] == "A")
    nB = sum(1 for v in lanes_result.values() for p in v["picked"] if p["grade"] == "B")
    nC = sum(1 for v in lanes_result.values() for p in v["picked"] if p["grade"] == "C")

    out = ['<!doctype html><html lang="vi"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           f'<title>Video viral {day}</title><style>{CSS}</style></head><body><main>']

    out.append(f"<h1>Video nguồn đang nổ — {day}</h1>")
    out.append('<div class="sub">Tool <code>viral_hunt</code> · lập tự động 03:00 · '
               f'nguồn: quét trang kết quả YouTube ({_n(meta.get("keywords", 0))} từ khoá × '
               f'{meta.get("pages", "?")} trang), KHÔNG dùng YouTube Data API</div>')
    out.append('<div class="sub">Gửi máy 1 / h2dev: mỗi lane dưới đây là đề bài lấy từ MỘT video nguồn '
               'đang nổ, đã đối chiếu công thức WIN của chính lane đó '
               '(<code>BAO_CAO_WIN_LANE_*_2026-10-16.html</code>). '
               'Video nào đã báo cáo thì không bao giờ xuất hiện lại.</div>')

    out.append('<h2>0. Tóm tắt lượt chạy</h2><div class="kpi">')
    out.append(f'<div><b>{tot}</b><span>đề bài đưa ra (mục tiêu 2/lane)</span></div>')
    out.append(f'<div><b>{nA} / {nB} / {nC}</b><span>hạng A / B / C</span></div>')
    out.append(f'<div><b>{_n(scanned)}</b><span>video đã quét &amp; chấm điểm</span></div>')
    out.append(f'<div><b>{_n(units)}</b><span>unit quota đã dùng</span></div>')
    out.append('</div>')

    # ngưỡng
    out.append('<div class="card tl mid"><b>Thang ngưỡng (thác nước — mỗi bậc chỉ nới MỘT trục)</b>'
               '<table style="margin-top:8px"><tr><th>Bậc</th><th>View tối thiểu</th>'
               '<th>Sub kênh</th><th>Tuổi video</th><th>Ý nghĩa</th></tr>')
    for g, vmin, dmax, label in LADDER:
        out.append(f'<tr><td><b>{g}</b></td><td class="n">≥ {_n(vmin)}</td>'
                   f'<td class="n">&lt; 10.000 (cố định)</td><td class="n">≤ {dmax} ngày</td>'
                   f'<td>{_e(label.split("·", 1)[1].strip() if "·" in label else label)}</td></tr>')
    out.append("</table>")
    out.append('<div class="note" style="margin-top:8px">Đo ngày 2026-10-18: quét 392 video manga '
               'đăng trong 7 ngày của cả thị trường Nhật, chỉ <b>1 video</b> đạt đủ bậc A và khớp '
               'ngách 4 lane. Nếu cứng bậc A thì phần lớn các ngày sẽ trắng ⇒ tool lấy bậc cao nhất '
               'có sẵn, ghi rõ bậc trên từng đề. Muốn cứng: <code>--ladder A</code> '
               '(hoặc <code>--min-views 100000</code>).</div></div>')

    # từng lane
    out.append("<h2>1. Đề bài theo lane</h2>")
    for lane in ("L", "N", "O", "M"):
        r = lanes_result.get(lane) or {"picked": [], "scanned": 0, "candidates": 0, "note": ""}
        L = LANES[lane]
        out.append(f'<h3>Lane {lane} — {_jp(L["channel"], tr.get(L["channel"]))} '
                   f'<span class="sub">({_handle(L["handle"], tr)} · '
                   f'tab <code>{_e(L["tab"])}</code>)</span></h3>')
        out.append(f'<div class="card tl"><b>Công thức WIN đang áp:</b> {_e(L["win_one_line"])}</div>')
        if not r["picked"]:
            out.append(f'<div class="card tl bad"><b>Không có đề hôm nay.</b> '
                       f'Đã quét {_n(r["scanned"])} video, {_n(r["candidates"])} video qua lọc cứng, '
                       f'nhưng không video nào đạt điểm tối thiểu. {_e(r.get("note", ""))}</div>')
            continue
        for idx, p in enumerate(r["picked"], 1):
            d = p["draft"]
            borrow = (f' <span class="tag m">mượn từ lane {_e(p["borrowed_from"])}</span>'
                      if p.get("borrowed_from") else "")
            out.append(f'<div class="card tl{" bad" if p["grade"] in ("E",) else ""}">')
            out.append(f'<div><b>Đề {idx}</b> &nbsp; {_grade_tag(p["grade"])}{borrow} &nbsp; '
                       f'<span class="sub">điểm khớp công thức {_score_bar(p["score"])}</span></div>')
            out.append(f'<div><b>Video nguồn:</b> <a href="https://www.youtube.com/watch?v={_e(p["video_id"])}">'
                       f'{_jp(p["title"], tr.get(p["title"]))}</a></div>')
            out.append(f'<div class="sub">Kênh {_jp(p["channel"], tr.get(p["channel"]))} · {_n(p["subs"])} sub · '
                       f'{_n(p["views"])} view trong {p["hours"]:.0f} giờ '
                       f'(<b>{_n(p["views_per_hour"])} view/giờ</b>) · {_n(p["likes"])} like · '
                       f'{_n(p["comments"])} bình luận · dài {p["mins"]:.0f} phút · '
                       f'đăng {_e(str(p["published"])[:10])}</div>')
            if p.get("manga_ratio"):
                out.append(f'<div class="sub">Kênh nguồn: {int(p["manga_ratio"] * 100)}% tiêu đề gần đây là manga</div>')
            if p.get("subs_unknown"):
                out.append('<div class="sub">⚠ <b>Sub chưa rõ</b> — YouTube không hiển thị số sub của kênh này '
                           '(kênh mới hoặc để riêng tư). Đã trừ 3 điểm khi xếp hạng. '
                           'Anh tự quyết có dùng hay không.</div>')

            out.append('<table><tr><th style="width:170px">Mục</th><th>Nội dung</th></tr>')
            rows = [
                ("Vì sao nổ", d.get("vi_sao_thang")),
                ("Đề bài tập mới", d.get("de_bai")),
                ("Khác nguồn ở đâu", d.get("khac_nguon")),
                ("Hook 3 câu đầu", d.get("hook_3cau")),
                ("Tiêu đề tiếng Nhật (để đăng)", d.get("title_jp")),
                ("Chữ trên thumbnail (tiếng Nhật)", d.get("thumbnail_jp")),
                ("Số liệu phải có", d.get("so_lieu_can")),
                ("Câu hỏi cuối", d.get("cau_hoi_cuoi")),
                ("Rủi ro", d.get("rui_ro")),
            ]
            for k, v in rows:
                if isinstance(v, list):
                    v = "<br>".join("• " + _e(x) for x in v) if v else "—"
                elif v is None or v == "":
                    v = "—"
                else:
                    v = _e(v)
                # LUẬT 2026-10-19: mọi chuỗi tiếng Nhật phải kèm bản dịch Việt
                if k.startswith("Tiêu đề tiếng Nhật") or k.startswith("Chữ trên thumbnail"):
                    v = _jp(d.get("title_jp" if "Tiêu đề" in k else "thumbnail_jp"),
                            tr.get(d.get("title_jp" if "Tiêu đề" in k else "thumbnail_jp")))
                out.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
            out.append("</table>")
            if d.get("nguon") != "llm" and str(d.get("nguon", "")).startswith("llm") is False:
                out.append(f'<div class="note">⚠ Đề bài sinh bằng khung xương (không có LLM): '
                           f'{_e(d.get("loi"))}</div>')
            out.append("</div>")
        if r.get("note"):
            out.append(f'<div class="note">{_e(r["note"])}</div>')

    # bảng xếp hạng tất cả ứng viên đã chấm (để anh tự xem có gì khác)
    out.append("<h2>2. Ứng viên đã chấm (xếp theo điểm)</h2>")
    out.append('<div class="note">Chỉ hiện video qua lọc cứng (kênh &lt;10k sub, manga, 5–45 phút). '
               'Dòng xanh = đã chọn làm đề. "—" = đã báo cáo ở lần trước nên bị loại.</div>')
    out.append('<div class="wrap"><table><tr><th>#</th><th>Lane</th><th>Hạng</th><th>Điểm</th>'
               '<th>View</th><th>View/giờ</th><th>Sub</th><th>Phút</th><th>Tiêu đề nguồn</th></tr>')
    rank = sorted(meta.get("all_scored", []), key=lambda x: -x["score"])[:40]
    for i, p in enumerate(rank, 1):
        chosen = " class=\"w\"" if p.get("chosen") else ""
        out.append(f'<tr{chosen}><td class="n">{i}</td><td>{_e(p["lane"])}</td>'
                   f'<td>{_grade_tag(p["grade"])}</td><td class="n">{_e(p["score"])}</td>'
                   f'<td class="n">{_n(p["views"])}</td><td class="n">{_n(p["views_per_hour"])}</td>'
                   f'<td class="n">{_n(p["subs"])}</td><td class="n">{p["mins"]:.0f}</td>'
                   f'<td><a href="https://www.youtube.com/watch?v={_e(p["video_id"])}">'
                   f'{_jp(p["title"], tr.get(p["title"]))}</a></td></tr>')
    out.append("</table></div>")

    # lịch sử
    hist = meta.get("history") or []
    if hist:
        out.append("<h2>3. Lịch sử báo cáo</h2><div class=\"wrap\"><table>"
                   "<tr><th>Ngày</th><th>Số video đã báo</th><th>Tổng view các video đó</th></tr>")
        for h in hist:
            out.append(f'<tr><td>{_e(h["day"])}</td><td class="n">{_n(h["n"])}</td>'
                       f'<td class="n">{_n(h["views"])}</td></tr>')
        out.append("</table></div>")

    out.append("<h2>4. Cách máy 1 / h2dev dùng báo cáo này</h2>")
    out.append('<div class="card"><ol>'
               '<li>Mỗi lane lấy tối đa <b>2 đề</b>, ưu tiên hạng A → B → C.</li>'
               '<li>Đọc mục "Đề bài tập mới" + "Hook 3 câu đầu" + "Tiêu đề JP" + "Chữ thumbnail JP".</li>'
               '<li>Đối chiếu lại <code>BAO_CAO_WIN_LANE_&lt;lane&gt;_2026-10-16.html</code> trước khi viết kịch bản.</li>'
               '<li>Chỗ ghi <code>[SỐ CẦN KIỂM]</code> là số CHƯA có nguồn — phải kiểm trước khi đưa vào kịch bản.</li>'
               '</ol></div>')
    # LUẬT 2026-10-19: đường dẫn phải ĐẦY ĐỦ TUYỆT ĐỐI, không cắt gọn.
    paths = meta.get("paths") or {}
    if paths:
        out.append('<div class="card tl"><b>Đường dẫn đầy đủ (copy nguyên dòng)</b>'
                   '<table style="margin-top:8px"><tr><th style="width:190px">File</th><th>Đường dẫn</th></tr>')
        for label, p in paths.items():
            if p:
                out.append(f'<tr><td>{_e(label)}</td><td><code>{_e(p)}</code></td></tr>')
        out.append("</table></div>")

    errs = meta.get("errors") or []
    if errs:
        out.append("<h2>5. Lỗi trong lượt chạy</h2><div class=\"card tl bad\"><ul>")
        for e in errs[:20]:
            out.append(f"<li>{_e(e)}</li>")
        out.append("</ul></div>")

    out.append(f'<div class="note" style="margin-top:28px">Sinh bởi '
               f'<code>{_e(meta.get("script_path") or "")}</code> lúc {_e(meta.get("finished", ""))}. '
               f'Quét {_n(scanned)} video · {_n(units)} unit quota.</div>')
    out.append("</main></body></html>")
    return "\n".join(out)


def jobs_payload(day, lanes_result, meta):
    """Bản cho máy đọc — không phải parse HTML."""
    out = {"day": day, "generated": meta.get("finished"), "thresholds": {
        "max_days": 5, "views_A": 100000, "views_B": 50000, "views_C": 30000,
        "max_subs": 10000, "manga": True},
        "lanes": {}}
    for lane, r in lanes_result.items():
        out["lanes"][lane] = {
            "channel": LANES[lane]["channel"],
            "tab": LANES[lane]["tab"],
            "win_one_line": LANES[lane]["win_one_line"],
            "scanned": r["scanned"],
            "jobs": [{
                "grade": p["grade"], "score": p["score"],
                "source": {"video_id": p["video_id"], "title": p["title"],
                           "channel": p["channel"], "subs": p["subs"], "views": p["views"],
                           "views_per_hour": p["views_per_hour"], "hours": p["hours"],
                           "published": p["published"],
                           "url": f"https://www.youtube.com/watch?v={p['video_id']}"},
                "draft": p["draft"],
            } for p in r["picked"]],
        }
    return out


def _free(base_dir, stem, ext):
    """Đường dẫn trống trong `base_dir`: tên gốc, nếu có rồi thì _lan2, _lan3…"""
    p = os.path.join(base_dir, f"{stem}{ext}")
    if not os.path.exists(p):
        return p
    n = 2
    while os.path.exists(os.path.join(base_dir, f"{stem}_lan{n}{ext}")):
        n += 1
    return os.path.join(base_dir, f"{stem}_lan{n}{ext}")


def next_free_path(base_dir, stem, ext):
    """Đường dẫn ĐẦY ĐỦ mà write() SẼ dùng (để in vào báo cáo trước khi ghi — luật 2026-10-19)."""
    if not base_dir:
        return None
    os.makedirs(base_dir, exist_ok=True)
    return _free(base_dir, stem, ext)


def write(day, lanes_result, meta, results_dir, reports_dir):
    html_txt = build(day, lanes_result, meta)
    payload = jobs_payload(day, lanes_result, meta)

    day_dir = os.path.join(reports_dir, day)
    os.makedirs(day_dir, exist_ok=True)

    # Không ghi đè báo cáo đã có trong ngày (chạy lại giữa ngày sẽ ra ít đề vì chống lặp,
    # ghi đè là mất bản đầy đủ). Bản thứ 2 trở đi ghi tên _lan2, _lan3…
    p_local = _free(day_dir, f"VIRAL_{day}", ".html")
    stem = os.path.splitext(os.path.basename(p_local))[0]
    p_jobs = os.path.join(day_dir, f"{stem}.jobs.json")
    open(p_local, "w", encoding="utf-8").write(html_txt)
    open(p_jobs, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=1))

    p_sync = None
    if results_dir and os.path.isdir(results_dir):
        p_sync = _free(results_dir, f"VIRAL_{day}", ".html")
        sstem = os.path.splitext(os.path.basename(p_sync))[0]
        open(p_sync, "w", encoding="utf-8").write(html_txt)
        open(os.path.join(results_dir, f"{sstem}.jobs.json"), "w",
             encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=1))
    return p_local, p_sync, p_jobs
