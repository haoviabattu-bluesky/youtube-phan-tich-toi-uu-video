# -*- coding: utf-8 -*-
r"""Ghi cot K theo luat anh chot 2026-11-02 (Lane-P + Lane-GEO):

  Video da dang, KHONG phai video moi nhat moi list trong 6 gio qua, va:
     CTR 24h < 2,5%   HOAC   CTR 24h khong hien ("—"/rong)   HOAC   impression 24h < 500
  -> ghi vao cot K dung chuoi:  CẦN THAY ĐỔI TIÊU ĐỀ+THUMBS
  Khong dung cot nao khac, khong doi mau nen.

So doc tu log lan chay CUOI trong ngay (dong "dong <n> <vid>: N=.. Q=.. imp24h=.."),
gio dang that lay tu YouTube Data API (de xet moc 6 gio).

  env -u PYTHONPATH py -3.13 scratch_analysis/ghi_K_theo_luat_moi.py --dry-run
  env -u PYTHONPATH py -3.13 scratch_analysis/ghi_K_theo_luat_moi.py --ghi
"""
import os, sys, re, json, time, argparse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "scratch_analysis"))
os.environ.pop("PYTHONPATH", None)
import daily_sheet as dsh
from ytapi import get as yt_get

TEXT = "CẦN THAY ĐỔI TIÊU ĐỀ+THUMBS"
CTR_MIN = 2.5
IMP_MIN = 500
NEWEST_H = 6

LOGS = {
    "Lane-P": [os.path.join(ROOT, "reports", "may1_logon", "2026-11-02.log")],
    "Lane-GEO": [os.path.join(ROOT, "reports", "may1_logon", "2026-11-02_geo_tay.log")],
}
LINE = re.compile(r"\[(?P<tab>Lane-[\w-]+)\] dong (?P<row>\d+) (?P<vid>[A-Za-z0-9_-]{11}): "
                  r"N=(?P<n>\d+) O=(?P<o>[\d.]+) P=(?P<p>[^ ]+) Q=(?P<q>[^ ]+) imp24h=(?P<imp>[\d.]+|None)")


def parse(logs):
    """{(tab,row): dict} — dong CUOI CUNG thang."""
    out = {}
    for p in logs:
        if not os.path.exists(p):
            print("  (!) khong thay log:", p); continue
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = LINE.search(ln)
            if not m:
                continue
            d = m.groupdict()
            q = d["q"].strip()
            ctr = None if q in ("—", "-", "", "None") else float(q.replace("%", "").replace(",", "."))
            imp = None if d["imp"] == "None" else float(d["imp"])
            out[(d["tab"], int(d["row"]))] = {"vid": d["vid"], "n": int(d["n"]), "o": d["o"],
                                              "p": d["p"], "q": q, "ctr24": ctr, "imp": imp}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", default="Lane-P,Lane-GEO")
    ap.add_argument("--ghi", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tabs = [t.strip() for t in a.tab.split(",") if t.strip()]
    data = parse([p for t in tabs for p in LOGS.get(t, [])])
    s = dsh.svc()
    sids = dsh.sheet_ids(s)
    now = datetime.datetime.now(datetime.timezone.utc)
    updates = []
    for tab in tabs:
        rows, yel = dsh.read_tab(s, tab)
        ids = [(i, r[11].strip()) for i, r in enumerate(rows[1:], start=2)
               if len(r) > 11 and len(r[11].strip()) == 11]
        # gio dang that qua API
        meta = {}
        if ids:
            try:
                resp = yt_get("videos", part="snippet", id=",".join(v for _, v in ids), maxResults=50)
                for it in resp.get("items", []):
                    meta[it["id"]] = datetime.datetime.fromisoformat(
                        it["snippet"]["publishedAt"].replace("Z", "+00:00"))
            except Exception as e:
                print("(!) API loi:", str(e)[:120])
        newest = max(meta.items(), key=lambda kv: kv[1]) if meta else None
        print(f"\n=== {tab}: {len(ids)} video co ID ===")
        for row, vid in ids:
            d = data.get((tab, row))
            if not d or d["vid"] != vid:
                print(f"  dong {row} {vid}: KHONG co so lan nay -> giu nguyen o K")
                continue
            pub = meta.get(vid)
            hrs = (now - pub).total_seconds() / 3600 if pub else d["n"] * 24
            exempt = bool(newest and newest[0] == vid and hrs < NEWEST_H)
            reasons = []
            if d["ctr24"] is None:
                reasons.append("CTR 24h không hiển thị")
            elif d["ctr24"] < CTR_MIN:
                reasons.append(f"CTR 24h {d['q']} < 2,5%")
            if d["imp"] is None or d["imp"] < IMP_MIN:
                reasons.append(f"impression 24h {d['imp'] if d['imp'] is not None else '—'} < 500")
            mark = bool(reasons) and not exempt
            if exempt:
                print(f"  dong {row} {vid}: MIEN TRU (video moi nhat, {hrs:.1f}h < 6h) -> giu nguyen K")
                continue
            cur_k = rows[row - 1][10] if len(rows[row - 1]) > 10 else ""
            print(f"  dong {row} {vid}: N={d['n']}ngay CTR24={d['q']} imp24h={d['imp']}"
                  f" | {'GHI K' if mark else 'de nguyen'}"
                  f"{' — ' + '; '.join(reasons) if reasons else ''}")
            if mark:
                updates.append({"row": row, "vals": {"K": TEXT}, "yellow": None,
                                "old": cur_k, "tab": tab})
        print(f"  o vang hien tai: {[r for r, v in yel.items() if v]}")
    print(f"\nTONG: {len(updates)} dong se ghi '{TEXT}'")
    for u in updates:
        print(f"  {u['tab']} dong {u['row']}  (K cu: {u['old'][:60]!r})")
    if not a.ghi:
        print("\nDRY-RUN — chua ghi gi. Them --ghi de ghi that.")
        return 0
    ts = time.strftime("%Y-%m-%d_%H%M%S")
    for tab in {u["tab"] for u in updates}:
        rows, yel = dsh.read_tab(s, tab)
        dsh.backup(os.path.join(ROOT, "reports", f"backup_sheet_{tab}_{ts}_truoc_ghiK.json"), tab, rows, yel)
        print(f"  da backup {tab}")
    for tab in {u["tab"] for u in updates}:
        us = [{"row": u["row"], "vals": u["vals"], "yellow": None} for u in updates if u["tab"] == tab]
        dsh.write(s, tab, sids[tab], us)
        print(f"  DA GHI {tab}: {len(us)} dong cot K")
    # doc lai xac minh
    print("\n--- doc lai xac minh ---")
    for tab in {u["tab"] for u in updates}:
        rows, _ = dsh.read_tab(s, tab)
        for u in updates:
            if u["tab"] != tab:
                continue
            got = rows[u["row"] - 1][10] if len(rows[u["row"] - 1]) > 10 else ""
            print(f"  {tab} dong {u['row']} K = {got!r} {'OK' if got == TEXT else 'SAI'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
