# -*- coding: utf-8 -*-
r"""
DONG BO CHI SO N-Q (SO NGAY LIST / VIEW / CTR TONG / CTR 24H) TU YOUTUBE STUDIO VE SHEET,
kem xoay vong R/S (VIEW CU / CTR 24H CU) TRUOC khi ghi de.

QUY TRINH (anh chot 2026-09-25):
  1. Doc gia tri HIEN TAI cua O (VIEW) va Q (CTR 24H) trong sheet.
  2. Copy O -> R (VIEW CU), Q -> S (CTR 24H CU)  [backup, KHONG doi gia tri that su thay doi
     neu R/S da co san tu truoc — luon ghi de bang gia tri O/Q NGAY TRUOC luc chay lan nay].
  3. Mo tung video (bang video_id o cot L) tren YouTube Studio, doc lai:
       N = SO NGAY LIST   (so ngay ke tu khi dang, lam tron xuong)
       O = VIEW           (tong luot xem, "Since published")
       P = CTR TONG       (CTR "Since published" — CTR TRON DOI video)
       Q = CTR 24H        (CTR cua dung 24 GIO GAN NHAT tinh tu luc chay — KHONG phai "Since
                            published", cung KHONG phai "First 24 hours" co dinh luc dang)
  4. Ghi N,O,P,Q (+ R,S da rotate o buoc 2) vao DUNG dong cua video_id do.
  MAC DINH KHONG dong/sua bat ky cot nao khac (E,G,K,...). Muon danh dau "CAN THAY DOI" thi
  chay rieng tools/mark_sheet.py (hoac --mark trong tool nay, xem duoi).

Chay:
  py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\sheet_metrics_sync.py --tab Satori-Lopezzapa68 --mail LopezzapataHilla@gmail.com
  py -3.13 ...\sheet_metrics_sync.py --tab A-shinya_shiryoshitsu --mail haoviabattu
  py -3.13 ...\sheet_metrics_sync.py --tab Satori-Lopezzapa68 --ws ws://localhost:PORT/...  --only yCSzCQN_VsE,MBKmD9CUGLo
  py -3.13 ...\sheet_metrics_sync.py --tab Satori-Lopezzapa68 --mail ... --mark      (sau khi ghi so, QUET lai va
                                                                                       ghi "CAN THAY DOI" vao E+G
                                                                                       cho dong khong dat — xem ham
                                                                                       can_thay_doi())

BAY DA TRA GIA (dung don gian hoa lai — xem them CLAUDE.md muc Du lieu):
  1. Toa do cot KHONG GIONG NHAU giua cac tab. Header dong 1 co tab ghi "ID" o L, co tab de
     trong (mail/URL kenh nam tam o do). NHUNG du lieu THAT o moi dong (tu dong 2) LUON dat
     video_id o cot L bat ke header noi gi -> doc video_id theo VI TRI COT (index 11), KHONG
     doc theo ten header.
  2. YouTube Studio KHONG CO preset "Last 24 hours" cho video analytics (chi co "First 24
     hours" — CO DINH tai luc dang, vo dung voi video da cu). Phai tu dung URL:
       /video/<id>/analytics/tab-reach_viewers/period-<start_ms>,<end_ms>
     voi start_ms/end_ms la epoch millisecond TU TAY TINH (now-24h .. now) — KHONG click UI.
     Da verify that 2026-09-25: URL nay nhay thang vao dung khoang, Studio tu doi nhan thanh
     "Custom". Day la cach DUY NHAT lay dung CTR-24h-truot, tuyet doi dung suy dien tu "Last 7
     days" (period-week) vi no gan nhu trung "Since published" voi video con moi.
  3. Studio hien "—" (KHONG PHAI "0,0%") khi mau qua nho de tinh % tin cay (vd 5 impressions
     trong 24h) — nhung se hien DUNG "0,0%" khi impressions du lon ma views=0. CA HAI deu la
     tin hieu that, ĐUNG QUY UOC CU: "—" -> o trong (chua co du lieu), "0,0%" -> ghi dung 0,0%.
  4. Dinh dang so trong sheet la kieu VIET (dau phay thap phan): "2,3%" khong phai "2.3%".
     Ghi sai dinh dang la lam hong dong bo voi cot P/Q da co san.
"""
import sys, os, re, time, argparse, datetime
sys.stdout.reconfigure(encoding="utf-8")
import requests
from playwright.sync_api import sync_playwright
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

GPM = "http://127.0.0.1:9495/api/v1"
BANNER = "GPMLogin Global API"
SHEET_ID = "1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU"
CREDS = r"D:\CLAUDE\credentials\google-sheets-key.json"

COL_ID = 11        # L (0-based)
COL_DAYS = 13       # N
COL_VIEW = 14       # O
COL_CTR_TOTAL = 15  # P
COL_CTR_24H = 16    # Q
COL_VIEW_OLD = 17   # R
COL_CTR_24H_OLD = 18  # S

DEEP = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
  const out = [];
  const walk = (root) => {
    for (const el of root.querySelectorAll('*')) {
      if (skip.has(el.tagName)) continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (el.children.length === 0) {
        const t = (el.textContent || '').trim();
        if (t && t.length < 200) out.push(t);
      }
    }
  };
  walk(document);
  return out;
}"""

CLICK_TEXT = """(label) => {
  let hit = null;
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (el.shadowRoot) walk(el.shadowRoot);
      if (!hit && el.children.length === 0 && (el.textContent||'').trim() === label) hit = el; } };
  walk(document);
  if (!hit) return false;
  let n = hit;
  for (let i = 0; i < 5 && n; i++) { if (n.click) n.click(); n = n.parentElement || (n.getRootNode && n.getRootNode().host); }
  return true;
}"""


# ---------------- Google Sheets ----------------
def sheets_svc():
    creds = Credentials.from_service_account_file(CREDS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return build("sheets", "v4", credentials=creds)


def col_letter(idx0):
    s, n = "", idx0 + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def read_rows(svc, tab):
    v = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"{tab}!A1:S500").execute()
    return v.get("values") or []


def write_row(svc, tab, row_num, vals):
    """vals = dict {col_idx0: value}. Ghi tung o rieng le (khong dung range lien tuc vi
    N..Q lien nhau nhung R,S co the da co gia tri backup khac vi tri) -> dung batchUpdate."""
    data = []
    for idx0, val in vals.items():
        rng = f"{tab}!{col_letter(idx0)}{row_num}"
        data.append({"range": rng, "values": [[val]]})
    body = {"valueInputOption": "USER_ENTERED", "data": data}
    svc.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()


def ensure_header(svc, tab):
    """Them nhan N1:S1 neu tab chua co (KHONG dong gi khac). An toan: chi ghi khi o dang trong."""
    v = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"{tab}!N1:S1").execute()
    cur = (v.get("values") or [[]])
    cur = cur[0] if cur else []
    want = ["SỐ NGÀY LIST", "VIEW", "CTR TỔNG", "CTR 24H", "VIEW CŨ", "CTR 24H CŨ"]
    if cur == want:
        return
    if any(c.strip() for c in cur):
        print(f"  [{tab}] N1:S1 da co du lieu KHAC nhan chuan -> BO QUA, khong ghi de:", cur)
        return
    svc.spreadsheets().values().update(spreadsheetId=SHEET_ID, range=f"{tab}!N1:S1",
                                        valueInputOption="USER_ENTERED", body={"values": [want]}).execute()
    print(f"  [{tab}] da them header N1:S1")


# ---------------- GPM ----------------
def gpm_find(mail):
    page = 1
    while True:
        d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        for p in d["data"]:
            n = p["name"].strip().lower()
            if n == mail.strip().lower() or n == mail.strip().lower().split("@")[0]:
                return p["id"]
        if page >= d["last_page"]:
            return None
        page += 1


def gpm_start(pid):
    j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=180).json()
    d = j.get("data")
    if j.get("message") == "ProfileUsingByOther":
        # BAT BUOC (anh chot 2026-09-25): profile dang duoc dung o noi khac (vd anh dang mo
        # tay xem Studio). TUYET DOI KHONG kill/dong no de chiem lai -> DUNG LAI, khong chay.
        raise RuntimeError("PROFILE_BUSY: profile dang duoc dung o noi khac (co the anh dang mo tay) "
                            "-> KHONG chay tool nay luc profile dang mo. Doi anh dong roi chay lai.")
    if not j.get("success") or d == BANNER or not isinstance(d, dict):
        raise RuntimeError(f"GPM start fail: {j.get('message') or d}")
    ws = d.get("websocket_debugging_url") or ""
    if not ws:
        raise RuntimeError("GPM websocket RONG -> stop + dong chrome cua profile roi chay lai (xem CLAUDE.md)")
    return ws


def gpm_stop(pid):
    try:
        requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
    except Exception:
        pass


# ---------------- parse ----------------
def num(s):
    if s is None:
        return None
    s = s.strip().replace(",", "").replace("%", "")
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([KMB])?", s)
    if not m:
        return None
    v = float(m.group(1))
    v *= {"K": 1e3, "M": 1e6, "B": 1e9}.get(m.group(2) or "", 1)
    return v


def after(parts, label, pred, span=6):
    for i, t in enumerate(parts):
        if t.strip() == label:
            for j in range(i + 1, min(i + 1 + span, len(parts))):
                v = pred(parts[j])
                if v is not None:
                    return v
    return None


def pct_after(parts, label, span=6):
    return after(parts, label, lambda t: num(t) if t.strip().endswith("%") else None, span)


def vn_pct(v):
    """so float -> chuoi kieu Viet '2,3%'. None -> ''."""
    if v is None:
        return ""
    return f"{v:.1f}".replace(".", ",") + "%"


def wait_text(page, needles, loops=25, gap=3):
    parts = []
    for _ in range(loops):
        time.sleep(gap)
        parts = page.evaluate(DEEP)
        j = " | ".join(parts)
        if any(n in j for n in needles):
            return parts
    return parts


# ---------------- 1 video ----------------
def read_video(page, vid):
    """Tra (days, views, ctr_total, ctr_24h) — None neu khong doc duoc muc do."""
    # Overview de lay ngay dang
    page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-overview/period-default",
              wait_until="domcontentloaded", timeout=90000)
    parts = wait_text(page, ["Average view duration", "Views"])
    j = " | ".join(parts)
    days = None
    m = re.search(r"([A-Z][a-z]{2} \d{1,2}, \d{4}) — Now", j)
    if m:
        try:
            d0 = datetime.datetime.strptime(m.group(1), "%b %d, %Y")
            hours = (datetime.datetime.now() - d0).total_seconds() / 3600
            days = int(hours // 24)
        except Exception:
            pass

    # Reach / Since published (period-default) -> Views + CTR TONG
    page.evaluate(CLICK_TEXT, "Reach")
    parts = wait_text(page, ["Thumbnail impressions"])
    views = after(parts, "Views", num)
    ctr_total = pct_after(parts, "Thumbnail click-through rate")

    # Reach / rolling 24h that su (now-24h .. now) -> CTR 24H
    now = datetime.datetime.now()
    start_ms = int((now - datetime.timedelta(hours=24)).timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-reach_viewers/period-{start_ms},{end_ms}",
              wait_until="domcontentloaded", timeout=90000)
    parts = wait_text(page, ["Thumbnail impressions"])
    ctr_24h = pct_after(parts, "Thumbnail click-through rate")

    return days, views, ctr_total, ctr_24h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab", required=True, help="ten tab trong sheet (= tab hien tai, vd Satori-Lopezzapa68)")
    ap.add_argument("--mail", help="ten profile GPM")
    ap.add_argument("--ws")
    ap.add_argument("--port", type=int)
    ap.add_argument("--only", default="", help="chi xu ly cac video_id nay, phan cach dau phay")
    ap.add_argument("--keep-open", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="chi in ra, KHONG ghi sheet")
    a = ap.parse_args()

    svc = sheets_svc()
    ensure_header(svc, a.tab)
    rows = read_rows(svc, a.tab)
    only = set(x.strip() for x in a.only.split(",") if x.strip())

    targets = []  # (row_num(1-based), video_id, cur_view, cur_ctr24h)
    for i, r in enumerate(rows[1:], start=2):  # dong 2 tro di
        vid = r[COL_ID].strip() if len(r) > COL_ID and r[COL_ID] else ""
        if not vid:
            continue
        if only and vid not in only:
            continue
        cur_view = r[COL_VIEW] if len(r) > COL_VIEW else ""
        cur_ctr24 = r[COL_CTR_24H] if len(r) > COL_CTR_24H else ""
        targets.append((i, vid, cur_view, cur_ctr24))

    print(f"[{a.tab}] So video se dong bo: {len(targets)}")
    if not targets:
        return 0

    pid = None
    ws = a.ws
    if not ws and a.port:
        import json as _json, urllib.request as _u
        with _u.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5) as r:
            ws = _json.load(r).get("webSocketDebuggerUrl")
    if not ws:
        if not a.mail:
            print("Can --mail hoac --ws/--port"); return 2
        pid = gpm_find(a.mail)
        if not pid:
            print("Khong tim thay profile GPM ten =", a.mail); return 2
        ws = gpm_start(pid)
        print("WS:", ws)

    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(90000)

        for row_num, vid, cur_view, cur_ctr24 in targets:
            print(f"-- dong {row_num} · {vid}", flush=True)
            try:
                days, views, ctr_total, ctr_24h = read_video(page, vid)
            except Exception as e:
                print("   LOI:", str(e)[:200]); continue

            vals = {
                COL_VIEW_OLD: cur_view,          # rotate O(cu) -> R
                COL_CTR_24H_OLD: cur_ctr24,      # rotate Q(cu) -> S
                COL_DAYS: str(days) if days is not None else "",
                COL_VIEW: str(int(views)) if views is not None else "",
                COL_CTR_TOTAL: vn_pct(ctr_total),
                COL_CTR_24H: vn_pct(ctr_24h),
            }
            print(f"   N={vals[COL_DAYS]} O={vals[COL_VIEW]} P={vals[COL_CTR_TOTAL]} Q={vals[COL_CTR_24H]}"
                  f"  (cu: R={cur_view} S={cur_ctr24})")
            if not a.dry_run:
                write_row(svc, a.tab, row_num, vals)

    if pid and not a.keep_open:
        gpm_stop(pid)
    print("XONG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
