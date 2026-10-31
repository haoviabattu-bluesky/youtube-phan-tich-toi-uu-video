# -*- coding: utf-8 -*-
"""sheet_note.py — ghi đường dẫn báo cáo viral vào tab NOTE, ô C21 (KHOÁ CỐ ĐỊNH).

Anh chốt 2026-10-19:
  * Mỗi ngày báo cáo mới được đưa lên tab `NOTE`, ô `C21` — KHOÁ CỐ ĐỊNH ô này.
  * Ngày sau ĐÈ LÊN ngày trước. Không thêm dòng, không đổi ô, không append.
  * Nội dung = ĐƯỜNG DẪN ĐẦY ĐỦ TUYỆT ĐỐI tới file HTML (một dòng), KHÔNG cắt gọn.

Ô B21 có nhãn `BÁO CÁO NGÀY` do anh đặt; script chỉ ghi C21, không đụng B21.
"""
import os
import sys

SHEET_ID = "1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU"
CREDS = r"D:\CLAUDE\credentials\google-sheets-key.json"
TAB = "NOTE"
CELL = "C21"

# Đường dẫn NHÌN TỪ MÁY 1 (nơi anh mở file) — khác đường dẫn trên máy 2 chạy tool.
# Anh chốt 2026-10-19: máy 1 đọc qua h2dev\FlowHandoff_local\results.
MAY1_RESULTS_DIR = r"E:\CLAUDE\YOUTUBE\h2dev\FlowHandoff_local\results"
# Máy 2 (máy này) ghi file thật ở đây:
MAY2_RESULTS_DIR = r"E:\CLAUDE\YOUTUBE\FlowHandoff_local\results"


def path_for_may1(local_path):
    """Đổi đường dẫn máy 2 -> đường dẫn máy 1 (cùng tên file, khác gốc thư mục).

    E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results\\VIRAL_X.html
      -> E:\\CLAUDE\\YOUTUBE\\h2dev\\FlowHandoff_local\\results\\VIRAL_X.html
    """
    if not local_path:
        return None
    name = os.path.basename(local_path)
    return os.path.join(MAY1_RESULTS_DIR, name)


def write_report_path(path, dry_run=False):
    """Ghi `path` vào NOTE!C21 (đè giá trị cũ). Trả (ok, thông báo).

    `path` là đường dẫn NHÌN TỪ MÁY 1 (nơi anh mở file), KHÔNG phải đường dẫn trên máy chạy
    tool. Máy này là máy 2 (gốc `E:\\CLAUDE\\YOUTUBE\\FlowHandoff_local\\results`), còn máy 1
    đọc qua `E:\\CLAUDE\\YOUTUBE\\h2dev\\FlowHandoff_local\\results` (anh chốt 2026-10-19).
    Vì vậy hàm KHÔNG kiểm `os.path.exists` trên đường dẫn truyền vào — file nằm ở máy khác.
    Việc kiểm file thật do run_daily làm trước khi gọi hàm này.
    """
    if not path:
        return False, "đường dẫn rỗng"
    if not os.path.isabs(path):
        return False, f"đường dẫn KHÔNG tuyệt đối: {path} (luật: phải đầy đủ tuyệt đối)"
    if dry_run:
        return True, f"[dry-run] sẽ ghi {TAB}!{CELL} = {path}"
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as e:
        return False, f"thiếu google-api-python-client: {e}"
    if not os.path.exists(CREDS):
        return False, f"không thấy service account: {CREDS}"
    try:
        creds = Credentials.from_service_account_file(
            CREDS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{TAB}!{CELL}",
            valueInputOption="RAW",
            body={"values": [[path]]}).execute()
        # đọc lại để xác minh (không tin output của lệnh ghi)
        back = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"{TAB}!{CELL}").execute()
        got = (back.get("values") or [[""]])[0][0]
        if got != path:
            return False, f"ghi xong nhưng đọc lại thấy {got!r} ≠ {path!r}"
        return True, f"đã ghi {TAB}!{CELL} = {path}"
    except Exception as e:                                    # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:200]}"


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Ghi đường dẫn báo cáo vào NOTE!C21")
    ap.add_argument("--path", required=True, help="đường dẫn ĐẦY ĐỦ TUYỆT ĐỐI tới file báo cáo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ok, msg = write_report_path(a.path, dry_run=a.dry_run)
    print(("OK   " if ok else "LỖI  ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
