# -*- coding: utf-8 -*-
"""Ap luat cot K + to vang + TONGHOP cho cac tap can sua (4 lane, 2026-10-18).

  py -3.13 reports/apply_marks_4lanes.py --dry-run
  py -3.13 reports/apply_marks_4lanes.py
"""
import sys, os, json, argparse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import daily_sheet as dsh
from daily_k_rules import k_note

TODAY = datetime.date.today().isoformat()
OUT = os.path.join(ROOT, "reports")

# tab -> [(video_id, hours, views, ctr_total, ctr_24h_truot, imp_24h)]
PLAN = {
    "L-shakai-no-naze": [
        ("7YoIs7L8c_w", 469.0, 6200, 3.8, None, 40.0),   # ep05 CTR 24h = "—" (40 hiển thị)
        ("iHbgfMd8Mbk", 277.0, 1800, 3.8, 2.4, 247.0),   # ep08
    ],
    "Lane-N": [
        ("EvdfvywqDc8", 277.0, 863, 3.1, 2.0, 50.0),     # ep01
        ("oXCuQVjE4jQ", 182.0, 80, 0.8, None, 15.0),     # ep04 CTR 24h = "—" (15 hiển thị)
    ],
}

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

s = dsh.svc()
sids = dsh.sheet_ids(s)

for tab, items in PLAN.items():
    rows, yel = dsh.read_tab(s, tab)
    idx = {}
    for i, r in enumerate(rows[1:], start=2):
        r = r + [""] * 25
        vid = r[11].strip()
        if vid:
            idx[vid] = (i, r[0].strip(), r[10].strip())
    print(f"\n=== {tab} ({len(rows)} dòng) ===")
    updates, eps = [], []
    for vid, hours, views, ctr_t, ctr_q, imp24 in items:
        if vid not in idx:
            print(f"  !! KHONG THAY {vid} trong tab -> bo qua")
            continue
        row, stt, old_k = idx[vid]
        note, yellow = k_note(hours, views, ctr_t, ctr_q, imp24)
        print(f"  {vid} (ep{stt}, dòng {row})")
        print(f"    K cũ : {old_k[:90] or '(trống)'}")
        print(f"    K mới: {note}")
        print(f"    vàng : {yellow} (đang: {yel.get(row)})")
        updates.append({"row": row, "vals": {"K": note}, "yellow": yellow})
        eps.append((stt, yellow))

    if a.dry_run or not updates:
        continue
    for u in updates:
        p = os.path.join(OUT, f"backup_sheet_{tab}_{TODAY}_truoc_ghi_K{u['row']}.json")
        dsh.backup(p, tab, rows, yel)
        print("  backup ->", p)
    dsh.write(s, tab, sids[tab], updates)
    print(f"  ĐÃ GHI K + tô vàng {len(updates)} dòng")
    bak = os.path.join(OUT, f"backup_TONGHOP_{TODAY}_truoc_ghi_{tab}.json")
    for x in dsh.tonghop(s, tab, eps, bak):
        print("  TONGHOP:", x)
