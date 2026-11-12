# -*- coding: utf-8 -*-
r"""
MAY 1: DOC CHI SO 3 LANE X, GEO, P KHI ANH MO MAY (anh chot 2026-10-31).

Khac may 2 (03:00, 11 nhom lane): may 1 chi chay 3 lane trong tools\daily_lanes_may1.json,
task May1DailyMetricsLogon kich 5 phut sau khi dang nhap Windows. Moi ngay chi chay 1 lan thanh cong
(lan dang nhap sau trong ngay -> bo qua); chay loi thi lan mo may sau chay lai.

Luong: daily_parallel.py (CUNG code may 2, chi doi file lane + thu muc log qua env) -> doc lai sheet
-> viet bao cao .md + .json cho du an YIE:
    E:\CLAUDE\YOUTUBE\YOUTUBE_INTELLIGENCE_ENGINE\inbox\may1\<ngay>.md  (+ LATEST.md, <ngay>.json)

KHONG truyen --scheduled cho daily_parallel: gio mo may anh co the dang dung profile -> giu bay #9
(profile ProfileUsingByOther thi BO QUA lane do, khong dong profile cua anh).

  py -3.13 tools\may1_logon_run.py --tab Lane-P --force          (chay that 1 lane, bo qua khoa 1 lan/ngay)
  py -3.13 tools\may1_logon_run.py --dry-run --force             (doc Studio, KHONG ghi sheet)
  py -3.13 tools\may1_logon_run.py --report-only                 (chi viet lai bao cao tu log hom nay)
  pythonw  tools\may1_logon_run.py --scheduled                   (task May1DailyMetricsLogon)

Thu xong (khong phai dry-run) -> goi YIE orchestrator/after_collector.py tach nen (chi X/GEO/P).
"""
import os, sys, re, json, time, argparse, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "view_spike"))
if sys.stdout is None or sys.stdout.__class__.__name__ == "NullWriter":
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")   # pythonw: khong co console
else:
    sys.stdout.reconfigure(encoding="utf-8")

LANES_FILE = os.path.join(HERE, "daily_lanes_may1.json")
SUBDIR = "may1_logon"
TODAY = datetime.date.today().isoformat()
RDIR = os.path.join(ROOT, "reports", SUBDIR)
LOGF = os.path.join(RDIR, f"{TODAY}.log")
DONE = os.path.join(RDIR, f"{TODAY}.done.json")
YIE_INBOX = r"E:\CLAUDE\YOUTUBE\YOUTUBE_INTELLIGENCE_ENGINE\inbox\may1"
YIE_ROOT = r"E:\CLAUDE\YOUTUBE\YOUTUBE_INTELLIGENCE_ENGINE"
YIE_AFTER = os.path.join(YIE_ROOT, "orchestrator", "after_collector.py")
LANE_NAME = {"X": "X — AINazotokiLab", "Lane-GEO": "GEO — @ai-kaimei-lab", "Lane-P": "P — 日本企業ウォッチ"}

ROW_RE = re.compile(r"^(?P<t>\d\d:\d\d:\d\d) (?:<[^>]+> )?\[(?P<tab>[^\]]+)\] dong (?P<row>\d+) (?P<vid>[\w-]{11}): "
                    r"N=(?P<N>\S*) O=(?P<O>\S*) P=(?P<P>\S*) Q=(?P<Q>\S*) imp24h=(?P<imp>\S*) \| (?P<flag>VANG|ok) \| K=(?P<K>.*)$")
ISSUE_RE = re.compile(r"\[(?P<tab>[^\]]+)\] (?P<msg>.*(LOI|bo qua|KHONG|khong).*)$")


def log(*a):
    line = time.strftime("%H:%M:%S ") + "[may1] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    os.makedirs(RDIR, exist_ok=True)
    with open(LOGF, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_log(start_off):
    """Chi doc phan log cua LAN CHAY NAY (tu byte start_off)."""
    rows, issues, summary = {}, [], []
    if not os.path.exists(LOGF):
        return rows, issues, summary
    with open(LOGF, "rb") as f:
        f.seek(start_off)
        text = f.read().decode("utf-8", "replace")
    for ln in text.splitlines():
        m = ROW_RE.match(ln)
        if m:
            d = m.groupdict()
            rows[(d["tab"], int(d["row"]))] = d      # doc 2 lan trong 1 run -> giu lan sau
            continue
        if "[may1]" in ln:
            continue
        if "===== XONG" in ln:
            summary.append(ln.split("===== XONG", 1)[1].strip(" :="))
        m = ISSUE_RE.search(ln)
        if m and "DA GHI SHEET" not in ln:
            issues.append((m["tab"], m["msg"].strip()))
        elif " LOI " in ln or "ProfileUsingByOther" in ln:
            issues.append(("-", ln[9:].strip()))
    return rows, issues, summary


def read_sheet(tabs):
    """{tab: [{row, stt, title, vid, N..S, K}]} cho moi dong co video_id o cot L."""
    import daily_sheet as dsh
    s = dsh.svc()
    out = {}
    for tab in tabs:
        try:
            vals, _ = dsh.read_tab(s, tab)
        except Exception as e:
            out[tab] = {"error": str(e)[:200]}; continue
        lst = []
        for i, r in enumerate(vals[1:], start=2):
            r = r + [""] * (19 - len(r))
            vid = r[11].strip()
            if len(vid) != 11:
                continue
            lst.append({"row": i, "stt": r[0], "title": (r[4].strip().splitlines() or [""])[0][:80], "vid": vid,
                        "N": r[13], "O": r[14], "P": r[15], "Q": r[16], "R": r[17], "S": r[18], "K": r[10].strip()})
        out[tab] = lst
    return out


def md_cell(x):
    return str(x if x not in (None, "") else "—").replace("|", "/").replace("\n", " ")


def write_report(tabs, start_off, rc, dry, t_start, t_end):
    rows, issues, summary = parse_log(start_off)
    sheet = read_sheet(tabs)
    data = {"machine": "may1", "date": TODAY, "started": t_start, "finished": t_end, "dry_run": dry,
            "exit_code": rc, "lanes": {}, "issues": [{"tab": t, "msg": m} for t, m in issues],
            "collector_log": LOGF, "summary": summary,
            "meaning": {"N": "so ngay tu khi dang", "O": "view tron doi (Studio)", "P": "CTR tron doi",
                        "Q": "CTR 24h gan nhat", "R": "view lan chay truoc", "S": "CTR 24h lan chay truoc",
                        "imp24h": "impressions 24h gan nhat", "flag": "VANG = to vang cot K (can xem lai)"}}
    L = [f"# Báo cáo chỉ số máy 1 — {TODAY}", "",
         f"- Máy: **máy 1** (chỉ lane X, GEO, P) · chạy {t_start} → {t_end}"
         f"{' · **DRY-RUN (không ghi sheet)**' if dry else ''} · exit {rc}",
         f"- Nguồn: YouTube Studio (Reach, Since published + Custom 24h) → Google Sheet `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` cột N–S, K",
         f"- Log collector: `{LOGF}`",
         "- Quy ước: ô `—` = chưa có dữ liệu (KHÔNG phải 0). N ngày · O view trọn đời · P CTR tổng · Q CTR 24h · R/S = O/Q lần chạy trước · imp24h = lượt hiển thị 24h.",
         "- `đọc hôm nay` = có = Studio đọc được ở lần chạy này; không = số trên sheet là của lần trước.", ""]
    for tab in tabs:
        lst = sheet.get(tab)
        L.append(f"## {LANE_NAME.get(tab, tab)} (tab `{tab}`)"); L.append("")
        lane = {"tab": tab, "videos": []}
        if isinstance(lst, dict):
            L += [f"Lỗi đọc sheet: {lst['error']}", ""]; lane["error"] = lst["error"]
        elif not lst:
            L += ["Chưa có video_id ở cột L → chưa có gì để đo.", ""]
        else:
            L.append("| Dòng | STT | video_id | Tiêu đề (sheet) | N | O | P | Q | R | S | imp24h | Cờ | đọc hôm nay | K |")
            L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for v in lst:
                lr = rows.get((tab, v["row"]))
                rec = {**v, "read_today": bool(lr), "imp24h": lr["imp"] if lr else None,
                       "flag": lr["flag"] if lr else None}
                if lr:   # dry-run khong ghi sheet -> lay so vua doc tu log
                    rec.update({k: lr[k] for k in ("N", "O", "P", "Q")})
                    rec["K"] = lr["K"]
                for k in ("N", "O", "P", "Q", "R", "S"):
                    if rec[k] in ("—", "None"):
                        rec[k] = ""
                lane["videos"].append(rec)
                L.append("| " + " | ".join(md_cell(x) for x in (
                    v["row"], v["stt"], v["vid"], v["title"], rec["N"], rec["O"], rec["P"], rec["Q"], rec["R"], rec["S"],
                    rec["imp24h"] if rec["imp24h"] not in ("None",) else "", "VÀNG" if rec["flag"] == "VANG" else (rec["flag"] or ""),
                    "có" if rec["read_today"] else "không", rec["K"])) + " |")
            n_ok = sum(1 for x in lane["videos"] if x["read_today"])
            n_y = sum(1 for x in lane["videos"] if x["flag"] == "VANG")
            L += ["", f"Đọc được {n_ok}/{len(lst)} video · {n_y} dòng vàng.", ""]
        data["lanes"][tab] = lane
    L.append("## Sự cố / bỏ qua"); L.append("")
    L += [f"- `{t}` {m}" for t, m in issues] or ["- Không có."]
    L += ["", "## Tóm tắt collector", ""] + ([f"- {x}" for x in summary] or ["- (không thấy dòng XONG trong log)"])
    md = "\n".join(L) + "\n"

    os.makedirs(YIE_INBOX, exist_ok=True)
    suffix = "_dryrun" if dry else ""
    for p, body in ((os.path.join(YIE_INBOX, f"{TODAY}{suffix}.md"), md),
                    (os.path.join(YIE_INBOX, f"{TODAY}{suffix}.json"), json.dumps(data, ensure_ascii=False, indent=1)),
                    (os.path.join(RDIR, f"{TODAY}{suffix}_BAO_CAO.md"), md)):
        open(p, "w", encoding="utf-8").write(body)
    if not dry:
        open(os.path.join(YIE_INBOX, "LATEST.md"), "w", encoding="utf-8").write(md)
    log("da viet bao cao:", os.path.join(YIE_INBOX, f"{TODAY}{suffix}.md"))
    return data


def call_yie(rc):
    """Thu xong -> goi YIE (tach nen, khong cho): YIE CHI phan tich X/GEO/P, viet bao cao goi y
    tieu de/thumbnail + y tuong tap moi vao E:/CLAUDE/YOUTUBE/YOUTUBE_INTELLIGENCE_ENGINE/reports/may1/LATEST.md."""
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(exe):
        exe = sys.executable
    try:
        p = subprocess.Popen([exe, YIE_AFTER, "--scheduled", "--day", TODAY, "--exit-code", str(rc)], cwd=YIE_ROOT,
                             creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                             close_fds=True)
        log("da goi YIE after_collector pid", p.pid)
    except Exception as e:
        log("LOI goi YIE:", str(e)[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", default="", help="chi chay cac tab nay (X,Lane-GEO,Lane-P); bo trong = ca 3")
    ap.add_argument("--dry-run", action="store_true", help="doc Studio nhung KHONG ghi sheet")
    ap.add_argument("--force", action="store_true", help="chay ca khi hom nay da chay xong")
    ap.add_argument("--scheduled", action="store_true", help="goi tu task dang nhap (chi de ghi log)")
    ap.add_argument("--report-only", action="store_true", help="khong doc Studio, chi viet lai bao cao tu log hom nay")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    cfg = json.load(open(LANES_FILE, encoding="utf-8"))
    all_tabs = [t for g in cfg["groups"] for t in g["tabs"]]
    tabs = [t for t in all_tabs if not a.tab or t in {x.strip() for x in a.tab.split(",")}]
    if not tabs:
        log("khong co tab nao khop", a.tab); return 1
    if a.report_only:
        write_report(tabs, 0, None, a.dry_run, "-", "-"); return 0
    if os.path.exists(DONE) and not a.force and not a.dry_run:
        log("hom nay da chay xong (", DONE, ") -> bo qua. Dung --force de chay lai."); return 0

    t_start = time.strftime("%Y-%m-%d %H:%M:%S")
    log(f"===== BAT DAU {'scheduled (mo may)' if a.scheduled else 'tay'} | tabs={tabs}{' DRY-RUN' if a.dry_run else ''}")
    start_off = os.path.getsize(LOGF) if os.path.exists(LOGF) else 0
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "DAILY_LANES_FILE": LANES_FILE, "DAILY_REPORT_SUBDIR": SUBDIR}
    cmd = [sys.executable, os.path.join(HERE, "daily_parallel.py"), "--workers", str(a.workers), "--tab", ",".join(tabs)]
    if a.dry_run:
        cmd.append("--dry-run")
    try:
        rc = subprocess.run(cmd, cwd=ROOT, env=env).returncode
    except Exception as e:
        log("LOI chay daily_parallel:", str(e)[:200]); rc = -1
    t_end = time.strftime("%Y-%m-%d %H:%M:%S")
    log(f"daily_parallel exit {rc}")
    data = None
    try:
        data = write_report(tabs, start_off, rc, a.dry_run, t_start, t_end)
    except Exception as e:
        log("LOI viet bao cao:", str(e)[:300])
    if rc == 0 and not a.dry_run and data is not None and tabs == all_tabs:   # chay thu 1 lane khong khoa ca ngay
        json.dump({"finished": t_end, "tabs": tabs}, open(DONE, "w", encoding="utf-8"))
    if not a.dry_run:
        call_yie(rc)
    try:
        import spike_notify
        n = sum(1 for l in (data or {}).get("lanes", {}).values() for v in l.get("videos", []) if v["read_today"])
        y = sum(1 for l in (data or {}).get("lanes", {}).values() for v in l.get("videos", []) if v["flag"] == "VANG")
        spike_notify.toast("Máy 1: chỉ số X/GEO/P xong" if rc == 0 else "Máy 1: chỉ số X/GEO/P LỖI",
                           f"{n} video đọc được · {y} dòng vàng · báo cáo inbox\\may1\\{TODAY}.md")
    except Exception:
        pass
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
