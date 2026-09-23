# PHAN_TICH_TOI_UU_VIDEO

Vòng phản hồi (analytics) cho pipeline sản xuất video YouTube faceless ở `E:\CLAUDE\YOUTUBE\h2dev`.
Đọc số từ YouTube Studio → chạy SOP → đánh dấu "CẦN THAY ĐỔI" lên Google Sheet.

**Đọc `CLAUDE.md` trước** — đó là luật làm việc của dự án (vai trò, luật cứng, bản đồ lane ↔ mail ↔ channel).

## Nội dung

| Đường dẫn | Là gì |
|---|---|
| `YOUTUBE_POSTPUBLISH_ANALYTICS_SOP.md` | SOP 30 mục — khung phân tích bắt buộc |
| `CLAUDE.md` | Luật dự án + 6 bẫy đã trả giá + bản đồ lane |
| `tools\studio_collect.py` | Gom số từ YouTube Studio (GPMLogin + Playwright CDP) |
| `tools\scan_channels.py` | Quét lane ↔ mail ↔ channel id → `scan_channels.json` |
| `tools\open_studio_profile.py` | Mở profile Chrome riêng để đăng nhập tay |
| `tools\sol_packaging_review.py` | Nhờ GPT-5.6-sol chấm title + thumbnail video đã flop |
| `youtube_postpublish_metrics.csv` | Sổ số liệu: 1 dòng = 1 video × 1 mốc snapshot |
| `reports\` | Backup ô sheet trước khi ghi đè + báo cáo per-video |

## Dựng lại trên máy mới

1. **Python 3.13** + thư viện:
   ```
   py -3.13 -m pip install requests playwright pillow
   py -3.13 -m playwright install chromium
   ```
2. **GPMLogin** đã cài, đang chạy, và có sẵn 9 profile theo bảng lane trong `CLAUDE.md`.
   Không có GPM thì dùng `tools\open_studio_profile.py` (Chrome profile riêng, đăng nhập tay).
3. **Dự án anh em `h2dev`** phải có mặt: `tools\sol_packaging_review.py` import
   `E:\CLAUDE\YOUTUBE\h2dev\pipeline\sol_client.py` (đường dẫn hardcode — sửa hằng `PIPELINE`
   nếu máy 2 để h2dev ở ổ/thư mục khác).
4. **Google Sheet** `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` — ghi qua MCP `gsheets`
   (cấu hình MCP nằm ở `~/.claude`, không nằm trong repo này).

## KHÔNG nằm trong repo

- `studio_profile/` — profile Chrome 93 MB (cookie/session). Cố ý loại trừ: App-Bound Encryption
  của Chrome làm profile copy sang máy khác mất sạch cookie, nên chép cũng vô ích **và** đó là
  dữ liệu đăng nhập không được đẩy lên git. Máy 2 đăng nhập lại từ đầu.
- Mọi file credential / `.env`.
