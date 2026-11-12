# -*- coding: utf-8 -*-
r"""
GHI COT K theo luat anh chot 2026-11-02 (Lane-P + Lane-GEO):
  Video da dang, KHONG phai video moi nhat dang trong 6h:
     CTR 24h < 2,5%  HOAC  CTR 24h khong hien ("—"/rong)  HOAC  impression 24h < 500
        -> K = "CẦN THAY ĐỔI TIÊU ĐỀ+THUMBS" + to vang CA DONG
     nguoc lai -> giu nguyen K (khong ghi)
  Video moi nhat dang < 6h -> KHONG danh dau, K = ghi chu "MỚI ĐĂNG <6h — CHƯA XÉT",
  bo vang dong do.

Nguon so: log job may1 hom nay (reports/may1_logon/<ngay>.log) — dong CUOI CUNG moi (tab, dong).
Khong dung Studio o day, chi doc/ghi sheet.

  py -3.13 scratch_analysis/ghi_K_P_GEO.py            # in bang, KHONG ghi
  py -3.13 scratch_analysis/ghi_K_P_GEO.py --ghi      # ghi that
"""
import os, re, sys, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "scratch_analysis"))
os.environ.pop("PYTHONPATH", None)
import daily_sheet as dsh
from ytapi import get as yt_get   # helper API dung chung (khong in gi khi import)

TODAY = datetime.date.today().isoformat()
LOG = os.path.join(ROOT, "reports", "may1_logon", f"{TODAY}.log")
TABS = ("Lane-P", "Lane-GEO")
MARK = "CẦN THAY ĐỔI TIÊU ĐỀ+THUMBS"
ROW_RE = re.compile(r"\[(?P<tab>[^\]]+)\] dong (?P<row>\d+) (?P<vid>[\w-]{11}): N=(?P<N>\S*) O=(?P<O>\S*)"
                    r" P=(?P<P>\S*) Q=(?P<Q>\S*) imp24h=(?P<imp>\S*) \| (?P<flag>ok|VANG)")


def log_metrics():
    """(tab,row) -> dict so cua lan doc CUOI CUNG trong ngay."""
    out = {}
    if not os.path.exists(LOG):
        sys.exit("khong thay log " + LOG)
    for ln in open(LOG, encoding="utf-8", errors="replace"):
        m = ROW_RE.search(ln)
        if m:
            d = m.groupdict()
            out[(d["tab"], int(d["row"]))] = {"vid": d["vid"], "Q": d["Q"], "P": d["P"],
                                              "O": d["O"], "N": d["N"], "imp": d["imp"],
                                              "time": ln[:8]}
    return out


def num(t):
    try:
        return float(str(t).replace("%", "").replace(".", "").replace(",", "."))
    except Exception:
        return None


def pub_times(ids):
    """{vid: {'pub': aware-dt, 'title': str}} — khong co = video hen gio/rieng tu."""
    out = {}
    for i in range(0, len(ids), 50):
        d = yt_get("videos", part="snippet", id=",".join(ids[i:i + 50]))
        for it in d.get("items", []):
            out[it["id"]] = {"pub": datetime.datetime.fromisoformat(
                it["snippet"]["publishedAt"].replace("Z", "+00:00")),
                "title": it["snippet"]["title"]}
    return out


def main(argv):
    ghi = "--ghi" in argv
    met = log_metrics()
    meta = pub_times([v["vid"] for v in met.values()])
    now = datetime.datetime.now(datetime.timezone.utc)
    s = dsh.svc()
    sids = dsh.sheet_ids(s)
    plan, report = {}, []
    for tab in TABS:
        rows, yel = dsh.read_tab(s, tab)
        # video moi nhat cua lane (theo publishedAt) -> duoc mien 6h
        vids = [r[11].strip() for r in rows[1:] if len(r) > 11 and len(r[11].strip()) == 11]
        newest = max((meta[v]["pub"] for v in vids if v in meta), default=None)
        for row, r in enumerate(rows[1:], start=2):
            vid = r[11].strip() if len(r) > 11 else ""
            if len(vid) != 11 or vid not in met:
                continue                      # dong chua co ID hoac lan nay khong doc duoc
            m = met[(tab, row)]
            if m["vid"] != vid:
                continue                      # log cua lan chay khac -> bo qua cho an toan
            ctr = num(m["Q"]) if (m["Q"] and m["Q"] != "—") else None
            imp = num(m["imp"])
            pm = meta.get(vid)
            hours = (now - pm["pub"]).total_seconds() / 3600 if pm else None
            exempt = bool(pm and newest and pm["pub"] == newest and hours < 6)
            ly_do = []
            if ctr is None:
                ly_do.append("CTR 24h=—")
            elif ctr < 2.5:
                ly_do.append(f"CTR 24h={ctr:.1f}%")
            if imp is not None and imp < 500:
                ly_do.append(f"imp 24h={imp:.0f}")
            mark = bool(ly_do) and not exempt
            if exempt:
                newK = (f"{hours:.0f}h · {m['O']} view · CTR 24h {m['Q'] or '—'} · "
                        f"{imp:.0f} lượt hiển thị/24h. MỚI ĐĂNG <6h — CHƯA XÉT.")
            elif mark:
                newK = MARK
            else:
                newK = None                   # giu nguyen K dang co
            oldK = (r[10] if len(r) > 10 else "")
            report.append((tab, row, vid, pm["title"][:38] if pm else "?", hours, ctr, imp,
                           "MIEN_6H" if exempt else ("MARK" if mark else "GIU"),
                           ", ".join(ly_do), oldK[:40], newK))
            if newK is not None and newK != oldK:
                plan.setdefault(tab, []).append(
                    {"row": row, "vals": {"K": newK}, "yellow": False if exempt else True})
            elif mark and oldK == MARK:
                plan.setdefault(tab, []).append({"row": row, "vals": {}, "yellow": True})

    print(f"{'tab':9} {'dong':>4} {'video':11} {'h':>6} {'CTR24h':>7} {'imp24h':>7}  quyet  ly_do")
    for t, row, vid, title, h, ctr, imp, q, why, oldK, newK in report:
        print(f"{t:9} {row:>4} {vid} {('%.0f' % h) if h is not None else '?':>6} "
              f"{('%.1f' % ctr) if ctr is not None else '—':>7} {('%.0f' % imp) if imp is not None else '?':>7}  "
              f"{q:8} {why}")
    n = sum(len(v) for v in plan.values())
    print(f"\n-> {n} dong se ghi ({ {k: len(v) for k, v in plan.items()} })")

    if not ghi:
        print("DRY-RUN: chua ghi gi. Them --ghi de ghi that.")
        return
    for tab, ups in plan.items():
        dsh.write(s, tab, sids[tab], ups)
        print(f"[{tab}] da ghi {len(ups)} dong: " + ", ".join(str(u["row"]) for u in ups))


if __name__ == "__main__":
    main(sys.argv[1:])
