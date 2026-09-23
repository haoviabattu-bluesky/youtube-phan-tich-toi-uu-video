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
3. **Dự án anh em `h2dev`** phải có mặt: `tools\sol_packaging_review.py` cần
   `h2dev\pipeline\sol_client.py`. Đường dẫn **tự dò** (hàm `_find_pipeline`), thử theo thứ tự:
   biến môi trường `H2DEV_PIPELINE` → `<thư mục cha>\h2dev\pipeline` →
   `<thư mục cha>\YOUTUBE\h2dev\pipeline` → lùi thêm một cấp nữa.
   Nên chạy được cả khi h2dev nằm ở `E:\CLAUDE\YOUTUBE\h2dev` (máy 1) lẫn `E:\CLAUDE\h2dev` (máy 2).
   Nếu để chỗ khác hẳn thì đặt biến môi trường:
   ```
   setx H2DEV_PIPELINE "D:\duong\dan\h2dev\pipeline"
   ```
4. **Google Sheet** `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` — ghi qua MCP `gsheets`
   (cấu hình MCP nằm ở `~/.claude`, không nằm trong repo này).

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
và trạng thái đăng nhập của 9 profile. Chạy trôi + ghi ra `scan_channels.json` có channel id
là máy đã sẵn sàng. Profile nào báo chưa đăng nhập thì mở
`py -3.13 tools\open_studio_profile.py` rồi đăng nhập tay một lần.
