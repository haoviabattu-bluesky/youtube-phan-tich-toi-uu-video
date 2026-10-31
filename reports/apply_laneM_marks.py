# -*- coding: utf-8 -*-
"""Ghi lane M theo quyen anh chot 2026-10-18: to vang ca dong + ghi K + TONGHOP 'SUA CTR'.
Chi 3 tap vi pham CTR 24h (cot Q, 24h truot) < 2,5% va da du 48h: ep03, ep07, ep10.
  py -3.13 reports/apply_laneM_marks.py --dry-run
  py -3.13 reports/apply_laneM_marks.py
"""
import sys, os, json, argparse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import daily_sheet as dsh
from daily_k_rules import k_note

TAB = "M-teinengo-anaba"
TODAY = datetime.date.today().isoformat()
OUT = os.path.join(ROOT, "reports")

# video_id -> (gio that tu publishedAt Data API, views, ctr_tong, ctr_24h_truot, imp_24h)
TARGETS = {
    "VFdj45ytUaI": (403.0, 1100, 3.8, 2.2, 312.0),   # ep03
    "9Bn6J3RtCJ4": (236.0, 1100, 4.0, 2.1, 142.0),   # ep07
    "nNlqnf28Kak": (68.0, 430, 2.0, 2.0, 699.0),     # ep10
}

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

s = dsh.svc()
sids = dsh.sheet_ids(s)
rows, yel = dsh.read_tab(s, TAB)

# map video_id -> (row_num, stt, o K hien tai)
found = {}
for i, r in enumerate(rows[1:], start=2):
    r = r + [""] * 25
    vid = r[11].strip()
    if vid in TARGETS:
        found[vid] = (i, r[0].strip(), r[10].strip())

print(f"Tab {TAB}: {len(rows)} dong, tim thay {len(found)}/{len(TARGETS)} video can danh dau")
missing = set(TARGETS) - set(found)
if missing:
    print("THIEU:", missing)

updates, eps = [], []
for vid, (hours, views, ctr_t, ctr_q, imp24) in TARGETS.items():
    if vid not in found:
        continue
    row, stt, old_k = found[vid]
    note, yellow = k_note(hours, views, ctr_t, ctr_q, imp24)
    print(f"\n  {vid} (ep{stt}, dong {row})")
    print(f"    K cu : {old_k[:100] or '(trong)'}")
    print(f"    K moi: {note}")
    print(f"    to vang: {yellow} (dang vang: {yel.get(row)})")
    updates.append({"row": row, "vals": {"K": note}, "yellow": yellow, "stt": stt})
    eps.append((stt, yellow))

if a.dry_run:
    print("\nDRY-RUN: khong ghi gi")
    sys.exit(0)

# --- backup TRUOC khi ghi (bat buoc) ---
for u in updates:
    p = os.path.join(OUT, f"backup_sheet_{TAB}_{TODAY}_truoc_ghi_K{u['row']}.json")
    dsh.backup(p, TAB, rows, yel)
    print("backup ->", p)

# --- 1+2: to vang ca dong + ghi K ---
dsh.write(s, TAB, sids[TAB], updates)
print(f"\nDA GHI K + to vang {len(updates)} dong")

# --- 3: TONGHOP ---
th_bak = os.path.join(OUT, f"backup_TONGHOP_{TODAY}_truoc_ghi_laneM.json")
for x in dsh.tonghop(s, TAB, eps, th_bak):
    print("TONGHOP:", x)
print("TONGHOP backup ->", th_bak)
