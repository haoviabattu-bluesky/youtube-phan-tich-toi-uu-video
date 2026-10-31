# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Bản chất dự án

Không có git, không có package manager, không có test suite. Dự án gồm 3 phần:

- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\YOUTUBE_POSTPUBLISH_ANALYTICS_SOP.md`
  — SOP phân tích hiệu suất video sau khi đăng (30 mục). **Đây là luật, đọc trước khi phân tích.**
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\studio_collect.py`
  — tool gom số từ YouTube Studio qua GPMLogin + Playwright CDP (xem mục Dữ liệu).
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\youtube_postpublish_metrics.csv`
  — sổ số liệu, mỗi dòng = 1 video × 1 mốc snapshot.

Video cần phân tích là **kênh của chính user**, sản xuất bởi dự án `E:\CLAUDE\YOUTUBE\h2dev`
(nhiều lane song song). Vai trò của Claude ở đây là **chạy SOP như một analyst** rồi trả action
về đúng lane sản xuất — không phải viết app mới.

## Khung phân tích bắt buộc (đọc SOP để biết chi tiết + ngưỡng)

Thứ tự phân tích là cố định, không được đảo:

```
DISTRIBUTION → TRAFFIC MODE → PACKAGING (CTR) → HOOK (ret 5/10/20/30/60s) → BODY (AVD/APV)
→ SUGGESTED NEIGHBORHOOD → SEARCH → PRIMARY BOTTLENECK → 1 ACTION
```

Mọi video phải trả đủ 5 status + bottleneck + action (mục 19–20 của SOP). Chỉ **một**
`recommended_action` chính cho mỗi video, chọn từ danh sách đóng ở mục 20.

## Luật cứng — vi phạm là báo cáo sai

Những điều này là lý do SOP tồn tại; đừng "tối giản" chúng khi phân tích nhanh:

- **Đọc distribution TRƯỚC CTR.** Impressions < 100 ⇒ `NOT_TESTED` + `INSUFFICIENT_DATA`,
  tuyệt đối không kết luận thumbnail xấu.
- **Không có rule "CTR < 5% thì thay thumbnail".** Thumbnail review cần đồng thời:
  impressions ≈250–500+, recommendation cao, CTR ≲3–4%, đường impressions đã stall.
- **Không so hai video ở tuổi khác nhau** (chỉ A@48h vs B@48h).
- **Search < 5% ⇒ IMMATERIAL**: không diễn giải % keyword (25% của 0.4% traffic có thể là 1 view).
- **AVD không đọc một mình** — luôn kèm `video_length` + APV.
- **CTR không dùng để chẩn đoán hook**; hook chỉ đọc bằng retention 0–30s.
- **Suggested ≥ 40% ⇒ bắt buộc** thu "Content suggesting this video" (video + channel nguồn).
- **Ngưỡng chung chỉ là tạm**: có ≥10 video cùng lane thì baseline/median của lane thắng
  ngưỡng chung (mục 17). Không kết luận pattern từ 1–2 video.
- **Không đề xuất DELETE_VIDEO / REUPLOAD_VIDEO** vì view thấp.
- **A/B chỉ đổi một biến** mỗi lần (thumbnail HOẶC title, không cả hai).

## Dữ liệu — ĐÃ THÔNG ĐƯỜNG (verify thật 2026-09-23)

Số liệu gốc là **YouTube Studio Analytics của kênh mình** (impressions/CTR KHÔNG có trong
YouTube Analytics API công khai). Đọc bằng cách mở profile GPMLogin → Playwright CDP → Studio,
đúng như người thật xem:

```
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\studio_collect.py --mail <mail kênh> --lane <mã lane>
py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\studio_collect.py --ws ws://localhost:<port>/devtools/browser/<id> --channel UC... --lane <mã lane>
```

Ghi nối tiếp vào `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\youtube_postpublish_metrics.csv`
(schema mục 22 + 6 cột SOP còn thiếu: `direct_pct`, `title`, `topic`, `thumbnail_version`,
`title_version`, `hook_type`, `top_search_term_1`).

**BỐN BẪY ĐÃ TRẢ GIÁ — đừng "dọn cho gọn" lại:**
1. **Nội dung Studio nằm trong SHADOW DOM** (Polymer). `page.inner_text("body")` chỉ trả 237 ký tự
   rỗng tuếch trong khi `page.content()` là 5,4 MB → phải duyệt đệ quy `shadowRoot` (hàm `DEEP`
   trong tool). Nhìn qua rất giống "trang chưa tải xong" nên dễ đi chữa nhầm chỗ.
2. **Tab Reach là `tab-reach_viewers`, KHÔNG phải `tab-reach`.** Vào `/analytics/tab-reach/...`
   ra "Oops, something went wrong" vĩnh viễn (không log lỗi mạng, không console error) — dễ tưởng
   hỏng tài khoản/proxy. Tool đi đường an toàn: mở `tab-overview` rồi **bấm chữ "Reach"** như người.
3. **GPM `start` trả `success` nhưng `websocket_debugging_url` RỖNG** khi profile đang mở dở, và
   profile mở TAY từ UI GPM thì **không có `--remote-debugging-port`** → không attach được.
   Cách xử lý: `profiles/stop/<id>` → chờ → đóng nốt tiến trình chrome **của đúng profile đó theo PID**
   (đối chiếu `--user-data-dir` chứa id) → `start` lại. Không bao giờ `taskkill` theo tên chrome.exe.
4. **`—` trên Studio là "chưa có dữ liệu", không phải 0.** Video 6 impressions thì CTR/AVD/APV đều
   là `—`; ô trống trong CSV mang nghĩa đó, đừng điền 0 rồi tính median.

5. **Lần `goto` ĐẦU vào `studio.youtube.com` hay đứng lại ở ROOT**, lần thứ hai mới nhảy vào
   `/channel/<id>`. Chờ lâu hơn không cứu được — phải **goto lại**. Bỏ qua bẫy này thì 6 kênh
   đang đăng nhập bình thường bị báo oan là "CHƯA LOGIN".
6. **Tên profile GPM có thể CÓ hoặc KHÔNG có đuôi `@gmail.com`** (`haoviabattu` vs
   `AmmarHilham@gmail.com`). Khớp tuyệt đối với mail đầy đủ là trượt — phải dò cả phần trước `@`.

### Bản đồ lane ↔ mail ↔ channel id (quét thật 2026-09-23, `tools\scan_channels.py`)

| Lane | Mail = tên profile GPM | Channel ID | Video đã đăng |
|---|---|---|---|
| satori-jp-obaa | LopezzapataHilla@gmail.com | UC9huXCiBIXBfUh11D7ZsFSA | **8** |
| irogatatarukioku | AmmarHilham@gmail.com | UCtRuxojb7218QeFBf5TBCQQ | **3** |
| toshi-densetsu-jp (tab sheet `shinya_shiryoshitsu`) | haoviabattu@gmail.com — **KHÔNG qua GPM**, Chrome riêng (xem dưới) | UCYhbfP8greeTOL-0B_-OqLQ | 4 (theo sheet) |
| kenko-chiebukuro | normaneileenpm218@gmail.com | UCwdrP4WLHmmtYqf8QcxcFKg | 0 |
| teinengo-real | VirgiliTraino95@gmail.com | UCIimxP275YufOXXIlu9y9Lg | 0 |
| teinengo-tanoshimi | cobbytheona159@gmail.com | UClETn8eAXgRRKM4PkYEKzvA | 0 |
| kokoro-kazoku | FuentesMitsy202@gmail.com | UClHVEGr-4pG0CDW_YUKJ26g | 0 |
| sengoku-uragawa | AldenorRodrigues626@gmail.com | UCxBOdUsVT8g8WnpvJ8SdjyQ | 0 |
| teinengo-fuufu | MinyardJuan231@gmail.com | UC6IkfxpGTksDdzG3ENYbVdg | 0 |

Quét lại bất cứ lúc nào: `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO	ools\scan_channels.py`
(kết quả ghi `scan_channels.json`).

**Ngoại lệ kênh shinya (`haoviabattu@gmail.com`, kiểm 2026-09-23):** mail này KHÔNG login được
trong GPM (bảo mật) nên dùng **Chrome profile riêng** do dự án `E:\CLAUDE\YOUTUBE\AUTO_LIST` lập
(`project\config.json` → `channels.shinya_shiryoshitsu`, `via: local`). scan_channels.py quét GPM
nên sẽ báo "chưa đăng nhập" — đó là báo OAN, không phải lỗi.

- Thư mục profile: `E:\CLAUDE\YOUTUBE\HAOVIABATTU_PROFILE` · cổng CDP cố định **9222**
- Mở (đúng lệnh cũ, chạy nền, không tạo profile mới):
  `chrome.exe --user-data-dir=E:\CLAUDE\YOUTUBE\HAOVIABATTU_PROFILE --remote-debugging-port=9222 --no-first-run`
- Thu số: `py -3.13 tools\studio_collect.py --port 9222 --channel UCYhbfP8greeTOL-0B_-OqLQ --lane toshi-densetsu-jp`
- Profile này dùng chung với AUTO_LIST (upload/đặt lịch) → trước khi mở kiểm cổng 9222; đang có
  Chrome của nó chạy thì chỉ attach, KHÔNG đóng (có thể AUTO_LIST đang upload dở).

## Quan hệ với các dự án YouTube khác cùng máy

Dự án này là **vòng phản hồi** cho pipeline sản xuất nằm ở các thư mục anh em trong
`E:\CLAUDE\YOUTUBE\` (ví dụ `h2dev`, `VIDEO_VEO3`, `GROK_VIDEO`, `THUMBNAIL`). Khi kết luận
ra action, viết nó theo hướng đổi được ở tầng sản xuất tương ứng:

- `THUMBNAIL_REVIEW` / `PACKAGING_REVIEW` → skill `youtube-thumbnail`
- `HOOK_REVIEW` / `BODY_REVIEW` → skill `youtube-script` (hook 0–30s, nhịp thân bài)
- `TOPIC_REVIEW` / `AUDIENCE_MATCH_REVIEW` → skill `youtube-produce`, `youtube-series-builder`

## ⛔ VAI TRÒ: CHỈ PHÂN TÍCH + ĐÁNH DẤU LÊN SHEET (anh chốt 2026-09-23)

Claude **KHÔNG tự đổi title/description/thumbnail trên YouTube**, không dựng ảnh, không đụng Studio
để sửa. Việc của Claude là: đọc chỉ số → kết luận đạt/không đạt → **ghi yêu cầu vào Google Sheet**.
Anh là người quyết định và thực hiện thay đổi.

### Luật đánh dấu (anh chốt, thay cho ngưỡng CTR mềm ở mục 6 của SOP)

```
Video đã đăng ≥ 48h:
    nếu KHÔNG CÓ VIEW  hoặc  CTR < 2,5%
        → ghi "CẦN THAY ĐỔI" vào cột E (TITLE-DESCREPTION) và cột G (THUMBNAIL)
          của ĐÚNG dòng tập đó, trong tab = tên lane

Anh sửa xong sẽ tự ghi đè: "thay đổi tiêu đề {giờ} ngày/tháng" (và tương tự cho thumbnail)

Sau mốc đó, cứ mỗi 24h kiểm lại:
    CTR 24h vẫn < 2,5%  → ghi "CẦN THAY ĐỔI" tiếp (lặp không giới hạn)
    CTR > 2,5%          → ĐỂ NGUYÊN, ngừng đánh dấu
```

**24h gần nhất 0 VIEW ⇒ CHỈ ghi "CẦN THAY ĐỔI" vào cột G (THUMBNAIL), cột E (tiêu đề) GIỮ
NGUYÊN** (anh chốt 2026-09-23). Luật này ưu tiên hơn luật CTR ở trên. Tóm lại, với video ≥48h:

| 24h gần nhất | Ghi vào | `mark_needed` |
|---|---|---|
| (bất kể) tổng view lifetime **> 1000** | KHÔNG ghi — tạm chưa xét, anh sẽ nhắc khi cần (chốt 2026-09-23) | `BO_QUA_1000` |
| 0 view | chỉ G | `THUMB` |
| có view, CTR < 2,5% hoặc `—` | E + G | `TITLE+THUMB` |
| CTR ≥ 2,5% | không ghi | `NO` |

**CTR TỔNG < 2,5% nhưng CTR 24H ≥ 2,5% ⇒ GIỮ, không cần thay** (anh chốt 2026-09-23). Nếu ô
đang ghi "CẦN THAY ĐỔI" từ lượt trước thì trả E/G về tiêu đề + link thumbnail cũ (lấy từ file backup,
đối chiếu tiêu đề live trước khi ghi). Cách xử lý này chỉ áp cho trường hợp đó; mọi trường hợp khác
vẫn không tự xoá dấu. **Ô nào anh đã tự ghi chữ khác (vd E8 "ok không cần thay") thì KHÔNG ghi đè**;
trước khi ghi luôn kiểm ô vẫn đúng là "CẦN THAY ĐỔI".

"View" ở đây là tổng view của ngày (cột Views trong bảng theo ngày), không phải view tính từ impressions.

**CTR hiện `—` (chưa có dữ liệu / ít impressions) = CTR 0 ⇒ VẪN ĐÁNH DẤU** (anh chốt 2026-09-23).
Luật `NOT_TESTED` / "impressions < 100 thì không kết luận thumbnail" của SOP CHỈ áp cho phần
phân tích trong báo cáo, KHÔNG được dùng để bỏ qua việc đánh dấu sheet. Video ≥48h mà CTR `—`
hoặc < 2,5% là ghi "CẦN THAY ĐỔI", không ngoại lệ.

**CTR để xét là CTR 24H GẦN NHẤT, KHÔNG PHẢI CTR LIFETIME** (anh chốt 2026-09-23, theo
`YOUTUBE_24H_48H_72H_RECOVERY_SOP.txt`). Vết xe đổ: Valentich có CTR lifetime 2,6% trông như đạt,
nhưng từ 17/09 trở đi mỗi ngày chỉ 1–3 impressions, CTR 0%, 0 view — video đã chết mà em không đánh dấu.
Số theo ngày lấy ở Advanced mode, chia theo ngày (đọc bằng DEEP, bảng xếp ngày mới nhất trước):
`https://studio.youtube.com/video/<ID>/analytics/tab-reach_viewers/period-default/explore?entity_type=VIDEO&entity_id=<ID>&time_period=4_weeks&explore_type=TABLE_AND_CHART&metric=VIDEO_THUMBNAIL_IMPRESSIONS&granularity=DAY&t_metrics=VIDEO_THUMBNAIL_IMPRESSIONS&t_metrics=VIDEO_THUMBNAIL_IMPRESSIONS_VTR&t_metrics=EXTERNAL_VIEWS&dimension=DAY&o_column=DAY&o_direction=ANALYTICS_ORDER_DIRECTION_DESC`
Ngày hôm nay Studio chưa có số ("still processing") → "24h gần nhất" = ngày ĐỦ số mới nhất.
Mỗi video phải báo cả LIFETIME_DIAGNOSIS lẫn CURRENT_HEALTH (last 24h / previous 24h / 48h / 72h).
`studio_collect.py` đã tự thu số này (module `tools/studio_daily.py`) và ghi thêm các cột `*_last_24h`,
`*_previous_24h`, `*_last_48h`, `*_last_72h`, `distribution_change_pct`, `current_distribution_status`,
`mark_needed`, `daily_series`. Hai bẫy trong bảng số theo ngày:
- **Ngày có 0 impression bị Studio BỎ KHỎI BẢNG.** Phải lấy ngày chốt số theo khoảng ngày
  ghi ở đầu báo cáo ("Aug 26 – Sep 22, 2026"), không lấy theo dòng cuối có trong bảng
  (`report_end_day`). Nếu không, video im lặng hôm qua sẽ bị tính "24h gần nhất" là hôm kia.
- **`hours_since_publish` tính từ 00:00 của NGÀY đăng** (Studio chỉ cho biết ngày) nên có thể
  cao hơn thật tới 17,5h. Trước khi ghi sheet, luôn kiểm mốc 48h bằng giờ đăng thật trong cột K
  ("17:30 ngày dd/mm").
- Video đã ghi "CẦN THAY ĐỔI" mà CTR 24h sau đó > 2,5% thì KHÔNG tự xoá dấu, chỉ báo cho anh.

**Cách ghi — ô chỉ chứa ĐÚNG chữ `CẦN THAY ĐỔI`, không thêm gì.** Anh chốt 2026-09-23: không
ghi kèm lý do, số liệu hay ngày giờ vào ô — ghi đè thẳng cột E và G bằng đúng 4 chữ đó. Số liệu và
lý do để trong `youtube_postpublish_metrics.csv` + báo cáo, KHÔNG nhét vào sheet. Nội dung cũ của ô
(tiêu đề, link thumbnail) được sao lưu sang `reports/backup_sheet_<tab>_<ngày>.json` TRƯỚC khi ghi
đè. Không xoá dòng/cột nào trong sheet.

**Dò đúng dòng trước khi ghi.** Cột L (ID) nhiều dòng còn trống, và **tiêu đề trên sheet có thể
KHÁC tiêu đề live** (tập nào đã đổi tên sau khi đăng thì sheet vẫn giữ tên cũ) → khớp bằng ID nếu
có, không có thì khớp bằng NGÀY ĐĂNG trong cột GHI CHÚ ("ĐÃ ĐẶT LỊCH ĐĂNG VÀO 17:30 ngày dd/mm").
Ghi xong thì **điền luôn video_id vào cột L** để lần sau khỏi đoán.

Sheet: `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` · tab = mã lane (`Lopezzapa68`,
`irogatatarukioku`, …) · header dòng 1: A=STT, E=TITLE-DESCREPTION, G=THUMBNAIL, J=ĐÃ ĐĂNG,
K=GHI CHÚ, L=ID, **N=SỐ NGÀY LIST, O=VIEW, P=CTR TỔNG, Q=CTR 24H** (anh thêm 2026-09-23, mới có ở
tab `Lopezzapa68`; ĐỌC LẠI HEADER mỗi lần — anh đã chèn cột 1 lần). Mỗi lần thu số thì điền:
N = số ngày từ lúc đăng, làm tròn (giờ đăng lấy ở K "17:30 ngày dd/mm"; K đã bị ghi đè thì ngày đăng
Studio + 17:30); O = view lifetime Studio hiện; P = CTR lifetime (Studio để `—` thì tính từ
`daily_series` = tổng click / tổng impressions); Q = `ctr_last_24h` (0 impression ⇒ 0%).
Ghi dạng số thập phân (0.074) rồi định dạng `0.0%` — sheet dùng locale VN (dấu phẩy thập phân).

## Định dạng báo cáo

Dùng nguyên khung mục 23 (per-video), 24 (bảng so sánh trong kênh) và 29 (output cuối:
LANE_BASELINE → PER_VIDEO_REPORT → CHANNEL_COMPARISON → SUGGESTED_NEIGHBORHOOD →
SEARCH_FINDINGS → TOP_PATTERNS → PRIORITY_ACTIONS 1-2-3). Tiếng Việt, giữ tên field/status
nguyên dạng tiếng Anh in hoa như SOP viết.
