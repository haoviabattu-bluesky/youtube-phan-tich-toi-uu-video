# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Bản chất dự án

Không có git, không có package manager, không có test suite. Dự án gồm 3 phần:

- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\YOUTUBE_POSTPUBLISH_ANALYTICS_SOP.md`
  — SOP phân tích hiệu suất video sau khi đăng (30 mục). **Đây là luật, đọc trước khi phân tích.**
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\studio_collect.py`
  — tool gom số ĐẦY ĐỦ (impressions/traffic source/retention/suggesting sources…) ghi vào CSV,
  dùng khi cần báo cáo phân tích sâu theo khung SOP.
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\sheet_metrics_sync.py`
  — tool GỌN, chỉ đồng bộ 4 chỉ số N–Q (ngày/view/CTR tổng/CTR 24h) thẳng vào sheet + rotate
  R,S, dùng cho việc kiểm tra định kỳ mỗi 24h (xem mục "Cột chỉ số N–S").
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

**CHÍN BẪY ĐÃ TRẢ GIÁ — đừng "dọn cho gọn" lại:**
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
7. **YouTube Studio KHÔNG có preset "Last 24 hours" cho video analytics** (chỉ có "First 24
   hours" — CỐ ĐỊNH tại lúc đăng, vô dụng với video đã cũ). Bấm dropdown khoảng thời gian trên
   tab Reach chỉ thấy: Since published / First 24 hours / Last 7 days / Last 28/90/365 days /
   Since uploaded (lifetime) / theo tháng / Custom. **Cách lấy đúng CTR-24h-trượt (verify thật
   2026-09-25):** URL của tab Reach nhúng luôn khoảng thời gian dưới dạng epoch millisecond —
   `goto` thẳng `/video/<id>/analytics/tab-reach_viewers/period-<start_ms>,<end_ms>` với
   `start_ms = now-24h`, `end_ms = now` (tính tay bằng Python, KHÔNG cần bấm lịch/calendar UI).
   Studio tự nhận và đổ đúng số cho khoảng đó, nhãn tự đổi thành "Custom". Việc này tổng quát
   hoá được cho MỌI khoảng tuỳ ý (hôm qua, 48h, 7 ngày lệch...), không chỉ 24h.
8. **`—` xuất hiện khi mẫu quá nhỏ để Studio tính %** (vd 5 impressions trong cửa sổ 24h) —
   khác với `0,0%` khi impressions đủ lớn mà views=0. Cả hai đều là tín hiệu thật, giữ đúng quy
   ước cũ: `—` → ô trống (chưa đủ dữ liệu), `0,0%` → ghi đúng `0,0%` (0 lượt xem thật).
9. **KHÔNG CHẠY tool khi GPM báo `ProfileUsingByOther`** (anh chốt 2026-09-25) — nghĩa là
   profile đang được dùng ở nơi khác (rất có thể chính anh đang mở tay xem Studio). Cả 3 tool
   (`studio_collect.py`, `sheet_metrics_sync.py`, `scan_channels.py`) đều raise lỗi rõ ràng và
   **DỪNG LẠI** ở tình huống này — tuyệt đối không đóng/kill profile đó để chiếm lại (khác hẳn
   bẫy #3, vốn là profile do CHÍNH tool mở dở từ lần chạy trước rồi bỏ dở). Gặp lỗi này thì báo
   lại cho anh, đợi anh đóng cửa sổ đó rồi chạy lại.

### ⚠️ TAB TRONG SHEET ĐÃ ĐỔI TÊN (cập nhật 2026-09-25) — dùng bảng này, không dùng tên cũ

| Lane | **Tab hiện tại** (tên cũ) | Mail = tên profile GPM | Channel | Video đã đăng |
|---|---|---|---|---|
| Satori (人生の夕暮れ) | `Satori-Lopezzapa68` (cũ: `Lopezzapa68`) | LopezzapataHilla@gmail.com | UC9huXCiBIXBfUh11D7ZsFSA | 11 |
| A — vũ trụ (深夜の資料室) | `A-shinya_shiryoshitsu` (cũ: `shinya_shiryoshitsu`) | haoviabattu@gmail.com — **KHÔNG qua GPM**, Chrome riêng cổng 9222 (xem "Ngoại lệ kênh shinya" dưới) | UCYhbfP8greeTOL-0B_-OqLQ | ≥2 (sheet 23/09 ghi 4) |
| E (健康の知恵袋) | `E-70dai-kenko` (cũ: `70dai-kenko`) | normaneileenpm218@gmail.com | UCwdrP4WLHmmtYqf8QcxcFKg (@70dai-kenko) | 1 (ep01, lịch 24/09) |
| F (定年後のリアル) | `F-teinengo-real` (cũ: `teinengo-real`) | VirgiliTraino95@gmail.com | @teinengo-real | 0 (2 tập ghi "CẦN THAY" — mới xong packaging, chưa chắc đã đăng) |
| G (定年後の楽しみ方) | `G-teinengo-tanoshimi` (cũ: `teinengo-tanoshimi`) | cobbytheona159@gmail.com | @teinengo-tanoshimi | 1 (ep01, lịch 25/09) |
| K — 薬局スカッと (MỚI) | `K-yakkyoku-sukatto` | rosellagreysonbk920@gmail.com | **UCk8E_FHIYjY7GN_qdpSKaMw** (@yakkyoku-sukatto) — ⚠️ id cũ UCEBA1RFfkXQtqgiDVLh4bcw là kênh MẪU 千種テンカ, sửa 2026-10-05 | ~1-2, "CẦN ĐĂNG" |
| L — 社会のなぜ (MỚI) | `L-shakai-no-naze` | SyedualiBajwa92@gmail.com | **UCjy5fWoigvtCfduJDJ3jTbg** (@shakai-no-naze) — ⚠️ id cũ UCFWFKb3Yr_1SrAT0kcvwFdw là kênh MẪU 社会のウラガワ, sửa 2026-10-05 | 0, "CẦN ĐĂNG"/"CHỜ MÁY 2" |
| H (心の家族学) | `kokoro-kazoku` (không đổi tên) | FuentesMitsy202@gmail.com | UClHVEGr-4pG0CDW_YUKJ26g | 0 |
| I (戦国の裏側) | `sengoku-uragawa` (không đổi tên) | AldenorRodrigues626@gmail.com | UCxBOdUsVT8g8WnpvJ8SdjyQ | 0 |
| J (定年後の夫婦のカタチ) | `teinengo-fuufu` (không đổi tên) | MinyardJuan231@gmail.com | UC6IkfxpGTksDdzG3ENYbVdg | 0 |

⛔ **Lane D (色が語る記憶 / irogatatarukioku, mail AmmarHilham@gmail.com) — anh chốt 2026-09-25:
BỎ, KHÔNG theo dõi nữa.** Tab của nó đã không còn trong sheet (trước có tên `irogatatarukioku`,
giờ không thấy trong `list_sheets`); dòng mail trong tab GMAIL cũng chỉ còn mail/pass, các cột
NGÁCH/TÊN KÊNH/... đã trống. Không cần tìm lại tab, không đưa lane này vào bất kỳ lần sync/quét
nào nữa (đã bỏ khỏi `LANES` trong `scan_channels.py`).

Nguồn: `list_sheets` + tab GMAIL đọc lại 2026-09-25. Quét lại kênh/video bất cứ lúc nào:
`py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\scan_channels.py` (đã sửa `LANES` trỏ
đúng TÊN TAB MỚI 2026-09-25, bỏ lane D).

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

## Cột chỉ số N–S (anh chốt 2026-09-25) — chạy bằng `tools\sheet_metrics_sync.py`

Mỗi tab lane có 6 cột chỉ số cố định vị trí N→S (đã thêm header cho toàn bộ 9 tab hôm nay,
`Satori-Lopezzapa68` đã có sẵn từ trước):

| Cột | Tên | Ý nghĩa | Nguồn |
|---|---|---|---|
| N | SỐ NGÀY LIST | Số ngày kể từ khi đăng (làm tròn xuống) | Overview → "since published" date |
| O | VIEW | Tổng lượt xem (trọn đời) | Reach, khoảng "Since published" |
| P | CTR TỔNG | CTR trọn đời (from Since published) | Reach, khoảng "Since published" |
| Q | CTR 24H | CTR của đúng 24 giờ gần nhất tính từ lúc chạy (KHÔNG phải "Since published", KHÔNG phải "First 24 hours") | Reach, URL custom `period-<now-24h>,<now>` (xem bẫy #7 ở trên) |
| R | VIEW CŨ | Giá trị O của **lần chạy trước** | copy tay/tool trước khi ghi đè O |
| S | CTR 24H CŨ | Giá trị Q của **lần chạy trước** | copy tay/tool trước khi ghi đè Q |

**Quy trình BẮT BUỘC mỗi lần kiểm tra (đúng thứ tự):**
1. Đọc O, Q hiện tại của dòng → ghi (rotate) sang R, S — đây LÀ backup của lần chạy trước,
   không phải giá trị mới.
2. Mở video trên Studio, đọc lại N, O, P, Q **mới**.
3. Ghi N, O, P, Q mới đè lên giá trị cũ. R, S giữ nguyên giá trị vừa rotate ở bước 1.
4. **Mặc định KHÔNG đụng bất kỳ cột nào khác** (E, G, K, L, …) — kể cả khi phát hiện video cần
   đổi title/thumb. Việc ghi `CẦN THAY ĐỔI` vào E/G là một bước RIÊNG, chỉ làm khi anh yêu cầu
   rõ ràng (xem mục "Luật đánh dấu" dưới đây) — KHÔNG tự động bundle vào lần sync số liệu.

Chạy: `py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\sheet_metrics_sync.py --tab
Satori-Lopezzapa68 --mail LopezzapataHilla@gmail.com`. Tool tự đọc cột L (video_id) của mọi dòng
có giá trị, tự rotate O→R/Q→S, tự ghi N–Q mới. Cờ `--only id1,id2` giới hạn 1 vài video;
`--dry-run` chỉ in ra không ghi sheet — **dùng dry-run trước khi chạy hàng loạt trên tab mới**.

⚠️ Cột L trong DỮ LIỆU (từ dòng 2) LUÔN là video_id bất kể header dòng 1 ghi gì — một số tab
(E, F, G, K, L…) dùng ô L1/M1 của DÒNG 1 để ghi mail đăng nhập/URL kênh (không phải nhãn cột),
khác hẳn `Satori-Lopezzapa68`/`A-shinya_shiryoshitsu` có L1="ID" tường minh. Đọc video_id theo
**vị trí cột (index 11 = L)**, không đọc theo nhãn header.

### ⛔ LUẬT ĐÁNH DẤU MỚI — CHỈ CỘT K, TÔ VÀNG (anh chốt 2026-10-14, THAY cách ghi E/G bên dưới)

```
Video ≥ 48h, CTR 24h < 2,5%
  → ghi vào cột K (GHI CHÚ) của đúng dòng đó ĐÚNG chuỗi:  CTR 24h< 2.5- Yêu cầu thay đổi
  → tô nền ô K màu VÀNG (backgroundColor 1,1,0)
  → KHÔNG ghi "CẦN THAY ĐỔI" vào E/G nữa, KHÔNG đụng cột nào khác
```
- "CTR 24h" để xét = CTR của **ngày đủ số gần nhất** trong bảng theo ngày của Studio (cột `ctr_last_24h`
  do `studio_collect.py` thu, vd ep02 lane M ngày 12/10 = 1,7%). Cột Q (24h TRƯỢT now-24h..now) là
  khoảng thời gian KHÁC, có thể lệch hẳn (cùng video đó Q = 3,4%) — Q chỉ để xem, không dùng để đánh dấu.
  (Anh chưa chốt tường minh định nghĩa này — nếu anh nói khác thì sửa dòng này.)
- Cột K thường đang có ghi chú của anh ("TIÊU ĐỀ MÔ TẢ + THUMB ĐÃ SỬA XONG 8/10"…) → sao lưu sang
  `reports/backup_sheet_<tab>_<ngày>_truoc_ghi_K<dòng>.json` TRƯỚC khi ghi đè.
- Các ngoại lệ cũ vẫn giữ: tổng view > 1000 thì chưa xét; CTR `—` coi như 0 (vẫn đánh dấu).

### Luật đánh dấu (cũ — phần CÁCH GHI vào E/G đã bị thay bằng luật cột K ở trên)

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

**Thêm điều kiện mới (anh nêu 2026-09-25, xử lý bằng cột N–S ở trên):** một video có thể có
`CTR TỔNG` (cột P) trông ổn (>2,5%) nhưng **gần đây không còn ai xem** — CTR tổng cao chỉ vì
những giờ đầu tốt, giờ đã tắt hẳn phân phối. Đây LÀ đúng lý do có cột **CTR 24H (Q)** và
**VIEW CŨ (R)** riêng. Sau khi chạy `sheet_metrics_sync.py` để có N–Q mới + R,S (giá trị của
lần chạy trước), áp thêm:

```
IF video ≥ 48h VÀ (O == R  [không tăng view nào kể từ lần kiểm trước]
                    HOẶC Q rỗng/"—" [0 hoặc gần 0 impression trong 24h qua]
                    HOẶC Q < 2,5%)
   NGAY CẢ KHI P (CTR TỔNG) ≥ 2,5%
→ VẪN ghi "CẦN THAY ĐỔI" (đừng chỉ nhìn P rồi kết luận "để nguyên")
```

Điều kiện `O == R` chỉ áp dụng khi R **không rỗng** (đã có ít nhất 1 lần chạy trước để so sánh
— lần chạy ĐẦU TIÊN của một dòng thì R rỗng, bỏ qua điều kiện này, chỉ xét theo P như luật cũ).

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

Sheet: `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` · tab = tên đã đổi 2026-09-25, xem bảng
"TAB TRONG SHEET ĐÃ ĐỔI TÊN" ở mục Dữ liệu (`Satori-Lopezzapa68`, `A-shinya_shiryoshitsu`,
`E-70dai-kenko`, `F-teinengo-real`, `G-teinengo-tanoshimi`, `K-yakkyoku-sukatto`,
`L-shakai-no-naze`, `kokoro-kazoku`, `sengoku-uragawa`, `teinengo-fuufu`) · header dòng 1:
A=STT, E=TITLE-DESCREPTION, G=THUMBNAIL, J=ĐÃ ĐĂNG, K=GHI CHÚ, L=ID (một số tab không ghi rõ
nhãn "ID" ở L1 nhưng dữ liệu từ dòng 2 vẫn luôn đặt video_id ở đúng cột L) · N–S = chỉ số
(xem mục "Cột chỉ số N–S" ngay trên).

Cách điền khi thu số bằng `studio_collect.py` (2026-09-23):
N = số ngày từ lúc đăng, làm tròn (giờ đăng lấy ở K "17:30 ngày dd/mm"; K đã bị ghi đè thì ngày đăng
Studio + 17:30); O = view lifetime Studio hiện; P = CTR lifetime (Studio để `—` thì tính từ
`daily_series` = tổng click / tổng impressions); Q = `ctr_last_24h` (0 impression ⇒ 0%).
Ghi dạng số thập phân (0.074) rồi định dạng `0.0%` — sheet dùng locale VN (dấu phẩy thập phân).

## Định dạng báo cáo

Dùng nguyên khung mục 23 (per-video), 24 (bảng so sánh trong kênh) và 29 (output cuối:
LANE_BASELINE → PER_VIDEO_REPORT → CHANNEL_COMPARISON → SUGGESTED_NEIGHBORHOOD →
SEARCH_FINDINGS → TOP_PATTERNS → PRIORITY_ACTIONS 1-2-3). Tiếng Việt, giữ tên field/status
nguyên dạng tiếng Anh in hoa như SOP viết.

## Module `comment_care` — chăm sóc bình luận tiếng Nhật (anh duyệt triển khai 2026-10-05)

Thư mục `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\` (README trong đó; spec
`docs\superpowers\specs\2026-10-05-youtube-comment-care-design.md`; plan `plans\261005-0757-comment-care\`).
Luồng: fetch comment (Data API key) → **đọc hiểu video bắt buộc** (title/description + thư mục tập của h2dev qua Sheet cột C/L, fallback
`h2dev\FlowHandoff_local\jobs`) → classify (gemini) → Policy Engine (`policy\policy_table.yaml`, model không ghi đè được) → template | LLM
(claude-opus-5-5) → footer → QC rule + judge (gpt-5.6-sol) → `reports\comment_care\<ngày>\<tab>\DRAFT_REVIEW.txt` để anh duyệt.

Luật riêng của module (không mâu thuẫn mục "⛔ VAI TRÒ" ở trên vì **mặc định không gửi gì**):
- Gửi reply thật chỉ khi đủ 3 kill switch (env `COMMENT_CARE_AUTO_REPLY=1` + `mode: auto_*` trong `comment_care\config\channels.yaml` +
  cờ `--send`) **và** có token OAuth `youtube.force-ssl` của đúng Gmail kênh tại `D:\CLAUDE\credentials\youtube_oauth\<channel_id>.json`.
  Hiện CHƯA có token nào → tool chỉ soạn nháp. Anh là người authorize; Claude không tự tạo/đổi OAuth.
- **CÂU NHẠY CẢM KHÔNG TRẢ LỜI ĐƯỢC → 「はい、ご意見ありがとうございます。」 ("Vâng, cám ơn bạn đã góp ý") — anh chốt 2026-10-15
  (THAY luật "soạn trung lập + chờ anh duyệt" cùng ngày):** áp cho POLITICAL_SOCIAL (chính trị/xã hội/nam-nữ, kể cả phân biệt giới nặng),
  HOSTILE, và các nhóm HOSTILE/POLITICAL_SOCIAL/CRITICISM_CONSTRUCTIVE/DISAGREEMENT_POLITE khi độ tin thấp (mỉa mai, hiểu không chắc).
  Không bỏ qua, không soạn câu riêng, không footer, không chờ anh duyệt — đăng luôn rồi làm bình luận khác. Không like/tim các
  bình luận này (tim lên câu phân biệt giới/mỉa mai = kênh đồng tình). Code: `template_key: SENSITIVE` + `sensitive_fallback_categories`
  trong `policy_table.yaml`, QC miễn `duplicate_text` cho câu này. UNCLEAR (vô nghĩa) và không phải tiếng Nhật vẫn SKIP.
- Không có context video (không map được tập) → mọi category cần LLM bị SKIP, chỉ template được phép.
- Comment của chính kênh (câu hỏi ghim 👇) không bao giờ vào LLM. Mỗi thread bot reply tối đa 1 lần.
- Kênh Satori `UC9huXCiBIXBfUh11D7ZsFSA` **đã bị Google đình chỉ** (phát hiện 2026-10-05) → `enabled: false`; pilot là lane F.
- **2026-10-22 — giao cho Hermes** theo `comment_care\HUONG_DAN_HERMES.md` (lane F, L, N, O, P, Q; M tắt). Luật mới trong code:
  KHÔNG gọi Claude (`generate_use_claude: false`, soạn bằng sol→gemini); thân reply ≤50 ký tự, 1–2 câu, cấm trích dẫn lời khách/tiêu
  đề, cấm số, cấm "私も" (`reply_rules.py`, dùng chung QC + `review` từ chối câu EDIT sai luật); hỏi chế độ/không chắc/LLM lỗi →
  `コメントありがとうございます。` (template THANKS); `post-browser` tự like/tim (không like nhóm nhạy cảm) + chặn ngoài 08–22h JST
  + tự chuyển kênh cho mail chung K/O rồi chuyển về; lệnh mới `react-browser`, `thank`; `tools\verify_replies.py`
  (đối chiếu bằng API key), `tools\viet_reply.py`, `tools\keep_visible.ps1` (chạy bằng `powershell`, máy không có `pwsh`).

### Lệnh "vào lane X kiểm tra và bình luận" (anh chốt 2026-10-05)
Nghĩa là chạy trọn quy trình, không hỏi lại từng bước: (1) `cc.py run --channel X --mode draft_only` → (2) báo tiếng Việt: bảng số lượng +
đường dẫn `DRAFT_REVIEW.txt` (có dịch Việt) + đoạn **"khán giả nói gì"** (chủ đề lặp, trải nghiệm thật, câu hỏi/phản đối phổ biến, tín hiệu nhạy
cảm) + draft nào em nghi ngờ → (3) ~~chờ anh duyệt~~ — anh chốt 2026-10-08: KHÔNG cần duyệt, viết xong (ngắn, chữ đơn giản, thấu hiểu/cảm ơn, xin 1 like + 1 đăng ký) là đăng luôn; lane M tạm chưa làm → (4) `cc.py post-browser --channel X` qua
profile GPM = mail kênh, gõ chậm như người, **đăng xong lane nào TẮT profile lane đó ngay** (GPM `profiles/stop/<id>` đúng profile của kênh — anh chốt 2026-10-08, để người khác dùng; tool mặc định tắt, `--keep-open` mới giữ) → (5) đối chiếu TỪNG reply bằng Data API `comments.list?parentId=` trước khi báo đã đăng, ghi
`youtube_reply_id` → (6) báo bảng video/bình luận/reply + UNRESOLVED còn chờ. Kênh mới: tra channel_id THẬT từ video_id trong sheet (K, L từng
sai vì CLAUDE.md ghi id kênh mẫu). Câu mơ hồ ai là thủ phạm/nạn nhân → không đăng, đề xuất câu trung lập cho anh chọn.

**Lane O dùng chung mail/profile GPM với lane K** (rosellagreysonbk920): profile hay đang đứng ở kênh K → post-browser báo
`IDENTITY_MISMATCH` (đúng, chặn đăng nhầm). Cách làm (2026-10-15): mở `youtube.com/channel_switcher` bấm chữ 「人生のつづき」 → đăng →
chuyển về 「薬局スカッと帳」 rồi mới tắt profile. Script mẫu đã chạy được: chuyển kênh + `browser_poster._run` + chuyển về.

**Lane M (và A) = mail haoviabattu → KHÔNG qua GPM** (2026-10-14): mở Chrome `HAOVIABATTU_PROFILE` cổng 9222 rồi
`cc.py post-browser --channel M --cdp-port 9222 [--like 1,2 --heart 1]`. Mail có 2 kênh (A+M) → kiểm `youtube.com/account_advanced`
ghi đúng tên kênh M trước khi đăng. Like/tim: module `reactions.py`, chỉ bấm khi nút đang TẮT (bấm lại là gỡ). Bẫy: tab NỀN của
Chrome không ăn chuột ổn định (like FAILED, ô reply không hiện) → poster mở tab mới + `bring_to_front()`. Kịch bản các tập nằm ở
`E:\CLAUDE\YOUTUBE\FlowHandoff_local\jobs\<tab>\<ep>\script.txt` (không phải trong h2dev) — câu hỏi A/B/C giữa video nằm trong đó.

## Module `view_spike` — báo video mới đăng ≥1000 view/giờ (anh duyệt 2026-10-15)

Thư mục `view_spike\` (README trong đó; plan `plans\261015-1647-view-spike-alert\`). Task Scheduler
`ViewSpikeWatch` chạy `pythonw spike_watch.py` mỗi 15 phút. Mỗi lane chỉ 2 video MỚI NHẤT còn ≤72h
(anh chốt). Tầng 1 API (1 unit/vòng, 0 token LLM) ≥300 view/giờ công khai ⇒ tầng 2 mở Studio đọc thẻ
Realtime ≥1000 ⇒ toast góc màn hình + `view_spike\state\alerts.jsonl`. Báo tạm bằng toast (anh chốt).
- **Số công khai (API/trang xem) THẤP hơn Studio ~26%** (đo 2 lần 2026-10-15) — đừng nâng ngưỡng tầng 1 lên 1000.
- Thẻ Realtime: số từng cột KHÔNG có trong DOM → phải rê chuột `yta-realtime-chart`, bước ≤2px.
- ⚠️ **Tên tab đã đổi lần nữa (đo 2026-10-15)**: `G` (cũ G-teinengo-tanoshimi), `teinengo-fuufu` không còn,
  thêm `Lane-J/N/O/P/Q`. Map tab→mail ở `view_spike\config.json`, đối chiếu bằng channelId của video qua API
  (không tin ghi chú). Lane-J/N không có profile GPM, Lane-O chưa rõ mail → tầng 2 chỉ báo "nghi đang lên".
