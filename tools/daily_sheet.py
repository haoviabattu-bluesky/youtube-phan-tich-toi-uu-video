# -*- coding: utf-8 -*-
r"""
GOOGLE SHEET CHO JOB 05:00: doc A:S, sao luu (gia tri + mau cot K), ghi N–S + K, to/bo vang CA DONG.
Khong xoa dong/cot nao. Bo vang chi khi o K dang dung mau vang (1,1,0) — mau khac anh to thi giu.
"""
import os, json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SHEET_ID = "1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU"
CREDS = r"D:\CLAUDE\credentials\google-sheets-key.json"
YELLOW = {"red": 1, "green": 1, "blue": 0}
WHITE = {"red": 1, "green": 1, "blue": 1}


def svc():
    c = Credentials.from_service_account_file(CREDS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return build("sheets", "v4", credentials=c, cache_discovery=False)


def sheet_ids(s):
    m = s.spreadsheets().get(spreadsheetId=SHEET_ID, fields="sheets.properties(title,sheetId)").execute()
    return {x["properties"]["title"]: x["properties"]["sheetId"] for x in m["sheets"]}


def read_tab(s, tab):
    """(rows A:S, k_yellow{row_num: bool})"""
    rows = s.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"'{tab}'!A1:S500").execute().get("values") or []
    g = s.spreadsheets().get(spreadsheetId=SHEET_ID, ranges=[f"'{tab}'!K1:K500"],
                             fields="sheets.data.rowData.values.userEnteredFormat.backgroundColor").execute()
    yel = {}
    data = (g["sheets"][0].get("data") or [{}])[0].get("rowData") or []
    for i, rd in enumerate(data, start=1):
        bg = ((rd.get("values") or [{}])[0].get("userEnteredFormat") or {}).get("backgroundColor") or {}
        yel[i] = bg.get("red", 0) == 1 and bg.get("green", 0) == 1 and not bg.get("blue", 0)
    return rows, yel


def backup(path, tab, rows, yel):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"tab": tab, "rows": rows, "k_yellow": yel}, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)


def write(s, tab, sid, updates):
    """updates = [{'row': n, 'vals': {col_letter: value}, 'yellow': True|False|None}] — None = khong dong mau."""
    data = [{"range": f"'{tab}'!{col}{u['row']}", "values": [[v]]} for u in updates for col, v in u["vals"].items()]
    if data:
        s.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID,
                                              body={"valueInputOption": "USER_ENTERED", "data": data}).execute()
    reqs = [{"repeatCell": {"range": {"sheetId": sid, "startRowIndex": u["row"] - 1, "endRowIndex": u["row"]},
                            "cell": {"userEnteredFormat": {"backgroundColor": YELLOW if u["yellow"] else WHITE}},
                            "fields": "userEnteredFormat.backgroundColor"}}
            for u in updates if u.get("yellow") is not None]
    if reqs:
        s.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()


# ---------------- TONGHOP (anh chot 2026-10-17) ----------------
# Dong 1 = ten tab lane (B..I), cot A = "Ep01".. ; tap CTR 24h thap -> o (tap, lane) = MARK.
# Tap da dat ma o dang la MARK -> tra ve "Listed" (gia tri truoc khi danh dau). O khac giu nguyen.
TONGHOP = "TONGHOP"
MARK = "SỬA CTR"


def _col(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26); s = chr(65 + r) + s
    return s


def tonghop(s, tab, eps, backup_path=None):
    """eps = [(stt_tap, can_sua: bool)]. Tra list chuoi mo ta o da ghi."""
    v = s.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"{TONGHOP}!A1:Z200").execute().get("values") or []
    head = v[0] if v else []
    if tab not in head[1:10]:
        return [f"TONGHOP khong co cot {tab}"]
    ci = head.index(tab, 1)
    rowof = {}
    for i, r in enumerate(v[1:], start=2):
        a = (r[0] if r else "").strip().lower()
        if a.startswith("ep") and a[2:].isdigit():
            rowof[int(a[2:])] = i
    data, done = [], []
    for stt, bad in eps:
        try:
            ep = int(str(stt).strip())
        except Exception:
            continue
        r = rowof.get(ep)
        if not r:
            done.append(f"Ep{ep:02d}: khong co dong o TONGHOP"); continue
        cur = (v[r - 1] + [""] * 30)[ci].strip()
        if cur and cur.lower() != "listed" and cur != MARK:
            # O anh tu ghi chu khac (vd "ĐÃ THAY TITLE+THUMB 21/10") -> KHONG ghi de (dinh 2026-10-22: ghi de C4)
            done.append(f"Ep{ep:02d} {_col(ci + 1)}{r}: GIU NGUYEN ghi chu cua anh '{cur}'"
                        f"{' (CTR 24h van thap)' if bad else ''}")
            continue
        new = MARK if bad else ("Listed" if cur == MARK else None)
        if new is not None and new != cur:
            data.append({"range": f"{TONGHOP}!{_col(ci + 1)}{r}", "values": [[new]]})
            done.append(f"Ep{ep:02d} {_col(ci + 1)}{r}: '{cur}' -> '{new}'")
    if data:
        if backup_path:
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            json.dump({"tab": TONGHOP, "rows": v}, open(backup_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        s.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID,
                                              body={"valueInputOption": "USER_ENTERED", "data": data}).execute()
    return done
