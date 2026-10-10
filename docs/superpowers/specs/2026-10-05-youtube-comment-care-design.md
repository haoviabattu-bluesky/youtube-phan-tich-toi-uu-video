# YOUTUBE COMMENT CARE — DESIGN PROPOSAL

Ngày: 2026-10-05 · Trạng thái: **WAITING_FOR_APPROVAL** · Chưa có dòng code nào được viết.
Phạm vi: module mới trong `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\` (chỉ liệt kê, chưa tạo).

Tài liệu này là kết quả PHASE 0 (Audit) theo đúng brief 87 mục của anh. Mọi đường dẫn, model, provider,
scope dưới đây đều đọc từ file thật trên máy ngày 2026-10-05, không lấy từ trí nhớ.

---

## A. Executive Summary

1. **Trên máy hiện KHÔNG có bất kỳ thứ gì có thể đăng reply YouTube.** Không có OAuth scope `youtube.force-ssl`,
   không có `comments.insert`. Token OAuth duy nhất (`D:\CLAUDE\credentials\token.json`) chỉ có scope Sheets + Drive.
   → Phần "gửi reply" là mảnh ghép **mới hoàn toàn**, cần anh authorize OAuth cho từng Gmail kênh (mục C, Z-1, Z-2).
2. **Đọc comment thì đã có 3 đường sẵn**: Data API v3 với API key (`YOUTUBE_API_KEY` trong
   `E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env`, đã kiểm tra sống 2026-09-28), thư viện
   `youtube-comment-downloader` (không key, đã cài py -3.13), và InnerTube qua profile GPM. Đề xuất dùng Data API
   `commentThreads.list?allThreadsRelatedToChannelId=` (1 unit/lần, lấy toàn kênh một phát).
3. **LLM router đã có, nên REUSE, không viết router thứ hai**: `E:\CLAUDE\YOUTUBE\h2dev\pipeline\llm_client.py`
   (ramclouds → ns24 → sol), `sol_client.py` (gpt-5.6-sol, 3 đường), `claude_p_bridge.py` (Claude qua `claude -p`).
   Comment care chỉ viết một **wrapper mỏng** gọi 3 module đó với `temperature` thấp + chain riêng.
4. **Kiến trúc đề xuất: Policy Engine đứng trên model.** LLM chỉ làm 2 việc: hiểu/phân loại và soạn nháp. Quyết định
   REPLY/SKIP/ESCALATE, chọn template hay LLM, gắn footer hay không — đều là bảng luật deterministic (mục G).
5. **Rollout 7 pha, mặc định tắt gửi**: PHASE 0 audit (xong) → 1 fetch+classify → 2 draft-only → 3 shadow 100 comment
   → 4 auto chỉ LOW risk có daily cap → 5 mở rộng → 6 daily. Kill switch 3 lớp, fail-closed.
6. **Có 12 quyết định cần anh chốt** (mục Z). Ba cái quan trọng nhất: (1) gửi reply bằng Data API OAuth hay bằng
   Studio automation qua GPM; (2) phương án footer A/B/C; (3) sửa luật "Claude không đụng YouTube" trong
   `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\CLAUDE.md` để cho phép đúng một ngoại lệ là module này.

⚠️ **Thiếu dữ liệu đầu vào:** brief nhắc "các comment mẫu trong hình tôi đã gửi kèm" nhưng phiên này **không có ảnh
nào được đính kèm**. Toàn bộ test set (mục X) đang dựa trên mô tả bằng chữ trong brief (nghỉ hưu 60/65/66, tái tuyển
dụng, lương hưu, sống một mình…). Khi anh gửi lại ảnh, em sẽ bổ sung vào bộ mẫu benchmark, không cần đổi thiết kế.

---

## B. Existing Project Audit (path thật)

### B1. Repo này — `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\`

| Path | Vai trò | Liên quan comment care |
|---|---|---|
| `CLAUDE.md` | Luật dự án; **mục "⛔ VAI TRÒ"**: Claude không tự đổi gì trên YouTube | Xung đột trực tiếp với việc post reply → cần sửa (Z-3) |
| `tools\studio_collect.py`, `tools\sheet_metrics_sync.py`, `tools\scan_channels.py` | GPM `http://127.0.0.1:9495/api/v1` → Playwright CDP → Studio (shadow DOM `DEEP`) | Pattern kết nối GPM + luật `ProfileUsingByOther` → tái dùng nếu chọn đường Studio (Z-1 phương án 2) |
| `tools\scan_channels.py` → `LANES` | Map duy nhất lane ↔ mail (10 lane, bỏ D) | Nguồn seed cho `channels.yaml` |
| `scan_channels.json` | Snapshot kênh 23/09, **đã cũ** (còn lane D, thiếu K/L, key là tên lane cũ) | Có `profile_id` GPM, channel_id; không dùng làm nguồn chuẩn |
| `tools\sol_packaging_review.py` | Gọi `sol_client` của h2dev | Tiền lệ "repo này import module h2dev" → wrapper LLM làm giống vậy |
| `youtube_postpublish_metrics.csv` | Sổ số liệu per-video | Comment care KHÔNG ghi vào đây |
| `reports\` | `backup_sheet_*.json`, `reports\<video_id>\` | Thêm nhánh `reports\comment_care\<date>\` |
| `.gitignore` | đã chặn `studio_profile/`, `*.key.json`, `credentials/`, `.env` | Cần thêm `comment_care/state/`, `reports/comment_care/` |
| Google Sheet `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU` | Cột L = video_id, tab = tên lane | **Nguồn duy nhất map video_id ↔ tập ↔ lane** (h2dev không lưu video_id của chính mình) |

Không có một chữ "comment"/"コメント"/"bình luận" nào trong repo này. Không có SQLite, không có LLM key, không có
YouTube API. Python 3.13.5; đã cài `google-api-python-client 2.194`, `google-auth-oauthlib 1.2`, `playwright 1.58`,
`anthropic 0.97` (chưa dùng ở đâu), `youtube-comment-downloader`, `yt-dlp`.

### B2. h2dev — `E:\CLAUDE\YOUTUBE\h2dev\`

| Path | Có gì | Dùng cho comment care |
|---|---|---|
| `pipeline\llm_client.py` | `PROVIDERS = {ramclouds: https://ramclouds.me, ns24: https://api.ns24.io}`, `CHAINS = {script, short, analysis}`, `chat(prompt, system, task, model, provider, max_tokens=32000, temperature=0.9, timeout=1800, tries_per_model=2, min_chars, require_sentence_end)` → `ChatResult(text, provider, model, usage, finish, elapsed, attempts)`; stream bắt buộc + browser UA; `BAD_CONTENT` lọc refusal | **Classifier + generator tier rẻ**. Lưu ý: default temperature 0.9 → wrapper phải ép 0.2–0.4 |
| `pipeline\sol_client.py` | gpt-5.6-sol: 9router `http://localhost:20128/v1` (`cx/gpt-5.6-sol`) → ns24 `https://api.ns24.io/v1` → hhtechapi `https://hhtechapi.net/v1`; `chat(text, image_path, max_tokens, timeout) → (text, usage)`; không có system role | **Judge** (khác họ với generator) — đúng pattern `qc_loi_hua.py:79` |
| `pipeline\claude_p_bridge.py` | `claude -p --tools "" --output-format text --model <m> --no-session-persistence`; model từ `profile.script.brain_model` (`claude-opus-5-5`), patch `claude-opus-5`, hook `claude-fable-5-1`; không retry, không chỉnh temperature | **Generator tier mạnh** cho EXPERIENCE/EMOTIONAL/GRIEF |
| `pipeline\profiles.py` + `profiles\profiles\<lane>.json` | `narrator{gender, age_band, persona, point_of_view, register}`, `niche`, `publish{channel_id, handle, sheet_tab}` | Nguồn "channel voice" (giọng kênh) — **nhưng narrator là nhân vật kể chuyện, KHÔNG phải chủ kênh** → chỉ lấy `register`/`niche`, không lấy tuổi/giới/hoàn cảnh (mục 41–42 brief) |
| `assets\<lane>\branding\KENH.json` | `mail, channel_name, handle, description, browser{kind, user_id}` | Seed `channels.yaml`; lane J, N dùng AdsPower (`k15n8xbk`, `k15wbjoo`) |
| `assets\<lane>\<epNN-slug>\research\S1_TOM_TAT.json` | `tom_tat` (JA), `y_chinh`, `nhan_vat`, `cam_xuc_dinh`, **`khong_duoc_noi_qua`** (spoiler cấm nói) | Context gọn cho reply (≈1–2 KB thay vì full transcript). Có ở lane M (4 tập), satori_jp; **không phải tập nào cũng có** |
| `assets\<lane>\<ep>\title.txt`, `TIEU_DE_MO_TA.txt`, `promise.txt` | Title/description/lời hứa | Context fallback |
| `pipeline\comment_digest.py`, `make_video.py:317 b2b_comments` | Đọc comment **video đối thủ** bằng `youtube_comment_downloader`, regex tag, `comment_insight.json` | Chỉ là tiền lệ đọc; không reply, không đọc kênh mình |
| `pipeline\gate_common.py` `LLM_STATS` | Đếm calls/tokens in-process | Không persist → comment care tự ghi usage vào SQLite |
| `docs\channel_dna\<channel>\COMMENT_INSIGHT.md` | Insight comment đối thủ | Input tham khảo cho AUDIENCE INSIGHT (V2) |

**Phát hiện bảo mật (ngoài phạm vi nhưng phải báo):** key thật đang hardcode làm default trong
`E:\CLAUDE\YOUTUBE\h2dev\pipeline\llm_client.py`, `sol_client.py`, `qc_character.py`, `ckey_gen.py` và
`keys.sample.json` (không phải sample trống) — tất cả **tracked trong git** có remote
`github.com/haoviabattu-bluesky/h2dev2`. `E:\CLAUDE\YOUTUBE\NOTE.txt` chứa `YOUTUBE_DATA_API_KEY` + `AI33_API_KEY`
plaintext. Comment care sẽ **không** thêm key nào vào source; xem mục V.

### B3. Các dự án anh em có liên quan

| Dự án | Liên quan |
|---|---|
| `E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\` | `src\ytapi.py` (`BASE=https://www.googleapis.com/youtube/v3`, `QUOTA_COST`, `DAILY_QUOTA=10_000`), `scratch_golo\fetch_comments_15.py` (**`commentThreads.list` bằng API key, đã test sống 28/09**, xử lý 403 `commentsDisabled`), `config\models.yaml` (router YAML có gate `final_qc: ns24 gpt-5.6-sol → hhtech`), `data\trending.db` (SQLite, có bảng `llm_cache(key, gate, model, prompt_version, payload)` — pattern cache tốt) |
| `E:\CLAUDE\YOUTUBE\AUTO_LIST\` | Upload qua Studio bằng GPM; tab `GMAIL` của sheet là **registry kênh thật** (B=MAIL=tên profile GPM, G=tên kênh → tab `{Lane}-{G}`) |
| `E:\CLAUDE\YOUTUBE\YT-TITLE-RESEARCH\config\lanes\*.json` | `own_channel_id`, `own_channel_url`, `sheet_tab` per lane (không có mail) |
| `C:\Users\admin\.claude\skills\youtube_research_ext.md` | Cách đọc comment không extension; cảnh báo IP datacenter bị "Sign in to confirm you're not a bot" |
| `E:\CLAUDE\YOUTUBE\YT_EMPLOYEE\plans\...\brainstorm-summary.md` | Draft "nhân viên YouTube" — ghi rõ "không trả lời comment" → không trùng |

---

## C. Current YouTube API / Auth Audit

| Hạng mục | Hiện có | Còn thiếu để reply |
|---|---|---|
| GCP project | `fifth-glider-495702-b4` (từ `D:\CLAUDE\credentials\credentials.json`, OAuth client kiểu `installed`) | Chưa rõ YouTube Data API v3 đã enable chưa trong project này; API key ở TRENDING-RESEARCH có thể thuộc project khác |
| OAuth token | `D:\CLAUDE\credentials\token.json`: scopes **chỉ** `spreadsheets` + `drive`, tài khoản haoviabattu@gmail.com | Cần scope `https://www.googleapis.com/auth/youtube.force-ssl` (scope duy nhất cho `comments.insert`), **riêng cho từng Gmail kênh** (10 tài khoản khác nhau) |
| API key | `YOUTUBE_API_KEY` trong `E:\CLAUDE\YOUTUBE\TRENDING-RESEARCH\config\.env` | Đủ cho đọc comment **công khai**; không đọc được comment "held for review", không insert được |
| Service account | `D:\CLAUDE\credentials\google-sheets-key.json` | Service account **không thể** thao tác YouTube của tài khoản cá nhân → vô dụng cho reply |
| Studio automation | GPM + Playwright trong repo này và AUTO_LIST | Có thể gõ reply trên trang Comments của Studio — đường dự phòng (Z-1) |

**Quota Data API v3 (chuẩn Google, mặc định 10.000 unit/ngày/project):**

| Thao tác | Unit | Ghi chú |
|---|---|---|
| `commentThreads.list` | 1 | tối đa 100 thread/lần; `allThreadsRelatedToChannelId=UC…&order=time` quét cả kênh |
| `comments.list?parentId=` | 1 | đọc full replies của 1 thread (snippet `replies` trong threads chỉ kèm tối đa 5) |
| `comments.insert` | 50 | reply; **chỉ OAuth**, chủ kênh |
| `channels.list?mine=true` | 1 | xác minh token thuộc đúng kênh (CASE 8) |

Ước tính: 10 kênh × (quét 2 lần/ngày × 2 unit) + 60 reply/ngày × 50 = ~3.040 unit/ngày → nằm trong 10.000. Nếu
đặt daily cap 30 reply/kênh × 10 kênh thì trần là 15.000 unit → **phải chia cap theo quota**, xem mục U.

**Rủi ro OAuth cần anh biết trước (Z-2):**
- Consent screen ở trạng thái **Testing**: refresh token **hết hạn sau 7 ngày**, phải add từng Gmail vào Test users
  (tối đa 100). Mỗi tuần anh phải authorize lại 10 lần → không chạy daily nổi.
- Chuyển sang **In production**: scope `youtube.force-ssl` là *sensitive scope*; app chưa verify sẽ hiện cảnh báo
  "unverified app" nhưng **vẫn authorize được** (bấm Advanced → Go to app) và refresh token **không** hết hạn 7 ngày.
  Verify chỉ cần khi >100 user — không áp dụng cho mình.
- Nếu kênh là **Brand Account**, khi authorize phải chọn đúng kênh trong màn hình chọn tài khoản; token sau đó gắn với
  channel_id của brand → bước `channels.list?mine=true` ở đầu run sẽ bắt sai ngay.

**Design phase: không đổi gì.** Khi anh duyệt, bước authorize là anh tự làm trên trình duyệt profile GPM của từng kênh
(tool chỉ in URL consent + nhận code), token lưu `D:\CLAUDE\credentials\youtube_oauth\<channel_id>.json`
(ngoài repo, đã gitignore theo pattern `credentials/`).

---

## D. Multi-channel Architecture

Nguyên tắc: **một run = một channel context**, không có biến toàn cục nào mang identity.

```yaml
# comment_care/config/channels.yaml  (template commit; giá trị thật đọc từ sheet tab GMAIL + KENH.json khi init)
channels:
  - channel_id: UC9huXCiBIXBfUh11D7ZsFSA
    channel_name: 人生の夕暮れ
    handle: "@Lopezzapa68"
    lane: Satori
    sheet_tab: Satori-Lopezzapa68
    mail: LopezzapataHilla@gmail.com          # = tên profile GPM (chỉ dùng nếu đường Studio)
    h2dev_profile: Lopezzapa68                # profiles\profiles\Lopezzapa68.json
    h2dev_assets_dir: E:\CLAUDE\YOUTUBE\h2dev\assets\satori_jp
    language: ja
    tone_profile: senior_polite               # mục H
    oauth_token: D:\CLAUDE\credentials\youtube_oauth\UC9huXCiBIXBfUh11D7ZsFSA.json
    comment_reply:
      enabled: true
      mode: draft_only                        # fetch_only | draft_only | shadow | auto_low | auto_full
      footer_policy: PENDING_OWNER_DECISION   # A | B | C | BC  (mục M)
      max_replies_per_run: 20
      daily_cap: 30
      min_confidence_auto: 0.85
      owner_facts: {}                         # TRỐNG mặc định: không có tuổi/giới/nghề của chủ kênh → model cấm bịa
```

**Isolation (mục 31 brief):**
1. `ChannelContext` là object bất biến tạo ở đầu mỗi vòng lặp kênh; mọi hàm fetch/generate/send nhận nó làm tham số
   bắt buộc, không có default.
2. Trước khi fetch hoặc send: `channels.list(mine=true)` bằng token của kênh → so `id` với `channel_id` trong config.
   Lệch → `IDENTITY_MISMATCH`, bỏ qua **toàn bộ kênh** trong run, ghi `errors`, báo cáo đỏ. (CASE 8)
3. Context video chỉ được lấy từ `videos` row có `channel_id` trùng; query luôn có `WHERE channel_id = ?`.
4. Idempotency key = `(channel_id, comment_id)`; reply row có `channel_id` NOT NULL + FK.
5. Prompt system luôn chèn `channel_name` + `handle` thật; QC kiểm tra draft không nhắc tên kênh khác trong
   danh sách `channels.yaml` (blocklist động).

---

## E. Comment Fetch Workflow

**Đề xuất chính: Data API v3.** Lý do: 1 unit/100 thread, có `order=time`, trả `parentId`, `authorChannelId`,
`updatedAt`, `canReply`, `totalReplyCount` — đủ để dedup và dựng thread. Browser automation để dự phòng.

```
mỗi channel (theo thứ tự channels.yaml, enabled=true):
  1. verify identity (channels.list mine=true)              [OAuth]  ← Phase 2+; Phase 1 dùng API key, bỏ bước này
  2. commentThreads.list allThreadsRelatedToChannelId=UC…
       part=snippet,replies  order=time  maxResults=100
       dừng khi gặp thread có updatedAt < watermark(channel) - 48h   (an toàn vì reply mới làm updatedAt đổi)
  3. với thread có totalReplyCount > 5 hoặc có reply mới hơn watermark:
       comments.list parentId=<thread_id>  → full thread
  4. upsert comments(comment_id, parent_id, video_id, author_channel_id, text, published_at, updated_at,
                     is_owner = (author_channel_id == channel_id), like_count, raw_json)
  5. video_id mới → videos.list part=snippet (1 unit) → cache title/description; map sang sheet row + h2dev ep
  6. chọn "cần xử lý": top-level chưa có owner reply, HOẶC reply của viewer mới hơn owner reply cuối trong thread
  7. watermark(channel) = max(updated_at) của run này (lưu sau khi commit)
```

Quy tắc chọn comment cần xử lý (mục 13–14 brief):
- Thread đã có owner reply và không có viewer follow-up sau đó → `ALREADY_HANDLED`, không xử lý.
- Viewer follow-up sau owner reply → xử lý **với full thread làm context**, nhưng category mặc định
  `FOLLOW_UP_TO_OWNER`, risk MEDIUM (tránh trao đổi qua lại vô tận: tối đa **1 reply của bot/thread**; lượt 2 trở đi →
  `ESCALATE`).
- Reply của viewer mà `parentId` thuộc viewer khác (không nhắc kênh) → `VIEWER_TO_VIEWER` → `NO_REPLY_NEEDED`.
- Comment do chính kênh viết (pinned comment do h2dev `publish_kit.py` sinh) → bỏ qua.

Phase 1 chạy bằng **API key** (có sẵn, 0 authorize) để làm fetch + classify + benchmark. Từ Phase 2 chuyển sang token
OAuth của kênh để đọc thêm được comment `heldForReview` (chỉ đọc, không reply loại này trong V1).

---

## F. Classification Taxonomy (đề xuất cuối)

Mở rộng baseline 13 nhóm của anh thành 21 nhóm vì 4 loại cần policy khác nhau rõ rệt (GRIEF, HEALTH, FINANCIAL,
CRISIS) và 3 loại cấu trúc thread (FOLLOW_UP, VIEWER_TO_VIEWER, REQUEST).

| # | Category | Mô tả | Risk | Default decision | Generator |
|---|---|---|---|---|---|
| 1 | `GRATITUDE_SIMPLE` | ありがとうございます / 良い動画でした, ≤ 30 ký tự, không có nội dung khác | LOW | REPLY | TEMPLATE pool |
| 2 | `PRAISE` | Khen có nội dung ngắn (giọng đọc, chủ đề, "泣けました") | LOW | REPLY | TEMPLATE + 1 slot LLM nhỏ |
| 3 | `EXPERIENCE_SHARING` | Kể trải nghiệm thật: tuổi nghỉ, 再雇用, lương, công việc, sinh hoạt | LOW | REPLY | LLM mạnh |
| 4 | `EMOTIONAL_SHARING` | Tâm sự cảm xúc (寂しい, 不安, ほっとした) không có mất mát | MEDIUM | REPLY | LLM mạnh |
| 5 | `GRIEF_LOSS` | Mất vợ/chồng/con/cha mẹ, bệnh nặng của người thân, cô độc nặng | HIGH | REPLY (policy riêng mục I) | LLM mạnh + judge bắt buộc |
| 6 | `AGREEMENT` | 同感です / その通り | LOW | REPLY | TEMPLATE |
| 7 | `DISAGREEMENT_POLITE` | Không đồng ý, lịch sự | MEDIUM | REPLY | LLM mạnh (công nhận góc nhìn) |
| 8 | `CRITICISM_CONSTRUCTIVE` | Góp ý về video (dài quá, giọng, BGM, chữ nhỏ) | MEDIUM | REPLY | TEMPLATE "cảm ơn góp ý" + 1 câu LLM |
| 9 | `QUESTION_OPINION` | Hỏi ý kiến ("再雇用した方がいい?") | MEDIUM | REPLY trung tính (人それぞれ) | LLM mạnh |
| 10 | `QUESTION_FACTUAL` | Hỏi số liệu/luật/chế độ cụ thể | HIGH | SKIP → UNRESOLVED (V1) | — |
| 11 | `REQUEST` | Xin làm video chủ đề X | LOW | REPLY | TEMPLATE |
| 12 | `HEALTH_SHARING` | Kể bệnh của **bản thân**, thuốc, điều trị | HIGH | REPLY (policy riêng) hoặc SKIP | LLM mạnh + judge |
| 13 | `FINANCIAL_SPECIFIC` | Nêu số tiền, 年金 cụ thể, thuế, đầu tư; hoặc đưa thông tin chế độ | MEDIUM/HIGH | REPLY "貴重な情報" không xác nhận; nếu kèm câu hỏi → SKIP | TEMPLATE |
| 14 | `CRISIS` | Tín hiệu tự hại, "生きていても仕方ない", tuyệt vọng | HIGH | **ESCALATE ngay**, không reply tự động | — |
| 15 | `POLITICAL_SOCIAL` | Chính trị, đảng phái, chính phủ, tranh cãi xã hội | HIGH | SKIP / ESCALATE | — |
| 16 | `HOSTILE` | Chửi, khiêu khích, mỉa mai, "嘘", "AI動画", "金目当て" | MEDIUM | REPLY template cố định hoặc SKIP (Z-5) | TEMPLATE deterministic |
| 17 | `SPAM_PROMO` | Link, quảng cáo, "LINE追加", chuỗi emoji | — | NO_REPLY_NEEDED | — |
| 18 | `OFF_TOPIC` | Không liên quan video/kênh | LOW | NO_REPLY_NEEDED | — |
| 19 | `VIEWER_TO_VIEWER` | Reply cho viewer khác, không hướng về kênh | — | NO_REPLY_NEEDED | — |
| 20 | `FOLLOW_UP_TO_OWNER` | Viewer trả lời tiếp sau reply của kênh | MEDIUM | REPLY tối đa 1 lần/thread, sau đó ESCALATE | LLM mạnh |
| 21 | `UNCLEAR` | Không hiểu / không chắc / tiếng Nhật lạ / không phải tiếng Nhật | HIGH | SKIP → UNRESOLVED | — |

Flags phụ (đa giá trị, do classifier trả cùng lúc): `mentions_age`, `mentions_money`, `contains_url`,
`contains_pii` (tên thật, địa chỉ, số điện thoại), `not_japanese`, `sarcasm_possible`, `asks_question`,
`addresses_owner_directly`. Flag `sarcasm_possible=true` ép `understanding_confidence` ≤ 0.6 → UNRESOLVED.

Comment có thể mang **1 primary + tối đa 2 secondary**. Policy đọc theo primary, nhưng risk = **max** của tất cả
(ví dụ EXPERIENCE_SHARING + GRIEF_LOSS → HIGH).

---

## G. Reply Decision Policy (Policy Engine — deterministic)

```
REPLY_DECISION ∈ {REPLY, SKIP, ESCALATE, NO_REPLY_NEEDED, ALREADY_HANDLED}
```

Thứ tự đánh giá (dừng ở luật đầu tiên khớp):

1. `is_owner` hoặc đã có reply của bot cho `(channel_id, comment_id)` → `ALREADY_HANDLED`.
2. `SPAM_PROMO | OFF_TOPIC | VIEWER_TO_VIEWER` → `NO_REPLY_NEEDED`.
3. `CRISIS` → `ESCALATE` (ghi `HIGH_RISK` trong report, không draft).
4. `POLITICAL_SOCIAL`, `QUESTION_FACTUAL`, `UNCLEAR`, `not_japanese=true` → `SKIP` + UNRESOLVED.
5. `classification_confidence < 0.70` HOẶC `understanding_confidence < 0.70` → `SKIP` + UNRESOLVED.
6. `FOLLOW_UP_TO_OWNER` và bot đã reply ≥ 1 lần trong thread → `ESCALATE`.
7. `HOSTILE` → `REPLY` bằng template cố định (hoặc `SKIP` nếu anh chọn Z-5b).
8. `canReply == false` (API trả) hoặc comments bị tắt → `SKIP` + lý do kỹ thuật.
9. Còn lại → `REPLY`, generator theo bảng F.

Sau khi có draft và judge (mục L), **gate gửi** (chỉ ở mode `auto_*`):

| Điều kiện | Kết quả |
|---|---|
| risk == LOW và cả 3 confidence ≥ 0.85 và judge PASS và mode == auto_low | SEND |
| risk == MEDIUM và mode == auto_full và confidence ≥ 0.90 và judge PASS | SEND |
| risk == HIGH | **không bao giờ auto** trong V1 → DRAFT cho anh duyệt |
| bất kỳ ngưỡng nào không đạt | DRAFT (review queue) |

Threshold đề xuất (thay cho 0.90/0.75 ví dụ của anh): auto **≥ 0.85** cho LOW vì LOW đã được template hoá phần lớn,
rủi ro thực nằm ở judge chứ không ở classifier; MEDIUM yêu cầu 0.90; dưới **0.70** → không draft, đưa thẳng UNRESOLVED
để tiết kiệm token. Khoảng 0.70–0.84 → draft + review. Con số này sẽ **hiệu chỉnh lại sau benchmark 50–100 comment**
(mục X), không nên chốt cứng bây giờ.

**Policy thắng model (mục 76):** output của classifier chỉ là *gợi ý*; bảng trên là code Python, model không có đường
nào ghi đè. Ví dụ model phân loại HOSTILE nhưng "đề xuất giải thích lại" → policy vẫn ép template.

---

## H. Japanese Tone & Politeness Policy — `REPLY_TONE_PROFILE = senior_polite`

**Giọng:** chủ kênh (チャンネル運営者) nói với người xem lớn tuổi hơn hoặc ngang tuổi. Khiêm tốn, ấm, chậm rãi.

**Style guide (sẽ thành `comment_care/policy/ja_style_guide.md` + được nhúng vào system prompt):**

| Nên | Tránh |
|---|---|
| です・ます nhất quán; 「〜していただき、ありがとうございます」 | ございます chồng tầng kiểu tổng đài (「〜でございますでしょうか」) |
| 「お話」「ご経験」「お身体」「お気持ち」「お過ごしください」 | 「あなた」「お前」「〜さんは」 (không gọi tên/username) |
| Nhắc **đúng 1 chi tiết** viewer kể (「65歳で退職されたとのこと」) | Tóm tắt lại cả đời họ; lặp lại nguyên văn comment |
| 「〜かと思います」「〜かもしれません」 khi nêu ý | 「〜すべきです」「〜した方がいいです」「おっしゃる通りです」(xác nhận fact) |
| Kết: 「どうかお身体を大切にお過ごしください」「穏やかな日々が続きますように」 | 「頑張ってください！」「応援しています！！」, dấu chấm than, emoji |
| 1–4 câu, mỗi câu ≤ 60 ký tự | Văn dài, liệt kê, đầu dòng, ngoặc vuông, dấu ★ |
| 「私ども」「当チャンネル」 hiếm khi cần; mặc định không xưng | 「私も〜でした」(nhận vơ trải nghiệm), tuổi/giới/nghề của chủ kênh |
| Nếu cần khuyên: 「専門の窓口にご相談されるのも一つかと思います」 | Chẩn đoán, kê đơn, số liệu luật/thuế/年金 cụ thể |

**Độ dài theo nhóm** (không tính footer): GRATITUDE/AGREEMENT/REQUEST 1–2 câu · PRAISE/CRITICISM 2 câu ·
EXPERIENCE/EMOTIONAL/DISAGREEMENT/QUESTION_OPINION 2–4 câu · GRIEF 2–3 câu (ngắn hơn, không "an ủi dài") · HOSTILE 1 câu.

**Cấu trúc EXPERIENCE (mục 54):** 感謝 → 1 chi tiết cụ thể → 受け止め (ghi nhận góc nhìn, không đánh giá) → 結び
(chúc) → footer (theo policy M).

**Emoji:** mặc định **0**. Cho phép tối đa 1 ký tự 「🙏」 hoặc 「🌸」 chỉ ở PRAISE/GRATITUDE khi comment của viewer có emoji
trước. Không bao giờ ở GRIEF/HOSTILE/HEALTH.

**Username:** không 「@xxx様」. YouTube đã hiển thị thread.

**Controlled variation (mục 57):** thư viện `templates/ja/*.yaml` có 3 slot `kansha` (6 biến thể), `uketome`
(8), `musubi` (8). Template reply = chọn ngẫu nhiên có trọng số nhưng **không lặp cùng tổ hợp cho 2 reply liên tiếp
trong cùng video** (tra bảng `replies` 20 dòng gần nhất). LLM reply: system prompt kèm 3 reply gần nhất của kênh với
chỉ thị "đừng mở đầu giống các câu này".

---

## I. Sensitive / Hostile / Unclear Policy

### I1. HOSTILE — deterministic, không LLM generation

Đánh giá 3 câu:

| Câu | Nhận xét |
|---|---|
| 「はい、ご意見をお寄せいただき、ありがとうございます。」 | Chữ 「はい、」 mở đầu trong **văn viết** dễ đọc thành 「はいはい」 (cho qua, dửng dưng) với người Nhật → **không khuyến nghị** |
| 「ご意見をお寄せいただき、ありがとうございます。」 | Tự nhiên, trung tính, đúng tinh thần "cảm ơn góp ý", không mở cửa tranh luận → **khuyến nghị** |
| 「貴重なご意見をありがとうございます。今後の参考にさせていただきます。」 | Cũng ổn nhưng 「参考にさせていただきます」 ngụ ý sẽ tiếp thu → với comment vô lý có thể bị viewer khác hiểu là thừa nhận. Dùng cho CRITICISM_CONSTRUCTIVE thì hợp hơn |

→ Template HOSTILE duy nhất: **「ご意見をお寄せいただき、ありがとうございます。」** Không footer (khuyến nghị, Z-5).
Nếu `hostile_confidence ≥ 0.90` → gửi template (khi auto bật cho nhóm này, Phase 5). Nếu 0.70–0.89 → DRAFT review.
Comment hostile có kèm **thông tin sai về kênh** (vd "動画は盗作") → vẫn template, không biện minh; ghi `HIGH_RISK`
để anh tự quyết có trả lời tay không.

### I2. GRIEF_LOSS

- Không 「頑張って」, không 「元気を出して」, không 「お気持ちはよく分かります」.
- Khung: 「お話を聞かせていただき、ありがとうございます。」→ 1 câu ghi nhận cụ thể nhưng không diễn giải nỗi đau
  (「奥様を亡くされてから、お一人で過ごされているとのこと」)→ 「どうかご無理をなさらず、お身体を大切にお過ごしください。」
- Judge bắt buộc với rubric riêng (mục L). Footer: **flag cho anh** (Z-6), khuyến nghị bỏ.
- Nếu có dấu hiệu CRISIS lẫn vào → chuyển CRISIS → ESCALATE, không reply.

### I3. HEALTH_SHARING / FINANCIAL_SPECIFIC

- Cấm số liệu, cấm xác nhận đúng/sai, cấm 「おっしゃる通り」. Chỉ 「貴重な情報をありがとうございます」 /
  「実際のご経験を共有していただき、ありがとうございます」 + chúc sức khoẻ.
- Nếu comment kèm **câu hỏi** cần chuyên môn → `QUESTION_FACTUAL` → SKIP/UNRESOLVED.
- V1 không fact-check bằng web search (tốn, dễ sai, không cần cho mục tiêu "chăm sóc").

### I4. UNCLEAR — HARD RULE

Bất kỳ điều kiện nào trong mục 9 brief → không draft, ghi `UNRESOLVED_COMMENTS.txt` theo đúng format anh yêu cầu
(CHANNEL/VIDEO/VIDEO_TITLE/VIDEO_URL/COMMENT_ID/COMMENT_URL/AUTHOR/COMMENT/REASON_NOT_REPLIED/MODEL/CONFIDENCE).
Comment URL dựng được: `https://www.youtube.com/watch?v=<video_id>&lc=<comment_id>` (YouTube mở thẳng thread).

### I5. Hard blocklist (rule-based, chạy trước judge)

Regex/substring trên draft: `お前|あんた|あなたは間違|勉強して|理解していない|そんなことも|常識|当たり前|はぁ|笑$|w$|ｗ|
おっしゃる通り|間違いありません|必ず|絶対に|私も.*(退職|定年|歳)|私は\d+歳|年金は.*円|税率|控除|診断|処方|治療法|
@|http|\.com|LINE|登録はこちら` + bất kỳ ký tự Latin/tiếng Việt có dấu, JSON brace, chữ "CATEGORY", "CONFIDENCE",
tên kênh khác trong `channels.yaml`. Khớp → `DO_NOT_SEND`, regenerate 1 lần, vẫn khớp → SKIP.

---

## J. Context Retrieval (đủ nhưng rẻ)

| Tầng | Nguồn | Khi nào nạp | Kích thước |
|---|---|---|---|
| L0 | `channel_name`, `handle`, `niche`, `tone_profile`, `owner_facts` (rỗng) | luôn | ~200 token |
| L1 | `videos.title` + `videos.description` (cắt 600 ký tự đầu, bỏ hashtag/link) từ Data API | luôn | ~400 token |
| L2 | Thread: top-level + owner reply + viewer follow-up (toàn bộ, cắt 1.500 ký tự) | khi comment là reply hoặc thread có owner reply | ≤ 800 token |
| L3 | `S1_TOM_TAT.json` → `tom_tat`, `y_chinh`, `cam_xuc_dinh`, `khong_duoc_noi_qua` | chỉ EXPERIENCE/EMOTIONAL/GRIEF/DISAGREEMENT/QUESTION_OPINION/FOLLOW_UP **và** map được tập | ~500 token |
| L4 | `promise.txt` / `title.txt` của tập | khi không có S1_TOM_TAT | ~100 token |
| Full transcript / `script.txt` | **không bao giờ** trong V1 | — |

Map `video_id → tập h2dev`: đọc tab lane trên sheet (cột L = video_id, cột A = STT), STT ↔ `epNN` trong
`h2dev_assets_dir`. Không map được → dùng L1 thôi và ghi `context_level=L1` vào log (judge sẽ chặt hơn về
"không bịa nội dung video"). Cache video context trong SQLite `videos.context_json` 7 ngày.

---

## K. Reply Generation Architecture

```
comment + ChannelContext + VideoContext
        │
        ▼
[1] PRE-FILTER (deterministic, 0 token)
    is_owner? dup? spam regex (url/LINE/emoji≥5)? not-ja (ký tự kana/kanji < 30%)? length ≤ 30 & khớp pool GRATITUDE?
        │
        ▼
[2] CLASSIFY + UNDERSTAND  (LLM rẻ, JSON schema cố định, temperature 0.1)
    → {primary, secondary[], flags{}, summary_ja(≤60字), key_detail_ja(≤40字), classification_conf, understanding_conf}
    JSON lỗi → parse lại 1 lần → vẫn lỗi → UNCLEAR
        │
        ▼
[3] POLICY ENGINE (mục G) → decision + generator_kind + footer_rule + risk
        │
   ┌────┴──────────────┐
   ▼                   ▼
TEMPLATE            LLM GENERATE
(pool có kiểm       (tier theo risk/category, temperature 0.3, max_tokens 300,
 soát, 0 token)      prompt_version pinned, output = chỉ text reply tiếng Nhật)
   └────┬──────────────┘
        ▼
[4] POST-PROCESS deterministic: strip, chuẩn hoá 。, bỏ dòng trống kép, gắn footer theo rule, đo độ dài
        ▼
[5] HARD BLOCKLIST (I5) → fail → regen (≤1)
        ▼
[6] JAPANESE QUALITY JUDGE (mục L, model khác họ) → PASS / FAIL(lý do)
        fail → regen với feedback (≤2 lần tổng) → vẫn fail → SKIP + UNRESOLVED (reason = judge_fail:<rubric>)
        ▼
[7] GATE (mục G) → SEND | DRAFT | SKIP
```

Prompt generation chứa rõ: "Bạn là người vận hành kênh `<channel_name>`. Bạn **không** có thông tin cá nhân nào về
bản thân ngoài danh sách `owner_facts` (hiện rỗng) → không được nói về tuổi, giới, nghề, gia đình, trải nghiệm của
mình. Chỉ trả về đúng đoạn reply tiếng Nhật, không giải thích." (mục 41–42).

---

## L. QC / Judge Architecture

Hai lớp:

**L-A Rule QC (Python, 0 token):** Japanese-only (tỉ lệ kana/kanji ≥ 60%, không ký tự Việt/Latin ngoài số),
độ dài trong khung, không JSON/label/ngoặc vuông, không tên kênh khác, không `@`, footer đúng y chang chuỗi trong
config (nếu rule bảo gắn) hoặc không có (nếu rule bảo bỏ), không trùng 100% với reply đã gửi trong 30 ngày.

**L-B LLM Judge (model khác họ với generator):** trả JSON 9 tiêu chí anh nêu (mục 75) mỗi cái `PASS|FAIL` + lý do
ngắn, cộng `reply_confidence 0–1`:

1. 日本語として自然か 2. 丁寧か 3. 高齢者に失礼ではないか 4. 上から目線ではないか 5. 反論しすぎていないか
6. コメント内容に合っているか (kèm `key_detail_ja` để judge check có nhắc đúng chi tiết không bịa)
7. AIっぽすぎないか 8. 不必要な断定がないか (đặc biệt về 年金/税/健康) 9. CTAが不自然ではないか
+ 10. **運営者の個人情報・経験を捏造していないか** (thêm, vì mục 41) + 11. **動画内容を捏造していないか**
(so với VideoContext).

Bất kỳ FAIL → regen với lý do đính kèm; tối đa 2 regen; vẫn FAIL → SKIP. GRIEF/HEALTH: judge chạy **2 model**
(sol + gemini), cần cả hai PASS (pattern `_MODEL_HOI_LAI` của `qc_visual.py`).

---

## M. CTA / Footer Strategy

**Đánh giá câu baseline của anh:**

> ご視聴いただき、ありがとうございます。よろしければ高評価とチャンネル登録をお願いいたします。
> また、ベルマークを押して通知をオンにしていただくと、新しい動画を見逃さずにご覧いただけます。

- *Tự nhiên/lịch sự:* đạt. 「ベルマーク」 là từ người Nhật dùng thật; 「通知をオン」 ổn với người lớn tuổi.
- *Dài:* 2 câu ≈ 95 ký tự, **thường dài hơn phần reply chính** (2–4 câu ≈ 80–150 ký tự) → tỉ lệ CTA/nội dung quá cao,
  mắt người đọc thấy CTA trước khi thấy sự chân thành.
- *Giống spam:* nguy cơ thật ở 2 chỗ. (a) Bộ lọc của YouTube coi **cùng một đoạn text lặp lại nhiều lần từ cùng tài
  khoản** là tín hiệu spam; reply của chủ kênh ít bị ẩn hơn comment lạ nhưng không miễn nhiễm, và quan trọng hơn là
  **cảm nhận người xem khác** khi lướt thread thấy 30 reply kết bằng cùng 2 câu. (b) Người xem đã comment thì **đa số
  đã subscribe**; xin đăng ký với người đã đăng ký đọc như không nhớ họ.
- *Phản cảm:* chắc chắn ở GRIEF_LOSS, HOSTILE, CRISIS (không reply), HEALTH nặng, và ở reply **thứ 2 trong cùng thread**.

**Ba phương án (giữ nguyên yêu cầu của anh, chỉ thêm rủi ro + khuyến nghị):**

| | OPTION A — 100% | OPTION B — bỏ ở grief/hostile/sensitive | OPTION C — rotate 2–4 phiên bản |
|---|---|---|---|
| Đúng yêu cầu gốc | Tuyệt đối | Có ngoại lệ rõ ràng | Có, nội dung CTA giữ |
| Rủi ro spam-pattern | Cao nhất | Trung bình | Thấp |
| Rủi ro phản cảm | Có (grief/hostile) | Không | Còn ở grief/hostile nếu không kết hợp B |
| Chân thành | Giảm rõ ở comment sâu | Giữ | Giữ |
| Phức tạp code | Nhỏ nhất | Nhỏ | Nhỏ |

**Khuyến nghị: B + C kết hợp ("BC")**, với 3 biến thể đã rút gọn còn 1 câu, dùng luân phiên theo video:

- V1: 「ご視聴いただきありがとうございます。よろしければ高評価・チャンネル登録もお願いいたします。」
- V2: 「いつもご覧いただきありがとうございます。チャンネル登録とベルマークの通知設定をしていただけると励みになります。」
- V3: 「ご視聴ありがとうございます。新しい動画を見逃さないよう、よろしければ通知をオンにしていただければ幸いです。」
- V-full (bản 2 câu của anh): dùng cho reply **đầu tiên** của mỗi video (comment sớm nhất), 1 lần/video.

Ngoại lệ bỏ footer (B): `GRIEF_LOSS`, `HOSTILE`, `HEALTH_SHARING` (risk HIGH), `FOLLOW_UP_TO_OWNER` (reply lần 2
trong thread), `DISAGREEMENT_POLITE` nếu judge chấm tiêu chí 9 FAIL. Cấu hình bằng `footer_policy` per channel nên
anh đổi A/B/C/BC bất kỳ lúc nào không cần sửa code. **Không triển khai phương án nào trước khi anh chốt Z-4.**

---

## N. Model Routing (chỉ model/provider có thật trong repo)

| Task | Model | Provider (base_url) | Fallback | Cost | Lý do |
|---|---|---|---|---|---|
| Dedup, thread build, spam regex, GRATITUDE pool match, footer, blocklist, length | — | Python | — | 0 | Deterministic, mục 34 |
| Language detect | — | Python (tỉ lệ kana/kanji) | — | 0 | Không cần LLM |
| Classify + understand (JSON) | `gemini-3.8-flash` | ramclouds `https://ramclouds.me` qua `llm_client.chat(task="comment_classify")` | ns24 `gemini-3.8-flash` → ns24 `deepseek-v4.1-flash` → sol `gpt-5.6-sol` | thấp | Chain `analysis` sẵn có; đổi temperature 0.1, `max_tokens` 400 |
| Generate: PRAISE/CRITICISM slot nhỏ, QUESTION_OPINION | `gemini-3.8-flash` | ramclouds | ns24 `gemini-3.8-flash` → sol | thấp | Câu ngắn, template-guided |
| Generate: EXPERIENCE / EMOTIONAL / GRIEF / DISAGREEMENT / FOLLOW_UP | `claude-opus-5-5` (hoặc `claude-fable-5-1`) | `claude_p_bridge.ask()` (Claude Code CLI, không API key) | `gpt-5.6-sol` qua `sol_client` → `gemini-3.8-flash` | cao nhưng theo subscription | Nuance tiếng Nhật + đọc kỹ chi tiết; đúng pattern `hook_stage.py:633` |
| Judge (reply của Claude) | `gpt-5.6-sol` | `sol_client`: 9router `http://localhost:20128/v1` → ns24 → hhtechapi | `gemini-3.8-flash` | trung bình | Khác họ với generator (`qc_loi_hua.py` pattern) |
| Judge (reply của gemini / template) | `claude-sonnet-5-5` qua `claude -p` | Claude CLI | `gpt-5.6-sol` | trung bình | Khác họ; sonnet rẻ hơn opus, đủ cho chấm rubric |
| Judge lớp 2 cho GRIEF/HEALTH | `gemini-3.8-flash` | ramclouds | ns24 | thấp | Cần 2 PASS |
| Benchmark (Phase 2) | tất cả 5: `gemini-3.8-flash`, `deepseek-v4.1-flash`, `gpt-5.6-sol`, `claude-opus-5-5`, `claude-fable-5-1` | như trên | — | 1 lần | Chọn generator chính bằng số liệu, không bằng cảm tính |

Ghi chú kỹ thuật:
- `llm_client.CHAINS` hiện không có task `comment_*`; wrapper trong repo này sẽ truyền `provider=`/`model=` tường
  minh từng bước thay vì sửa h2dev (0 thay đổi ở h2dev, không cần anh duyệt thêm).
- `claude -p` không chỉnh được temperature → bù bằng system prompt rất chặt + judge. Nếu benchmark cho thấy Opus
  "sáng tạo quá", đổi sang `gemini-3.8-flash` temperature 0.3 làm generator chính.
- `anthropic 0.97` đã cài nhưng **không có key** nào trong repo → không dùng SDK trực tiếp trong V1.
- Usage (tokens, provider, model, elapsed, attempts) từ `ChatResult` ghi vào bảng `llm_calls` mỗi lần gọi.

---

## O. State / Database — SQLite

Path: `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\state\comment_care.sqlite` (gitignore). WAL mode.

```sql
channels   (channel_id PK, channel_name, handle, lane, sheet_tab, mode, footer_policy, daily_cap,
            watermark_updated_at, identity_verified_at, last_run_id)
videos     (video_id PK, channel_id FK, title, description_head, published_at, ep_slug, context_level,
            context_json, context_cached_at)
comments   (comment_id PK, channel_id FK, video_id FK, parent_id, author_channel_id, author_display,
            text, like_count, published_at, updated_at, is_owner, is_reply, can_reply,
            discovered_at, raw_json, UNIQUE(channel_id, comment_id))
classifications (id PK, comment_id FK, run_id FK, primary_cat, secondary_cats, flags_json, summary_ja,
            key_detail_ja, classification_conf, understanding_conf, model, provider, prompt_version, created_at)
decisions  (id PK, comment_id FK, run_id FK, decision, risk, generator_kind, footer_rule, policy_version, reason)
drafts     (id PK, comment_id FK, run_id FK, attempt_no, text_body, footer_text, final_text, model, provider,
            prompt_version, rule_qc_json, judge_json, judge_model, reply_conf, status
            /* GENERATED|BLOCKED|JUDGE_FAIL|APPROVED|EDITED|REJECTED */, created_at)
replies    (id PK, channel_id FK, comment_id FK, draft_id FK, idempotency_key UNIQUE /* channel_id:comment_id */,
            final_text, status /* SENDING|SENT|FAILED|UNKNOWN_RECONCILE */, youtube_reply_id, sent_at,
            api_response_json, error)
runs       (run_id PK, started_at, finished_at, mode, channels_json, counts_json, quota_used, git_sha, policy_version)
errors     (id PK, run_id FK, channel_id, comment_id, stage, error_type, message, created_at)
llm_calls  (id PK, run_id FK, comment_id, stage, provider, model, tokens_in, tokens_out, elapsed_s, attempts, ok)
review_queue (draft_id PK FK, queued_at, decided_at, decision /* APPROVE|EDIT|REJECT|SKIP */, edited_text, note)
```

Audit trail (mục 46) = join `comments → classifications → decisions → drafts → replies` theo `comment_id`,
có CLI `audit --comment-id` in ra chuỗi đó dạng TXT.

---

## P. Folder Structure (đề xuất, chưa tạo)

```
E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\
  comment_care\
    README.md
    config\
      channels.yaml.example          (commit)   channels.yaml (gitignore — có mail thật)
      settings.yaml                  (batch size, cap, quota budget, retention)
    policy\
      POLICY_v1.md                   (bảng G, I — bản người đọc)
      policy_table.yaml              (bảng G dạng máy đọc, có policy_version)
      ja_style_guide.md
      blocklist_ja.txt
    prompts\v1\
      classify.system.md  classify.schema.json
      generate_senior_polite.system.md
      judge_ja.system.md  judge.schema.json
    templates\ja\
      gratitude.yaml  agreement.yaml  request.yaml  criticism.yaml  financial_info.yaml  hostile.yaml  footer.yaml
    src\comment_care\
      __init__.py  cli.py  context.py (ChannelContext/VideoContext)  config.py
      yt_api.py (fetch/insert/verify identity, quota meter)  oauth.py (load token, không tự tạo)
      store.py (SQLite)  prefilter.py  classifier.py  policy.py  templates.py
      generator.py  qc_rules.py  judge.py  footer.py  sender.py (idempotent)  reconcile.py
      llm.py (wrapper mỏng gọi h2dev llm_client / sol_client / claude_p_bridge)
      report.py  review.py (APPROVE/EDIT/REJECT từ TXT)  insight.py (V2, stub)
    state\                           (gitignore) comment_care.sqlite, quota_YYYY-MM-DD.json
    tests\                           fixtures 50–100 comment ẩn danh hoá + unit test policy/qc
  reports\comment_care\YYYY-MM-DD\   (gitignore)
      COMMENT_REPORT.txt  UNRESOLVED_COMMENTS.txt  DRAFT_REVIEW.txt  SHADOW_REVIEW.txt  HIGH_RISK.txt  reply_log.jsonl
```

---

## Q. Reporting

`COMMENT_REPORT.txt` theo đúng khung mục 43 của anh, cộng thêm: `Quota used / budget`, `LLM calls by model`,
`Identity check per channel`, `Context level distribution (L1/L3)`. `DRAFT_REVIEW.txt` theo format mục 70
(COMMENT / CATEGORY / PROPOSED REPLY / CONFIDENCE / ACTION=WOULD_REPLY|WOULD_SKIP), mỗi block có `DRAFT_ID` để anh
ghi `APPROVE|EDIT:<text>|REJECT|SKIP` vào ngay dưới; `review.py` đọc lại file này. Cuối run in ra terminal đúng câu
"Có X bình luận chưa được trả lời. Xem tại: <PATH>" (mục 10). Không giấu lỗi: `Errors: N` + 5 lỗi đầu in thẳng.

## R. Unresolved Comment Workflow

UNCLEAR / SKIP / judge-fail / ESCALATE → `UNRESOLVED_COMMENTS.txt` (format mục 9). Anh xử lý tay trên YouTube
hoặc ghi `REPLY_MANUAL_DONE` → lần sau tool thấy owner reply trong thread → tự đóng. Comment nằm UNRESOLVED **không
bị đưa lại vào LLM** ở run sau (tiết kiệm), trừ khi `--retry-unresolved`.

## S. Error Recovery

| Tình huống | Xử lý |
|---|---|
| Quota exhausted (403 `quotaExceeded`) | Dừng mọi gọi API của run, ghi `quota_YYYY-MM-DD.json`, báo đỏ; run sau cùng ngày chỉ chạy offline (classify/draft từ cache) |
| OAuth expired / refresh fail | Kênh đó → `AUTH_ERROR`, bỏ qua, in hướng dẫn authorize lại; **không** chuyển sang token kênh khác |
| Comment/video deleted (404) | Mark `comments.deleted_at`, không reply |
| Comments disabled / `canReply=false` | SKIP lý do kỹ thuật |
| API/provider timeout | retry theo `llm_client` (2/model) + chain; API YouTube: 3 lần backoff 2/4/8s; insert **không retry mù** (xem T) |
| Model trả JSON hỏng | parse lại 1 lần với prompt sửa → UNCLEAR |
| Japanese QC fail | regen ≤2 → SKIP |
| Crash giữa batch | mọi bước ghi SQLite theo transaction nhỏ; resume bằng `runs.finished_at IS NULL` → bỏ qua comment đã có `decisions` của run dở |
| **Network fail sau insert, trước khi ghi state** | mục T |

## T. Duplicate Prevention

1. `replies.idempotency_key = channel_id:comment_id` UNIQUE → DB từ chối lần 2.
2. Trình tự gửi: `INSERT replies(status=SENDING)` **commit** → gọi `comments.insert` → `UPDATE status=SENT,
   youtube_reply_id` commit. Crash giữa 2 bước → row kẹt `SENDING`.
3. Khi khởi động, `reconcile.py` quét `SENDING`: gọi `comments.list parentId=<comment_id>` (1 unit), tìm reply có
   `authorChannelId == channel_id` và `textOriginal == final_text` (hoặc đăng sau `sent_at - 5 phút`) → `SENT` +
   lấy `youtube_reply_id`; không tìm thấy → `UNKNOWN_RECONCILE`, **không tự gửi lại**, đưa vào HIGH_RISK để anh xem.
4. Trước mỗi lần gửi còn check lại thread live: nếu đã có owner reply (do anh trả lời tay trong lúc tool chạy) → huỷ.
5. Fingerprint text: không gửi reply có `final_text` trùng 100% với reply đã SENT cùng video trong 30 ngày
   (ngoại lệ template HOSTILE/GRATITUDE vẫn phải khác slot tổ hợp).

## U. Rate / Cost Control

| Tham số | Giá trị khởi điểm | Ghi chú |
|---|---|---|
| Comment fetch/run/kênh | ≤ 200 thread | 2 unit |
| Comment đưa vào LLM/run/kênh | ≤ 50 | ưu tiên mới nhất; còn lại run sau |
| Reply gửi/run/kênh | ≤ 20 | |
| Daily cap/kênh | 30 | Phase 4: **10**; AUTO lần đầu: hard cap 5/kênh/ngày trong 3 ngày |
| Daily cap toàn hệ | 60 reply (= 3.000 unit) | quota budget tổng cho module: 6.000/10.000 unit, phần còn lại để TRENDING-RESEARCH |
| Khoảng cách giữa 2 insert | ngẫu nhiên 20–60s, cùng kênh | trông như người |
| Khung giờ gửi | 08:00–22:00 JST | reply 3h sáng giờ Nhật trông như bot |
| Token budget/run | cảnh báo khi > 150k tokens | ghi `llm_calls` |
| Retries | API 3 lần backoff; LLM theo chain; judge regen ≤ 2 | |

## V. Security / Privacy

- Token OAuth: `D:\CLAUDE\credentials\youtube_oauth\<channel_id>.json`, không bao giờ trong repo; `channels.yaml`
  thật gitignore (có mail), chỉ commit `.example`.
- Không thêm API key hardcode. Key lấy qua env hoặc cơ chế `keys.py` sẵn có của h2dev.
- Raw comment (author, text) chỉ nằm trong SQLite + `reports\comment_care\` (gitignore). **Retention:** raw text và
  author 90 ngày → job `purge` xoá text, giữ `comment_id`, category, decision, hash. Aggregate insight giữ vô hạn.
- Không build profile cá nhân viewer (mục 65). Bảng `comments` không có index theo `author_channel_id` ngoài phục vụ
  dựng thread; `insight.py` chỉ aggregate theo category/keyword/tuần.
- Khi gọi provider ngoài (ramclouds/ns24/hhtech là proxy bên thứ ba), comment text **có đi qua họ**. Tối thiểu hoá:
  gửi text comment + context, không gửi author name, không gửi URL.
- Khuyến nghị ngoài phạm vi: xoay key đang lộ trong h2dev git (B2) — không thuộc module này.

## W. Rollout Plan

| Phase | Nội dung | Điều kiện sang phase sau | Mode |
|---|---|---|---|
| 0 | Audit + proposal (tài liệu này) | Anh APPROVE | — |
| 1 | `store`, `yt_api` (fetch bằng API key), `prefilter`, `classifier`, report. **Không OAuth, không draft** | 1 tuần dữ liệu; phân phối category hợp lý khi anh soi 50 comment | `fetch_only` |
| 2 | `policy`, `templates`, `generator`, `qc_rules`, `judge`, `DRAFT_REVIEW.txt`, `review.py`; **benchmark 5 model** trên 50–100 comment thật (mục X) | Anh chọn generator chính; ≥ 90% draft được APPROVE không sửa ở nhóm LOW | `draft_only` |
| 2b | Anh authorize OAuth `youtube.force-ssl` cho **1 kênh pilot** (đề xuất Satori — 11 video, nhiều comment nhất); `identity verify`, `sender` + `reconcile` viết nhưng `send` bị kill switch chặn | CASE 6/7/8 pass bằng test giả lập | `draft_only` |
| 3 | Shadow 100 comment hoặc 5 ngày trên kênh pilot → `SHADOW_REVIEW.txt` | Anh chấm: tone, đúng ý, lỗi, "đáng lẽ không nên reply" ≤ 2% | `shadow` |
| 4 | Auto cho LOW (GRATITUDE, PRAISE, AGREEMENT, REQUEST, EXPERIENCE_SHARING không flag) kênh pilot, cap 5→10/ngày | 2 tuần không sự cố | `auto_low` |
| 5 | Mở MEDIUM (DISAGREEMENT, CRITICISM, QUESTION_OPINION, FOLLOW_UP lần 1), HOSTILE template; thêm kênh | Mỗi kênh mới đi lại 2b→3 rút gọn (shadow 30 comment) | `auto_full` |
| 6 | Daily (anh tự lập lịch bằng Task Scheduler/`/loop`; module không tự tạo scheduler) + `AUDIENCE_INSIGHTS_WEEKLY.md` (V2) | — | — |

Kill switch 3 lớp, **cả 3 phải đồng ý mới gửi**: env `COMMENT_CARE_AUTO_REPLY=1` (mặc định không set = tắt) +
`channels.yaml mode ∈ {auto_low, auto_full}` + cờ CLI `--send`. Config lỗi parse / thiếu token / identity mismatch →
fail closed = `draft_only`. `--dry-run` luôn thắng mọi thứ.

## X. Acceptance Tests

| Case | Input | Kỳ vọng |
|---|---|---|
| 1 | 「再雇用」 (2 chữ) | UNCLEAR, understanding_conf < 0.7, không draft, vào UNRESOLVED; reply không được bịa "再雇用されたご経験" |
| 2 | 8 dòng: nghỉ 66 tuổi, sống bằng 年金, không bất hạnh | EXPERIENCE_SHARING; draft nhắc đúng **1** chi tiết (66歳 hoặc 年金生活) không nhắc hết; judge tiêu chí 6/11 PASS |
| 3 | 「こんな動画作って恥ずかしくないのか。全部嘘。」 | HOSTILE ≥ 0.9; final_text == template cố định; không footer (nếu Z-5a); không câu nào khác |
| 4 | 「65歳から年金を繰り下げると何%増えますか？」 | QUESTION_FACTUAL → SKIP; không có số % nào trong bất kỳ draft nào (blocklist bắt `%`/`円` nếu lọt) |
| 5 | Tiếng Nhật rối/typo đổi nghĩa/kanji lạ | UNCLEAR → `UNRESOLVED_COMMENTS.txt` có đủ 11 field + COMMENT_URL `watch?v=…&lc=…` |
| 6 | Thread đã có owner reply, không follow-up | ALREADY_HANDLED; 0 LLM call; không có row `drafts` |
| 7 | Giả lập crash sau `comments.insert` (mock trả 200, raise trước UPDATE) → chạy lại | reconcile tìm thấy reply → SENT; **0** insert mới; nếu mock không trả reply → UNKNOWN_RECONCILE, vẫn 0 insert |
| 8 | Token của kênh B gán cho channel A trong config | `channels.list mine` lệch → IDENTITY_MISMATCH; kênh A bị skip toàn bộ; không fetch, không send |
| 9 | Mock generator trả câu tiếng Việt hoặc lẫn "Cảm ơn" | Rule QC Japanese-only FAIL → regen → SKIP; không bao giờ tới sender |
| 10 | Mock generator trả 「あなたは動画を理解していないようですね」 | Blocklist bắt + judge tiêu chí 4 FAIL → DO_NOT_SEND |
| 11 | GRIEF: 「去年妻を亡くし、一人です」 | GRIEF_LOSS; không 「頑張って」; footer theo Z-6; 2 judge PASS mới DRAFT; risk HIGH → không auto |
| 12 | 「死にたくなる」 lẫn trong experience | CRISIS → ESCALATE, HIGH_RISK.txt, 0 draft |
| 13 | Kill switch: env bật, config `auto_low`, **thiếu** `--send` | 0 insert; report ghi "SEND BLOCKED: cli flag" |
| 14 | 30 GRATITUDE liên tiếp cùng video | Không 2 reply liên tiếp cùng tổ hợp slot; không 2 final_text trùng 100% |
| 15 | Daily cap 5 đã đạt, còn 10 draft APPROVED | 10 cái giữ APPROVED, gửi ngày sau; report ghi rõ |

Benchmark (Phase 2): 50–100 comment thật từ kênh Satori (fetch bằng API key, ẩn danh hoá author), 5 model ở mục N,
chấm 8 tiêu chí mục 59 theo thang 1–5 bởi anh + 1 judge model; chọn generator chính theo tổng điểm có trọng số
Politeness ×2, Hallucination ×2, Senior-suitability ×1.5.

## Y. Files To Create / Modify (CHỈ LIỆT KÊ)

**Tạo mới** (toàn bộ dưới `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\comment_care\` như mục P): ~22 file `.py`,
3 prompt set, 7 template yaml, 2 policy file, 2 config, `README.md`, `tests\`.

**Sửa (nhỏ, trong repo này):**
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\.gitignore`: thêm `comment_care/state/`, `comment_care/config/channels.yaml`,
  `reports/comment_care/`.
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\CLAUDE.md`: mục "⛔ VAI TRÒ" thêm ngoại lệ có kiểm soát cho module này
  (Z-3) + mục mô tả comment_care.
- `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\README.md`: thêm mục.

**Không sửa:** bất kỳ file nào trong `E:\CLAUDE\YOUTUBE\h2dev\` (wrapper import, không chỉnh `CHAINS`);
`D:\CLAUDE\credentials\token.json` (token Sheets/Drive giữ nguyên, YouTube token là file **mới riêng**);
Google Sheet (chỉ đọc cột L/A để map video→tập; không ghi gì trong V1).

## Z. Decisions I Need To Approve

| # | Quyết định | Phương án | Khuyến nghị |
|---|---|---|---|
| Z-1 | **Kênh gửi reply** | (a) YouTube Data API `comments.insert` + OAuth `youtube.force-ssl` per Gmail · (b) Studio browser automation qua GPM/AdsPower (gõ reply trên trang Comments) | **(a)**: có `youtube_reply_id`, idempotency chắc, quota rõ; (b) chỉ làm fallback nếu OAuth bị vướng |
| Z-2 | **OAuth consent screen** | (a) dùng lại project `fifth-glider-495702-b4`, chuyển consent sang *In production* (unverified, chấp nhận màn cảnh báo khi authorize) · (b) giữ *Testing* (token chết sau 7 ngày, authorize lại hàng tuần) · (c) tạo GCP project mới riêng cho comment care | **(c)** nếu muốn tách quota với TRENDING-RESEARCH, không thì **(a)**. (b) không chạy daily được |
| Z-3 | Sửa luật "Claude KHÔNG đụng YouTube" trong CLAUDE.md | (a) thêm ngoại lệ: *chỉ* `comment_care` được post reply, chỉ khi 3 kill switch bật · (b) giữ nguyên → module dừng ở `draft_only` vĩnh viễn, anh dán tay | **(a)** nhưng chỉ sau Phase 3 |
| Z-4 | **Footer** | A / B / C / **BC** (mục M) | **BC** |
| Z-5 | Footer với HOSTILE | (a) không footer · (b) có footer | **(a)**; ngoài ra chọn template 「ご意見をお寄せいただき、ありがとうございます。」 hay giữ 「はい、…」 |
| Z-6 | Footer với GRIEF_LOSS / CRISIS / HEALTH nặng | (a) không footer · (b) có | **(a)** |
| Z-7 | Câu template HOSTILE | 3 câu ở I1 | 「ご意見をお寄せいただき、ありがとうございます。」 |
| Z-8 | Kênh pilot Phase 2b–4 | Satori (`UC9huXCiBIXBfUh11D7ZsFSA`, 11 video) hay kênh khác | Satori |
| Z-9 | Generator mạnh | `claude-opus-5-5` qua `claude -p` (dùng subscription Claude Code) hay `gpt-5.6-sol` hay `gemini-3.8-flash` | Chốt **sau benchmark**; tạm Opus |
| Z-10 | `owner_facts` | Để trống (reply không bao giờ nói về bản thân chủ kênh) hay anh cung cấp vài fact chung per lane (vd "kênh do nhóm nhỏ vận hành") | **Trống** trong V1 |
| Z-11 | Retention raw comment | 90 ngày / 30 ngày / vô hạn | 90 ngày |
| Z-12 | Emoji | 0 tuyệt đối / tối đa 1 ở PRAISE khi viewer dùng trước | 0 tuyệt đối ở Phase ≤4 |

---

```text
STATUS: WAITING_FOR_APPROVAL

Recommended implementation order:
1. Phase 1 — store.py + yt_api.py (fetch bằng API key có sẵn) + prefilter + classifier + COMMENT_REPORT/UNRESOLVED.
   Chạy 1 tuần trên Satori để có dữ liệu thật cho taxonomy + benchmark. Không OAuth, không draft.
2. Phase 2 — policy engine + templates + generator + rule QC + judge + DRAFT_REVIEW/review.py;
   benchmark 5 model trên 50–100 comment thật → chốt Z-9.
3. Phase 2b — anh authorize OAuth youtube.force-ssl cho kênh pilot; identity verify + sender + reconcile
   (bị kill switch chặn); test CASE 6/7/8/13 bằng mock.
4. Phase 3 — Shadow 100 comment → SHADOW_REVIEW.txt → anh duyệt.
5. Phase 4 — auto LOW, cap 5/ngày, 1 kênh. Sau đó Phase 5–6.

Critical decisions requiring owner approval:
1. Z-1 + Z-2: gửi bằng Data API OAuth (per-Gmail, consent In production hoặc project mới) hay Studio automation.
2. Z-4/5/6/7: footer BC + bỏ footer ở HOSTILE/GRIEF + câu template HOSTILE.
3. Z-3: cho phép ngoại lệ "post reply" trong CLAUDE.md của dự án (chỉ sau Phase 3).
4. Z-8/9: kênh pilot Satori; generator chính chốt sau benchmark.
```
