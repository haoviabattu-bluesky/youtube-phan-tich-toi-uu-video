---
title: View spike alert — plan
created: 2026-10-15
status: draft (chờ anh duyệt)
---

# Plan — 4 phase

| Phase | Nội dung | Kết quả kiểm được | Trạng thái |
|---|---|---|---|
| 01 | **Spike rủi ro**: tìm cách đọc view/giờ trong Studio + đo lệch API↔Studio trên 1–2 video thật | đọc được (text 60m + hover cột 48h); API thấp hơn Studio ~26% | ✅ 2026-10-15 |
| 02 | Tầng 1 (API): sheet → 2 video mới nhất/lane ≤72h → snapshot → view/giờ → NGHI (≥300) | `--dry-run`: 12 video / 14 tab, 1 unit, 0,6 s; Lane-P Y7TiikwCrtU 582/giờ ⇒ NGHI | ✅ 2026-10-15 |
| 03 | Tầng 2 (Studio) + báo | test `--alert 10`: M (9222) 48h-hover 134/giờ, F (GPM) 60m 22/giờ → 2 toast; Lane-P PROFILE_BUSY → không đụng, toast ⚠️; profile F đóng lại (0 tiến trình) | ✅ 2026-10-15 |
| 04 | Task Scheduler `ViewSpikeWatch` 15 phút, pythonw, khoá run.lock, README + CLAUDE.md | `schtasks /Run` → Last Result 0, vòng 83 s | ✅ (chưa có số chạy 24h) |

## Cấu trúc file dự kiến (mỗi file ≤200 dòng)
```
view_spike/
  spike_watch.py            CLI: --once / --dry-run / --threshold / --suspect
  spike_sources.py          đọc sheet tab lane + Data API videos.list
  spike_state.py            snapshots.jsonl, tính view/giờ, cooldown, khoá file
  spike_studio_realtime.py  mở profile (tái dùng gpm_* của tools/) + đọc Realtime qua DEEP
  spike_notify.py           toast Windows + alerts.jsonl (+ Telegram nếu anh chọn)
  config.yaml               ngưỡng, lane → mail/cổng, cửa sổ thời gian
  state/                    snapshots.jsonl, alerts.jsonl, run.lock
```
Tái dùng: `DEEP` + `gpm_find/start/stop` (tools/studio_collect.py), đọc key như comment_care.

## Sau mỗi phase
Smoke test có số đo thật → ghi frontmatter phase `status: completed` → DỪNG chờ anh xác nhận.
