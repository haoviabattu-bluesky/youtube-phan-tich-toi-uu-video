# PHAN_TICH_TOI_UU_VIDEO

Vòng phản hồi (analytics) cho pipeline sản xuất video YouTube faceless ở `E:\CLAUDE\YOUTUBE\h2dev`.
Đọc số từ YouTube Studio → chạy SOP → đánh dấu "CẦN THAY ĐỔI" lên Google Sheet.

**Đọc `CLAUDE.md` trước** — đó là luật làm việc của dự án (vai trò, luật cứng, bản đồ lane ↔ mail ↔ channel).

## Nội dung

| Đường dẫn | Là gì |
|---|---|
| `YOUTUBE_POSTPUBLISH_ANALYTICS_SOP.md` | SOP 30 mục — khung phân tích bắt buộc |
| `CLAUDE.md` | Luật dự án + 6 bẫy đã trả giá + bản đồ lane |
| `tools\studio_collect.py` | Gom số ĐẦY ĐỦ từ YouTube Studio (GPMLogin + Playwright CDP) → CSV |
| `tools\sheet_metrics_sync.py` | Đồng bộ 4 cột N–Q (ngày/view/CTR tổng/CTR 24h) + rotate R,S thẳng vào Google Sheet |
| `tools\scan_channels.py` | Quét lane ↔ mail ↔ channel id → `scan_channels.json` |
| `tools\open_studio_profile.py` | Mở profile Chrome riêng để đăng nhập tay |
| `tools\sol_packaging_review.py` | Nhờ GPT-5.6-sol chấm title + thumbnail video đã flop |
| `youtube_postpublish_metrics.csv` | Sổ số liệu: 1 dòng = 1 video × 1 mốc snapshot |
| `reports\` | Backup ô sheet trước khi ghi đè + báo cáo per-video |

## Dựng lại trên máy mới

Dự án này **ĐỘC LẬP** — vòng chính (mở profile → đọc Studio → ghi sheet) không phụ thuộc h2dev
hay bất cứ dự án nào khác. Chỉ đúng **1 trong 5 tool** (`sol_packaging_review.py`, tính năng
phụ "nhờ AI chấm title/thumbnail") mượn client gọi model của h2dev — bỏ qua tool đó thì khỏi
cần h2dev. Việc trước đây liệt kê h2dev ngang hàng với các bước bắt buộc là **viết sai/gây hiểu
nhầm**, đã sửa lại theo đúng import thật của từng file (`grep import` xác nhận).

### A. BẮT BUỘC cho vòng chính (studio_collect.py, sheet_metrics_sync.py, scan_channels.py, open_studio_profile.py)

1. **Python 3.13** + thư viện:
   ```
   py -3.13 -m pip install requests playwright pillow google-auth google-api-python-client
   py -3.13 -m playwright install chromium
   ```
2. **GPMLogin** đã cài, đang chạy, và có sẵn 10 profile theo bảng lane trong `CLAUDE.md` (Lane D
   đã bỏ theo dõi 2026-09-25). Không có GPM thì dùng `tools\open_studio_profile.py` (Chrome
   profile riêng, đăng nhập tay — cách này hoàn toàn không cần GPM). Nếu GPM báo
   `ProfileUsingByOther` khi start — profile đang mở ở nơi khác (cửa sổ GPM app, hoặc phiên
   Claude khác) — **KHÔNG đóng/kill nó để chiếm lại**, đợi rồi chạy lại (CLAUDE.md bẫy #9).
3. **Credential Google Sheets cho `sheet_metrics_sync.py`** (tool DUY NHẤT tự ghi sheet bằng
   service account, không qua Claude/MCP) — file
   `D:\CLAUDE\credentials\google-sheets-key.json` (đường dẫn hardcode ở hằng `CREDS` đầu file).
   **Trên máy hiện tại file này đã có sẵn và ĐÚNG service account đã share**
   (`claude-sheets-reader@fifth-glider-495702-b4.iam.gserviceaccount.com`, verify 2026-09-25) —
   không cần làm gì thêm ở đây. Trên máy mới thì tự chép file này sang, hoặc sửa hằng `CREDS`.
   ⚠️ **"Share" trên Google Sheets có 2 mức** — Viewer chỉ đọc được, `sheet_metrics_sync.py` cần
   **Editor** mới ghi được. Share xong mà tool vẫn báo lỗi quyền (`HttpError 403`) thì đổi lại
   mức chia sẻ từ Viewer → Editor cho đúng email service account đó, không phải thêm bước gì
   khác.

### B. TÙY CHỌN — chỉ khi dùng `sol_packaging_review.py` ("nhờ AI chấm packaging video flop")

4. **Dự án anh em `h2dev`** phải có mặt: tool này cần `h2dev\pipeline\sol_client.py` (client gọi
   GPT-5.6-sol có sẵn của h2dev — lý do mượn: đỡ phải tự viết lại 1 client HTTP có 3 tầng
   fallback proxy). Đường dẫn **tự dò** (hàm `_find_pipeline`): biến môi trường
   `H2DEV_PIPELINE` → `<thư mục cha>\h2dev\pipeline` → `<thư mục cha>\YOUTUBE\h2dev\pipeline` →
   lùi thêm một cấp. Để chỗ khác hẳn thì `setx H2DEV_PIPELINE "D:\duong\dan\h2dev\pipeline"`.
   Cần thêm `py -3.13 -m pip install httpx` (dependency của `sol_client.py`). Key gọi model có
   sẵn giá trị mặc định trong `sol_client.py`/`keys.py` của h2dev, không cần cấu hình gì thêm.

### Google Sheet

`1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` — Claude ghi qua MCP `gsheets` (cấu hình MCP
nằm ở `~/.claude`, không nằm trong repo này, dùng cho mọi thao tác Claude tự làm như đánh dấu
`CẦN THAY ĐỔI`); riêng `sheet_metrics_sync.py` ghi trực tiếp qua credential ở mục A.3, độc lập
hoàn toàn với MCP — 2 đường ghi khác nhau nhưng cùng 1 sheet, cùng 1 service account.

## KHÔNG nằm trong repo

- `studio_profile/` — profile Chrome 93 MB (cookie/session). Cố ý loại trừ: App-Bound Encryption
  của Chrome làm profile copy sang máy khác mất sạch cookie, nên chép cũng vô ích **và** đó là
  dữ liệu đăng nhập không được đẩy lên git. Máy 2 đăng nhập lại từ đầu.
- Mọi file credential / `.env`.

## Kiểm tra nhanh trên máy mới

```
py -3.13 tools\scan_channels.py
```

Lệnh này chạm vào đúng 3 thứ dễ hỏng nhất: Python + thư viện, GPMLogin (`127.0.0.1:9495`),
và trạng thái đăng nhập của 10 profile. Chạy trôi + ghi ra `scan_channels.json` có channel id
là máy đã sẵn sàng cho `studio_collect.py`. Profile nào báo chưa đăng nhập thì mở
`py -3.13 tools\open_studio_profile.py` rồi đăng nhập tay một lần.

Lệnh này **không đụng tới** credential Google Sheets (mục 4 ở trên) — kiểm riêng phần đó bằng:

```
py -3.13 tools\sheet_metrics_sync.py --tab Satori-Lopezzapa68 --mail LopezzapataHilla@gmail.com --only yCSzCQN_VsE --dry-run
```

`--dry-run` đọc sheet + đọc Studio thật nhưng KHÔNG ghi gì — thấy in ra được dòng
`N=... O=... P=... Q=...` là cả 2 phía (đọc sheet qua service account, đọc Studio qua GPM) đều
thông; lỗi `HttpError 403` ở bước đọc sheet là dấu hiệu service account chưa được share quyền
Editor (xem lại mục 4).
