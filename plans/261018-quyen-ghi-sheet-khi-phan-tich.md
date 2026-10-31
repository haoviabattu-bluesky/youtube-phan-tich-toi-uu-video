# QUY TẮC: quyền ghi sheet khi anh ra lệnh phân tích (chốt 2026-10-18)

> Trạng thái: **ĐANG ÁP DỤNG**. Chờ anh duyệt để chép nguyên khối này vào `CLAUDE.md`
> (mục "⛔ LUẬT ĐÁNH DẤU — CHỈ CỘT K, TÔ VÀNG"), vì ghi `CLAUDE.md` cần anh bấm duyệt.

## Luật

Khi anh báo lệnh kiểu *"vào lane X kiểm tra / phân tích video"*, Claude **ĐƯỢC PHÉP tự làm 3 việc, không hỏi lại**:

```
1. Tô nền VÀNG (backgroundColor 1,1,0) CẢ DÒNG của tập vi phạm — trong tab lane
2. Ghi cột K của đúng dòng đó: chuỗi CTR 24h + "YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ"
   → dùng nguyên hàm tools\daily_k_rules.py :: k_note(), KHÔNG tự đặt câu khác
3. Sang tab TONGHOP: ghi "SỬA CTR" vào ô giao
   (cột = tên tab lane ở DÒNG 1, dòng = "EpNN" ở CỘT A)
   vd lane M tập 10 → TONGHOP!F13
```

## Ràng buộc

- **Backup trước khi ghi cột K**: ô K hay có ghi chú tay của anh → lưu
  `reports\backup_sheet_<tab>_<ngày>_truoc_ghi_K<dòng>.json` (kèm cả bảng TONGHOP nếu sắp ghi).
- **Ngoài 3 việc trên KHÔNG đụng cột nào khác**: E, G, L, N–S… giữ nguyên tuyệt đối.
- Tập **<48h** hoặc **chưa có số theo ngày** ⇒ không tô, không ghi (chỉ báo WAIT_FOR_MORE_DATA).
- Việc đánh dấu này **không thay** bước sync N–Q: nếu lần phân tích có thu số mới thì vẫn chạy
  `sheet_metrics_sync.py` / `daily_0500_run.py` đúng quy trình rotate O→R, Q→S.

## Hai định nghĩa — ANH ĐÃ CHỐT 2026-10-18: theo CODE

| Câu hỏi | Chốt |
|---|---|
| "CTR 24h" để xét | **24h TRƯỢT now-24h..now = cột Q** (không dùng `ctr_last_24h`) |
| Ngoại lệ "tổng view > 1000 thì chưa xét" | **ĐÃ BỎ** — áp cho MỌI video, kể cả >1000 view |

⇒ Từ nay **`tools\daily_k_rules.py` là nguồn đúng**; `CLAUDE.md` dòng 201–207 đang ghi NGƯỢC
(dùng ngày đủ số + còn ngoại lệ 1000 view) và cần sửa cho khớp.

## Lần áp dụng đầu: lane M, 2026-10-18

Đã ghi và **đọc lại sheet xác minh** (không tin output tool):

| Tập | Dòng | CTR 24h (Q) | Cột K | Vàng |
|---|---|---|---|---|
| ep03 `VFdj45ytUaI` | 4 | 2,2% | `CTR 24h=2,2%, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ` | ✅ |
| ep07 `9Bn6J3RtCJ4` | 8 | 2,1% | `CTR 24h=2,1%, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ` | ✅ |
| ep10 `nNlqnf28Kak` | 11 | 2,0% | `CTR 24h=2,0%, YÊU CẦU THAY THUMB VÀ TIÊU ĐỀ` | ✅ |

TONGHOP cột F (lane M): `Ep03 F6`, `Ep07 F10`, `Ep10 F13` → `SỬA CTR`.

Không tô: ep01 4,5 · ep02 3,3 · ep04 3,7 · ep05 3,8 · ep06 3,6 · ep08 2,6 · ep09 7,3 (đều ≥2,5%);
ep12 (44h) và ep14 (20h) chưa đủ 48h.

Backup: `reports\backup_sheet_M-teinengo-anaba_2026-10-18_truoc_ghi_K{4,8,11}.json`
+ `reports\backup_TONGHOP_2026-10-18_truoc_ghi_laneM.json`
Script tái dùng: `reports\apply_laneM_marks.py --dry-run`

## Việc còn treo

- [ ] Anh duyệt để chép khối luật trên vào `CLAUDE.md`.
- [ ] Sửa `CLAUDE.md` dòng 201–207 cho khớp 2 điều đã chốt (đang ghi ngược với code).
