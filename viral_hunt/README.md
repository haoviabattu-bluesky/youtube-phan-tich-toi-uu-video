# viral_hunt — tìm video nguồn đang nổ cho lane L / N / O / M

Mỗi ngày **03:00** quét YouTube, chọn **2 video nguồn tốt nhất mỗi lane**, sinh đề bài,
xuất **1 báo cáo HTML** đẩy qua Syncthing (`FlowHandoff_local\results`) để máy 1 / h2dev đọc.

## Luật (anh chốt 2026-10-18)

| Điều kiện | Giá trị | Có nới được? |
|---|---|---|
| Kênh nguồn | **< 10.000 sub** | ❌ KHÔNG — luật cứng |
| Định dạng | manga faceless (漫画/マンガ/AI漫画/アニメ), 5–45 phút | ❌ KHÔNG |
| Kênh của mình | loại hẳn (12 channel_id trong `lanes.py`) | ❌ KHÔNG |
| Video mới đăng | ≤ 5 ngày | ✅ nới tới 7 ngày (bậc D/E) |
| View | **> 100.000** | ✅ nới tới 50k / 30k / 15k |
| Số đề / lane | 2 | — |
| Chống lặp | video_id đã báo cáo → KHÔNG bao giờ báo lại | — |

### Thang bậc (thác nước)

Đo thật 2026-10-18: quét **547 video** manga đăng trong 7 ngày của cả thị trường Nhật,
chỉ **1 video** đạt đủ bậc A (>100k view, ≤5 ngày, <10k sub) và khớp ngách 4 lane.
Nếu cứng bậc A thì phần lớn các ngày sẽ trắng.

| Bậc | View | Sub | Tuổi |
|---|---|---|---|
| **A** | > 100.000 | < 10k | ≤ 5 ngày |
| **B** | ≥ 50.000 | < 10k | ≤ 5 ngày |
| **C** | ≥ 30.000 | < 10k | ≤ 5 ngày |
| **D** | ≥ 30.000 | < 10k | ≤ 7 ngày |
| **E** | ≥ 15.000 | < 10k | ≤ 7 ngày |

Tool lấy bậc **cao nhất** có sẵn, ghi rõ bậc trên từng đề. Muốn cứng:
`--min-views 100000 --days 5`.

## Chạy

```bat
cd E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\viral_hunt
py -3.13 run_daily.py                          :: đủ 4 lane, có LLM (~6 phút)
py -3.13 run_daily.py --lane L,N               :: chỉ 2 lane
py -3.13 run_daily.py --no-llm                 :: không gọi LLM (ra khung xương)
py -3.13 run_daily.py --dry-run                :: không ghi file, không ghi state
py -3.13 run_daily.py --min-views 100000 --days 5   :: ngưỡng cứng đúng luật
py -3.13 run_daily.py --seed                   :: nạp watchlist từ cột VIDEO GỐC của sheet
py -3.13 run_daily.py --search-budget 0        :: chỉ watchlist, không quét web
```

Cài lịch 03:00 (PowerShell, không cần admin):

```powershell
powershell -ExecutionPolicy Bypass -File create_task.ps1
```

## Dữ liệu lấy từ đâu — API là đường CHÍNH, web là DỰ PHÒNG

**Sửa lại 2026-10-20: API KHÔNG lỗi.** Bản 2026-10-18 bỏ hẳn API vì project cạn quota 10.000
unit — đó là sự cố tạm thời, không phải API hỏng. Đo hôm nay key trả đúng cả
`videos.list` / `channels.list` / `playlistItems.list` / `search.list`.

| Thứ cần | Nguồn CHÍNH (API) | Nguồn DỰ PHÒNG (web) | Chi phí |
|---|---|---|---|
| `publishedAt` CHÍNH XÁC | `videos.list` | chữ "5 日前" (làm tròn — SAI) | 1 unit/50 video |
| view / like / comment | `videos.list` | watch page (1 request/video) | 1 unit/50 video |
| độ dài chính xác | `videos.list` `contentDetails.duration` | `lengthText` | 1 unit/50 video |
| sub kênh | `channels.list` | HTML `/channel/<id>?hl=ja` | 1 unit/50 kênh |
| tỉ lệ manga của kênh | `playlistItems.list` (20 tiêu đề) | `/channel/<id>/videos` `lockupViewModel` | 1 unit/kênh |
| quét từ khoá | trang `youtube.com/results` (0 unit) | — | 0 |

**Cả lượt chạy đầy đủ = 62 unit** (1.005 video + 663 kênh + 27 kênh ratio) trên trần 10.000/ngày.
`search.list` (100 unit/call) vẫn KHÔNG dùng — đó là thứ từng làm cạn quota.

Nếu API trả 403 `quotaExceeded` (key dùng chung với `TRENDING-RESEARCH\src\run_daily.py` và
`view_spike`), `enrich.available()` trả False và tool tự lùi về đường web. Test bằng
`--no-api`: đo thật 58/70 kênh xác minh được, **12 kênh còn lại bị LOẠI HẲN** — đúng luật.

### Vì sao không dùng Playwright

Playwright chỉ render lại thứ đã có trong `ytInitialData`. HTTP thuần: **38 giây cho 120 từ khoá**;
Playwright mở profile GPM mất **10–17 phút** và hay vướng `ProfileUsingByOther`. Ba thứ web
KHÔNG cho (tuổi chính xác, like/comment, sub tin cậy) thì API cho hết với 0,62% quota.

## Đầu ra

| Nơi | Nội dung |
|---|---|
| `E:\CLAUDE\YOUTUBE\FlowHandoff_local\results\VIRAL_<ngày>.html` | báo cáo → Syncthing sang máy 2 |
| `...\results\VIRAL_<ngày>.jobs.json` | bản máy đọc, không cần parse HTML |
| `reports\viral_hunt\<ngày>\VIRAL_<ngày>.html` | lưu máy này |
| `reports\viral_hunt\<ngày>\VIRAL_<ngày>.jobs.json` | bản máy đọc |
| `state\viral_hunt.sqlite` | `reported` / `seen` / `runs` / `channels` / `kw_cursor` |

Chạy lại trong cùng ngày **không ghi đè** bản đầu — ghi `_lan2`, `_lan3`…

## Cấu trúc

| File | Việc |
|---|---|
| `lanes.py` | **công thức WIN của 4 lane** + `core_win` + 120 từ khoá + kênh mình |
| `ytweb.py` | **toàn bộ nguồn dữ liệu, 0 quota**: search + phân trang + sub kênh + like |
| `analyze.py` | lọc cứng + thang bậc + chấm điểm + gọi LLM sinh đề bài |
| `report.py` | dựng HTML (cùng skin báo cáo WIN) + jobs.json |
| `state.py` | SQLite chống báo lặp |
| `watchlist.py` | SQLite kênh nguồn + cursor từ khoá (tự học kênh mới) |
| `run_daily.py` | điều phối |
| `websearch.py` / `ytapi.py` | ⚠ bản CŨ (dùng API / chỉ 1 trang) — đã bị `ytweb.py` thay. Giữ làm tham chiếu, đừng dùng. |

## Bẫy đã trả giá (đừng "dọn cho gọn")

0. **`search.list` có hạn mức RIÊNG theo ngày** ("Search Queries per day") — không liên quan
   quota 10.000 unit. Quét 38 từ khoá là ăn **HTTP 429** và chết cả ngày. ⇒ Vẫn KHÔNG dùng
   `search.list`; quét bằng trang kết quả (0 unit).

0b. **KHÔNG BAO GIỜ gán `subs = 0` khi không đọc được sub.** Đây là lỗi nặng nhất, đã xảy ra
   thật ngày 2026-10-20: `channel_subs()` gọi `youtubei/v1/browse` 800 kênh song song → 403 →
   trả `None` → code cũ coi là "0 sub, cho qua cổng <10k" ⇒ **kênh 711.000 sub lọt vào báo cáo
   như kênh 0 sub**. Luật: không xác minh được thì **LOẠI HẲN**, và đọc HTML
   `/channel/<id>?hl=ja` TRƯỚC (đo 5/5 OK, kể cả 3 kênh browse trả None).

0c. **Task Scheduler chạy `pythonw.exe` ⇒ `sys.stdout` và `sys.stderr` là `None`.**
   `llm_client.py` dòng 36 làm `sys.stdout.reconfigure(...)` ⇒ AttributeError ⇒ import chết ⇒
   **mọi call LLM hỏng**: 8/8 đề bài rỗng + toàn bộ tiêu đề in "chưa dịch được". Chạy tay
   `py -3.13` thì KHÔNG tái hiện được. Phải độn stream giả trước khi import `llm_client`
   (đã làm trong `translate.py` và `analyze.py`), và luôn ghi log ra
   `state/run_last.log` vì `pythonw` không có stdout.

1. **Filter "tuần" chỉ trả 62 video/từ khoá** (đo thật). Filter **"tháng" trả ~158–260**.
   Dùng `sp=CAMSBAgEEAE%3D`. Muốn 5000–10000 video thì phải **nhiều từ khoá + phân trang sâu**,
   không phải chỉ tăng `pages`.

2. **Phân trang dừng ở trang 2 nếu chỉ đọc `contents`**: trang 1 token ở
   `contents/twoColumnSearchResultsRenderer/primaryContents/sectionListRenderer/contents[1]/
   continuationItemRenderer`, nhưng trang 2+ trả `onResponseReceivedCommands[0]/
   appendContinuationItemsAction/continuationItems[1]/continuationItemRenderer`. Đọc cả hai.

3. **Trang kết quả có 6 `continuationCommand`** — 5 cái là **chip lọc** (chipBar/chipCloudRenderer).
   Lấy sai token ⇒ nhận trang trộn sort lung tung (view 89, 582, 233…) mà KHÔNG báo lỗi.

4. **`ytInitialData` phải bóc bằng `re.search(r"ytInitialData\s*=\s*(\{.*?\});", html, re.S)`** —
   thiếu `re.S` là không khớp → tưởng "YouTube chặn".

5. **Không regex `"videoId":"..."` trên cả trang** — bắt cả id trong `ytInitialPlayerResponse`,
   ra id rác. Phải đi bộ cây JSON tìm đúng key `videoRenderer`.

6. **`sp` phải URL-encode** (`CAMSBAgDEAE%3D`). Để nguyên `=` thì YouTube bỏ filter, trả sort
   relevance — vẫn "có video" nên rất dễ tưởng đang lọc đúng.

7. **Sub kênh: chuỗi thật là `チャンネル登録者数 17.3万人`.** KHÔNG có `subscriberCountText`,
   KHÔNG có `X人の登録者`. Regex `登録者([\d.,]+万?)人` trần khớp **dương tính giả** với mô tả
   kênh ("2026年はチャンネル登録者20万人を目標に" → ra 200.000 trong khi thật 173.000).

8. **`/channel/<id>` và `/channel/<id>/about` không có số sub trong HTML** (0 match) — phải gọi
   `youtubei/v1/browse`. Client ANDROID/IOS/WEB_CREATOR/WEB_EMBEDDED_PLAYER đều trả HTTP 400;
   chỉ **WEB** dùng được.

9. **`lengthText` có 2 dạng**: `simpleText` = "17:01", hoặc chỉ `accessibility.label` =
   "17 分 1 秒". Đọc cả hai, không thì video 17 phút bị coi là 0 phút và bị loại.

10. **Web search KHÔNG cho `publishedAt`, chỉ cho "3 日前"**. Bỏ qua là `hours=1` ⇒ view/giờ
    bằng đúng view (đo thật: 32.306 v/h cho video 32.306 view). Phải dùng `age_days`.

11. **`publishedTimeText` tiếng Nhật**: 秒/分/時間/日/週間/か月/年 — thiếu đơn vị nào thì video
    tuổi đó lọt qua lọc "≤5 ngày".

12. **Kênh tự học không được gán lane cố định.** Bản đầu lưu `lane` = lane đầu tiên chấm được
    (luôn là L) ⇒ lần sau mọi video của kênh đó chỉ chấm cho L, 3 lane kia ra **0 đề**.

13. **`core_win` phải là từ khoá LÕI, không phải từ khoá chung.** Để rộng (có chữ 年金) thì nhận
    oan video "50代で結婚…年金と相続"; để hẹp thì loại oan video 1,2 triệu view
    「60歳で辞めるか、65歳まで働くか。同期2人が…」— đúng ngách nhất của M.

14. **Không được nới trục SUB.** Bản đầu thêm bậc với sub <30k, kênh 17.600 sub lọt vào báo cáo —
    trái luật cứng. Sub luôn < 10k ở mọi bậc.

15. **Kênh không hiển thị sub** (kênh mới): browse trả `0 回視聴`, không có chuỗi 登録者 nào.
    Không phải lỗi code — đánh dấu "⚠ Sub chưa rõ", trừ 3 điểm, đừng loại thẳng (mất ~1/3 nguồn).

16. **Trang `/channel/<id>/videos` KHÔNG còn `richItemRenderer`/`videoRenderer`** (đổi 2026-10).
    Video nằm trong `lockupViewModel` với `contentId`, `metadata.lockupMetadataViewModel.title.content`.
    Đi tìm `richItemRenderer` sẽ ra **0 video mà không báo lỗi**.

17. **`lockupViewModel` in view HAI lần**: `text.content` = `"4655"` (số trần) và
    `accessibilityLabel` = `"4,655回視聴"`. Ghép cả hai (hàm `txt()` đệ quy) → `"46554,655回視聴"`
    → **sai 10.000 lần** (đo thật: 46.554.655 thay vì 4.655). Luôn đọc `accessibilityLabel` trước,
    chỉ dùng `text.content` khi không có label.

18. **Tuổi video phải lấy `uploadDate` ở trang watch, không dùng chữ "5 日前" trên trang search.**
    Chữ đó làm tròn: đo thật 2 video ghi "5 日前" nhưng tuổi thật **5,27** và **5,77** ngày.
    Dùng chữ trên search thì video 5,8 ngày lọt qua luật "≤5 ngày".

19. **Sub kênh: đọc HTML `/channel/<id>?hl=ja` trước, `youtubei/v1/browse` chỉ là phương án 2.**
    Browse hay trả **HTTP 403** khi bị gọi nhiều; HTML trang kênh luôn có
    `チャンネル登録者数 86.6万人`. Đọc sai nguồn → hàng loạt video bị ghi "sub không rõ" oan.

20. **`/watch` không trả `compactVideoRenderer` cho phần video liên quan nữa** (2026-10):
    `secondaryResults` rỗng, `youtubei/v1/next` trả 403. Đừng thiết kế luồng "mở rộng theo
    video liên quan" — nó im lặng trả 0. Mở rộng bằng **nhiều từ khoá** (đo thật: 4.841 từ khoá
    → 4.047 video unique, ~10 phút, 0 quota).

## Quota

**Không dùng quota.** Toàn bộ dữ liệu lấy từ web (`ytweb.py`): trang search + `youtubei/v1/browse`
+ trang watch. Không cần `YOUTUBE_API_KEY`, không đụng trần 10.000 unit/ngày của project
(dùng chung với `comment_care`, `view_spike`).

Số request 1 lần chạy: 120 từ khoá × 12 trang = 1.440 + 800 kênh sub + ~30 trang watch ≈ 2.300
request HTTP thường, chạy 12 luồng, ~4 phút.

## Khi có báo cáo WIN mới

Đọc `BAO_CAO_WIN_LANE_<lane>_<ngày>.html` mới rồi **sửa `lanes.py`**, đừng sửa logic chấm điểm:

- `win_one_line` — câu chốt công thức, in đầu mục mỗi lane
- `win_zone` / `lose_zone` — vùng làm / vùng đã thua (in vào prompt LLM)
- `topics_win` / `topics_lose` / `topics_soft` — từ khoá chấm điểm (title nặng gấp 2 desc)
- `core_win` — **bắt buộc có ≥1 trong title**, đây là cổng ngách
- `title_pat` — khuôn tiêu đề thắng (regex)
- `keywords` — từ khoá quét web (miễn phí quota, cứ thêm thoải mái)
- `draft_rule` — khung xương khi LLM chết
