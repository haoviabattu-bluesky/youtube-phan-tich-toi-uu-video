# BÁO CÁO PHÂN TÍCH 4 LANE — 2026-10-18

**Lệnh:** vào lane F / L / N / O kiểm tra, phân tích, báo tập nào cần sửa thumbnail + tiêu đề.
**Chạy:** 4 luồng song song, mỗi lane 1 profile riêng (F/L/O = GPM, N = AdsPower `k15wbjoo`), Chrome CDP 9222 không dùng cho 4 lane này.
**Nguồn:** YouTube Studio (impressions/CTR/retention/traffic) + YouTube Data API (view/like/comment/publishedAt) + bảng số theo ngày.
**Snapshot CSV:** 57 dòng mới (F 18 · L 18 · N 11 · O 10) · backup trước khi ghi: `reports/backup_metrics_20261018_1420_truoc_4lane.csv`

---

## 0. GIỚI HẠN DỮ LIỆU

| Vấn đề | Số đo | Ảnh hưởng |
|---|---|---|
| Studio còn "2 days of data still processing" | Bảng theo ngày chỉ tới **2026-10-16** | Ngày 17–18 chưa có số; "24h gần nhất" theo ngày = 10-16 |
| `hours_since_publish` tính từ 00:00 ngày đăng | Cộng tối đa +17,5h | Tôi tính lại tuổi từ `publishedAt` của API cho mọi kết luận |
| 1 video L không đọc được | `xIUVlWyZPiU` — API trả 404 (riêng tư/đã xoá/hẹn giờ) | Không phân tích, không đánh dấu |
| **CTR 24h dùng để xét = cột Q (24h trượt now−24h..now)** | Theo anh chốt 2026-10-18 | Khác `ctr_last_24h` (theo ngày) — 2 số có thể lệch hẳn |

---

## 1. LANE_BASELINE (chỉ video ≥48h)

| Chỉ số | F (n=16) | L (n=16) | N (n=9) | O (n=8) |
|---|---|---|---|---|
| median CTR | **6,3%** | 4,1% | 3,0% | **6,65%** |
| median CTR 24h (trượt) | 6,7% | 3,5% | 3,8% | 6,05% |
| median AVD | 393s | 276s | 344s | **475s** |
| median APV | 26,3% | 27,5% | **30,2%** | **40,7%** |
| median ret30 | 67% | 57,5% | 62% | 66,5% |
| median recommendation | 97,1% | 97,6% | **99,2%** | 96,8% |
| median browse / suggested | 86,2 / 9,8 | 89,5 / 8,6 | 60,8 / **35,4** | 76,7 / 17,4 |
| median search | 2,3% | 0,5% | 0,8% | 0,8% |

**Đọc baseline:**
- **O là lane khoẻ nhất**: CTR 6,65% + APV 40,7% + AVD 475s — cả packaging lẫn body đều trên chuẩn.
- **F có CTR cao nhất nhưng APV thấp nhất trong 3 lane lớn** (26,3%) — click tốt, giữ chân trung bình.
- **N có APV tốt (30,2%) nhưng CTR thấp nhất (3,0%)** — ngược lại F: nội dung giữ người, packaging yếu.
- Search <5% ở **cả 4 lane** ⇒ IMMATERIAL, không diễn giải keyword (đúng luật SOP).

---

## 2. KẾT QUẢ: 4 TẬP CẦN SỬA (đã ghi sheet + tô vàng)

| Lane | Tập | video_id | Tuổi | Imp | CTR tổng | **CTR 24h (Q)** | Imp 24h | View | Kết luận |
|---|---|---|---|---|---|---|---|---|---|
| **L** | ep05 | `7YoIs7L8c_w` | 469h | 19.600 | 3,8% | **— (40 hiển thị)** | 40 | 6.200 | SỬA |
| **L** | ep08 | `iHbgfMd8Mbk` | 277h | 10.900 | 3,8% | **2,4%** | 247 | 1.800 | SỬA |
| **N** | ep01 | `EvdfvywqDc8` | 277h | 5.500 | 3,1% | **2,0%** | 50 | 863 | SỬA |
| **N** | ep04 | `oXCuQVjE4jQ` | 182h | 6.100 | 0,8% | **— (15 hiển thị)** | 15 | 80 | SỬA |

**F: 0 tập cần sửa. O: 0 tập cần sửa.** Mọi video ≥48h của F đều có CTR 24h ≥ 3,8%; O ≥ 4,8%.

Đã ghi và **đọc lại sheet xác minh**:
- `L-shakai-no-naze` dòng 6 (ep05), dòng 9 (ep08) → cột K + vàng ✅
- `Lane-N` dòng 2 (ep01), dòng 5 (ep04) → cột K + vàng ✅
- TONGHOP: `Ep05 C8`, `Ep08 C11` (lane L) · `Ep01 D4`, `Ep04 D7` (lane N) → `SỬA CTR` ✅
- Backup: `backup_sheet_{L-shakai-no-naze,Lane-N}_2026-10-18_truoc_ghi_K{6,9,2,5}.json` + `backup_TONGHOP_2026-10-18_truoc_ghi_{tab}.json`

---

## 3. VÌ SAO 4 TẬP NÀY — và sửa cái gì

### L ep05 `7YoIs7L8c_w` — なぜ真面目に働いても、暮らしは楽にならないのか
```
Imp 19.600 (lane median 13.600) · CTR tổng 3,8% · CTR 24h "—" (chỉ 40 hiển thị/24h)
Rec 98,1% · Browse 97,2% · AVD 168s · APV 15,4% · ret30 49%
→ Đã được YouTube đẩy mạnh rồi TẮT. Impressions 24h chỉ còn 40.
```
**Nút thắt kép: BODY + PACKAGING.** APV 15,4% (median lane 27,5%) và ret30 49% (median 57,5%) là thấp nhất lane — nhưng CTR 3,8% vẫn quanh median. Nghĩa là **click được, xem không hết** ⇒ YouTube ngừng đẩy. Đổi thumbnail/tiêu đề chỉ chữa được nửa vấn đề; thân bài mới là gốc.
**Ưu tiên:** thumbnail trước (1 biến), nhưng ghi nhận đây là tập cần BODY_REVIEW.

### L ep08 `iHbgfMd8Mbk` — 義父と嫁は、なぜ「当たり前」でぶつかるのか
```
Imp 10.900 · CTR tổng 3,8% · CTR 24h 2,4% · imp 24h 247 · APV 29,1% · ret30 63%
Rec 97,3% · Browse 81,2% · Suggested 16,1%
```
**Nút thắt: PACKAGING.** Body tốt (APV 29,1% > median 27,5%, ret30 63% > 57,5%) nhưng CTR 24h 2,4% < 2,5%. Đây là ca **"CTR thấp + retention cao"** (mục 15 SOP) ⇒ **THUMBNAIL_REVIEW / TITLE_REVIEW**, không đụng body.

### N ep01 `EvdfvywqDc8` — 都合よく使われない60代男性が、絶対に言わない一言
```
Imp 5.500 · CTR tổng 3,1% · CTR 24h 2,0% · imp 24h 50 · APV 16,7% · ret30 62%
Rec 99,2% · Browse 89,3% · Suggested 9,3% · like 0
```
**Nút thắt: PACKAGING + BODY.** APV 16,7% (median N 30,2%) = giữ chân kém nhất lane; CTR 24h 2,0%. Lưu ý: ô K ghi "TIÊU ĐỀ MÔ TẢ + THUMB ĐÃ SỬA XONG 17/10 sửa 3 lần" — **đã sửa 3 lần mà CTR vẫn 2,0%**, nên lần này phải đổi **hướng khác** (concept thumbnail), không phải chỉnh lại lần 4.

### N ep04 `oXCuQVjE4jQ` — 人はなぜ「収入」が減ると、自分の価値まで疑ってしまうのか
```
Imp 6.100 · CTR tổng 0,8% · CTR 24h "—" (15 hiển thị) · View 80 · like 0 · comment 0
Rec 99,4% · Browse 10,0% · Suggested 80,0% (!)
```
**Ca nặng nhất 4 lane.** CTR 0,8% là mức gần như không ai click, dù YouTube đẩy 6.100 lần và **80% traffic đến từ Suggested**. Body ổn (APV 28,1%). ⇒ **Thuần PACKAGING**: thumbnail/tiêu đề không khớp nội dung video đang được gợi ý cạnh. Đây cũng là tập duy nhất toàn lane có Suggested > Browse — dấu hiệu bị đặt cạnh tệp khán giả khác.

---

## 4. TẬP GẦN NGƯỠNG — theo dõi, CHƯA sửa

| Lane | Tập | CTR 24h | Vì sao chưa sửa |
|---|---|---|---|
| L | ep07 `oljpMKOsZ0M` | 2,6% | Trên 2,5% nhưng imp 24h 942 ⇒ nếu tụt <2,5% lần sau thì sửa |
| L | ep01 `VE_CE60s40I` | 2,7% | 1.000 imp/24h, CTR gần ngưỡng |
| L | ep15 `9DXfxfghhEU` | 2,8% | CTR tổng 2,3% thấp, nhưng 24h 2,8% ⇒ GIỮ theo luật |
| N | ep05 `zl-rXzd4zZQ` | 3,9% | CTR tổng 2,6% nhưng 24h 3,9% ⇒ GIỮ |
| F | ep18 `XS4solt4RVk` | 3,8% | Chỉ 38h — **chưa đủ 48h** |
| F | ep17 `c7BAsPkpPcc` | — | 14h, 650 imp — chưa xét |
| L | ep17 `nDuj3Ovhwcc` | 1,5% | 38h — **chưa đủ 48h** (CTR tổng 1,3% rất thấp, cần xem lại sau 48h) |
| N | ep11 `RypJKGCiDY8` | — | 14h, 17 imp — NOT_TESTED |

---

## 5. TOP_PATTERNS 4 LANE

1. **F và O không có tập nào cần sửa.** F: 16/16 video ≥48h có CTR 24h ≥3,8%. O: 8/8 ≥4,8%. Đây là 2 lane packaging đang ổn định — đừng đụng.
2. **N là lane yếu nhất về packaging**: CTR median 3,0% (thấp nhất), 2/9 tập dưới ngưỡng, và ep04 có CTR 0,8% với **80% traffic từ Suggested** — bị ghép sai tệp khán giả.
3. **L có mẫu hình "được đẩy rồi tắt"**: ep05 (19.600 imp → 40/24h) và ep07 (21.000 imp → 942/24h) đều tụt sâu, cả hai đều có APV thấp (15,4% và 31,0%). Body là nút thắt thật của L, không phải thumbnail.
4. **Sửa 3 lần vẫn không cứu được** (N ep01, ep04 đều ghi "sửa 3 lần" ngày 17/10) ⇒ lần tới phải đổi **concept**, không tinh chỉnh.
5. **Like/1k view phân hoá rõ**: O 3,8–14 · F 0,2–9,2 · L 0,6–17,9 · N 0–76,9. Nhiều tập N và F có 0 like dù vài trăm view — tương tác yếu, nhưng mẫu nhỏ, chưa kết luận.

---

## 6. PRIORITY_ACTIONS

1. **N ep04 `oXCuQVjE4jQ` — ưu tiên số 1.** CTR 0,8% với 6.100 impressions và 80% Suggested. Làm lại thumbnail theo concept mới (không chỉnh bản cũ), và kiểm tra video nào đang suggest nó để biết đang bị đặt cạnh tệp nào.
2. **N ep01 `EvdfvywqDc8` — đổi concept thumbnail.** Đã sửa 3 lần vẫn 2,0% ⇒ giữ tiêu đề, đổi hẳn hình.
3. **L ep08 `iHbgfMd8Mbk` — chỉ sửa packaging.** Body tốt (APV 29,1%, ret30 63%), đây là ca sửa rẻ nhất, khả năng cao có kết quả.
4. **L ep05 `7YoIs7L8c_w` — sửa thumbnail nhưng ghi nhận BODY_REVIEW.** APV 15,4% là gốc rễ; đổi ảnh chỉ chữa phần ngọn.
5. **Đừng đụng F và O.** 0 tập dưới ngưỡng.

---

## 7. FILE ĐÃ ĐỘNG VÀO

| File | Việc |
|---|---|
| `youtube_postpublish_metrics.csv` | +57 dòng snapshot 2026-10-18 (backup `backup_metrics_20261018_1420_truoc_4lane.csv`) |
| Sheet tab `L-shakai-no-naze` | K6, K9 + vàng 2 dòng |
| Sheet tab `Lane-N` | K2, K5 + vàng 2 dòng |
| Sheet tab `TONGHOP` | `Ep05 C8`, `Ep08 C11`, `Ep01 D4`, `Ep04 D7` = SỬA CTR |
| `reports/collect_lane_by_ids.py` | Tool mới: thu số 1 lane theo danh sách video_id (dùng cho mọi lane) |
| `reports/collect_rolling24h.py` | Tool mới: thu CTR 24h trượt (cột Q) cho danh sách video_id |
| `reports/decide_4lanes.py` | Bảng quyết định tập nào cần sửa |
| `reports/apply_marks_4lanes.py` | Ghi K + vàng + TONGHOP (có `--dry-run`) |
| `reports/rolling24h_<lane>_2026-10-18.json` | Số CTR 24h trượt từng lane (57/57 video) |

**Không đụng:** YouTube (0 thay đổi), cột E/G/L/N–S (giữ nguyên).
