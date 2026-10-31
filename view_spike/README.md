# view_spike — báo khi video mới đăng đạt ≥1000 view/giờ (Studio)

Anh duyệt 2026-10-15. Plan: `plans/261015-1647-view-spike-alert/`.

## Chạy
| Lệnh | Việc |
|---|---|
| (tự động) Task Scheduler `ViewSpikeWatch` mỗi 15 phút | `pythonw spike_watch.py` — không cửa sổ |
| `py -3.13 spike_watch.py --dry-run` | chỉ tầng 1, in bảng, không mở Studio/không toast |
| `py -3.13 spike_watch.py --force ID,ID --alert 10` | TEST: ép kiểm Studio + hạ ngưỡng, toast có nhãn (TEST) |
| `py -3.13 spike_watch.py --test-toast` | bật 1 toast thử |
| `schtasks /Change /TN ViewSpikeWatch /DISABLE` (`/ENABLE`) | tạm tắt / bật lại |

## Luồng
1. **Tầng 1 (API, 1 unit/vòng ≈ 96 unit/ngày, 0 token LLM):** sheet cột L của các tab trong
   `config.json` → mỗi lane 2 video mới nhất còn ≤72h → `viewCount` → view/giờ công khai
   (so với snapshot cách ~60 phút; lần đầu = view / tuổi video). ≥ **300** ⇒ NGHI.
2. **Tầng 2 (Studio, chỉ video NGHI, tối đa 1 lần/giờ/video):** mở đúng profile → thẻ Realtime:
   - video mới: "N · Views · Last 60 minutes" ⇒ view/giờ = N
   - video cũ hơn: rê chuột 2 cột phải nhất của biểu đồ 48h ⇒ max(giờ hiện tại, giờ trọn gần nhất)
   ≥ **1000** ⇒ toast 🔥 + `state/alerts.jsonl` (mỗi video tối đa 1 lần / 6 giờ).
3. Không mở được Studio (profile đang bận / lane chưa có profile) ⇒ toast ⚠️ "nghi đang lên" kèm
   số API (tối đa 1 lần / 3 giờ / video).

## Số đo thật 2026-10-15
- API công khai thấp hơn Studio ~26% (604 vs 815; 911 vs 1236) ⇒ ngưỡng tầng 1 = 300.
- Vòng chỉ tầng 1: 0,6–0,8 s. Mở 1 profile GPM + đọc: ~45–100 s. Chrome 9222: ~20 s.

## Lane không mở được tầng 2 (mail = null trong config.json)
Lane-J (lethientan26061994 — không có trong GPM), Lane-N (thienduongly7890 — không có trong GPM),
Lane-O (@人生のつづき — không có trong tab GMAIL). Có profile thì điền `mail` vào config.json.

## File
`spike_watch.py` (CLI) · `spike_sources.py` (sheet + API, cache ngày đăng ở `state/meta.json`) ·
`spike_state.py` (snapshot, view/giờ, cooldown, khoá) · `spike_studio_realtime.py` (tầng 2) ·
`spike_notify.py` (toast) · `probe_*.py` (script đo Phase 1, giữ để tham khảo).
Log: `state/spike_watch.log`.

## Luật an toàn
`ProfileUsingByOther` → không đóng/kill, chỉ báo. Chỉ đóng profile GPM mà tool vừa mở; Chrome 9222
chỉ đóng nếu chính tool vừa mở nó. Không ghi Google Sheet, không sửa gì trên YouTube.

## Tắt theo dõi 1 video
Thêm `"exclude": ["<video_id>"]` vào lane trong `config.json` (vd Lane-P bỏ tập 2 `Y7TiikwCrtU`, 2026-10-16).
Vòng 15 phút kế tiếp tự áp dụng, không cần khởi động lại task.
