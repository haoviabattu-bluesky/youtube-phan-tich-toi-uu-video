# -*- coding: utf-8 -*-
"""Chuan hoa o K8 tab X ve DUNG chuoi anh chot (CLAUDE.md): 'CTR 24h< 2.5- Yeu cau thay doi'
Giu nguyen to vang. Backup gia tri K8 hien tai truoc khi ghi.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import daily_sheet as ds  # noqa: E402

CHOT = "CTR 24h< 2.5- Yêu cầu thay đổi"
s = ds.svc()

# 1. doc K8 hien tai + mau nen
got = s.spreadsheets().get(
    spreadsheetId=ds.SHEET_ID, ranges=["'X'!K8"],
    fields="sheets.data.rowData.values(userEnteredValue,effectiveFormat.backgroundColor)",
    includeGridData=True).execute()
cell = got["sheets"][0]["data"][0]["rowData"][0]["values"][0]
old = cell.get("userEnteredValue", {})
bg = cell.get("effectiveFormat", {}).get("backgroundColor", {})
print("K8 truoc:", old, "| bg:", bg)

bak = os.path.join(ROOT, "reports",
                   f"backup_sheet_X_{time.strftime('%Y-%m-%d')}_truoc_chuanhoa_K8.json")
json.dump({"range": "X!K8", "value": old, "backgroundColor": bg,
           "thoi_diem": time.strftime("%Y-%m-%d %H:%M:%S")},
          open(bak, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("backup:", bak)

# 2. ghi dung chuoi + to vang (giu nguyen neu da vang)
sid = ds.sheet_ids(s)["X"]
s.spreadsheets().values().update(
    spreadsheetId=ds.SHEET_ID, range="'X'!K8", valueInputOption="RAW",
    body={"values": [[CHOT]]}).execute()
s.spreadsheets().batchUpdate(
    spreadsheetId=ds.SHEET_ID,
    body={"requests": [{"repeatCell": {
        "range": {"sheetId": sid, "startRowIndex": 7, "endRowIndex": 8,
                  "startColumnIndex": 10, "endColumnIndex": 11},
        "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1, "green": 1, "blue": 0}}},
        "fields": "userEnteredFormat.backgroundColor"}}]}).execute()

# 3. doc lai
chk = s.spreadsheets().get(
    spreadsheetId=ds.SHEET_ID, ranges=["'X'!K8"],
    fields="sheets.data.rowData.values(userEnteredValue,effectiveFormat.backgroundColor)",
    includeGridData=True).execute()
c = chk["sheets"][0]["data"][0]["rowData"][0]["values"][0]
print("K8 sau :", c.get("userEnteredValue"),
      "| bg:", c.get("effectiveFormat", {}).get("backgroundColor"))
