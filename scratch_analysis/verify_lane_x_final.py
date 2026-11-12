# -*- coding: utf-8 -*-
"""Verify cuoi: tab X c��t N-S + K8 (chuoi + vang) + format P12."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import daily_sheet as ds  # noqa: E402

s = ds.svc()
rows = s.spreadsheets().values().get(
    spreadsheetId=ds.SHEET_ID, range="'X'!A1:S14").execute().get("values", [])
print("=== N-S tung dong ===")
ok = 0
for i, r in enumerate(rows, 1):
    if i == 1:
        continue
    g = lambda k: r[k] if k < len(r) else ""
    vid = g(11)
    if not vid:
        continue
    print(f"dong {i:>2} {vid:<13} N={g(13):<3} O={g(14):<8} P={g(15):<8} Q={g(16):<8} K={g(10)[:40]!r}")
    if g(13) and g(14):
        ok += 1
print("so dong co N+O:", ok)

chk = s.spreadsheets().get(
    spreadsheetId=ds.SHEET_ID, ranges=["'X'!K8", "'X'!P12"],
    fields="sheets.data.rowData.values(userEnteredValue,effectiveFormat(numberFormat,backgroundColor))",
    includeGridData=True).execute()
vals = chk["sheets"][0]["data"]
k8 = vals[0]["rowData"][0]["values"][0]
p12 = vals[1]["rowData"][0]["values"][0]
print("\nK8 =", k8.get("userEnteredValue"), "| bg:", k8.get("effectiveFormat", {}).get("backgroundColor"))
print("P12=", p12.get("userEnteredValue"), "| fmt:", p12.get("effectiveFormat", {}).get("numberFormat"))
