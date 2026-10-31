# 04 — DATABASE AND HISTORY

Audit only. All numbers below were produced by read-only scripts over the existing files; nothing was
modified, appended to, or deleted.

---

## 1. WHERE THE DATA LIVES

| # | Store | Path | Type | Size / records | Updated by | Freshness |
|---|---|---|---|---|---|---|
| 1 | **Google Sheet** (primary, live) | id `1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU`, 22 tabs | Google Sheets | 17 lane-like tabs; **138 video_ids**, 126 rows with N+O | 05:00 job (daily) + human | **live (2026-10-27)** |
| 2 | **Pre-write tab snapshots** | `reports/daily_0500/<YYYY-MM-DD>/<tab>_truoc.json` | JSON (full A:S values + K yellow flags) | **12 days × up to 9 tabs**; 12 581 lines total | 05:00 job | **live (2026-10-27)** |
| 3 | **Metrics CSV** | `youtube_postpublish_metrics.csv` | CSV, 70 columns | **174 rows / 84 videos / 8 channels** | `tools/studio_collect.py` — **manual** | **stale: last row 2026-10-18 06:48** |
| 4 | **Spike snapshots** | `view_spike/state/snapshots.jsonl` | JSONL | **2 744 lines** `{t, vid, views}` | `spike_watch.py` — task **Disabled** | stale: last 2026-10-18 07:52 |
| 5 | Spike alerts | `view_spike/state/alerts.jsonl` | JSONL | **4 lines** | same | stale |
| 6 | Spike metadata cache | `view_spike/state/meta.json` | JSON | 25 KB: `{sheet_at, tabs, videos:{published, channel_id, title}}` | `spike_sources.refresh_meta()` | stale |
| 7 | **Comment-care DB** | `comment_care/state/comment_care.sqlite` | SQLite, **11 tables** | see §6 | comment_care module | active, but a different subsystem |
| 8 | Run logs | `reports/daily_0500/<date>.log` | text | 12 files, up to 185 KB | 05:00 job | live |
| 9 | Sol review output | `reports/<vid>/sol_packaging_review.md` | Markdown | **1 file** (`yCSzCQN_VsE`) | manual | one-off |

**There is no database for performance data.** No SQLite/Postgres/DuckDB store holds metrics; the CSV and
the JSON backups are the only persistent history.

---

## 2. SCHEMA — GOOGLE SHEET LANE TAB

Read live from `'F-teinengo-real'!A1:Z2` (identical layout on all lane tabs; column count 25–26):

| Col | idx | Header | Owner | Content |
|---|---|---|---|---|
| A | 0 | STT | human | row number, **N = row N+1** |
| B | 1 | NỘI DUNG – LANE … (+ mail in the cell) | human | title/description working notes |
| C | 2 | FOLDER | human | **filesystem path** to the episode's asset folder |
| D | 3 | KỊCH BẢN | human | **status text, not a path** in practice (e.g. `Done`, `Xong toàn bộ`) |
| E | 4 | TITLE-DESCREPTION | human | full title + description |
| F | 5 | TAGS | human | tags |
| G | 6 | THUMBNAIL | human | thumbnail URL |
| H | 7 | STATUS-IMG | human | |
| I | 8 | VIDEO | human | published-video folder |
| J | 9 | LIST | human | upload status |
| K | 10 | GHI CHÚ | **machine (05:00) + human** | verdict prose; **row painted yellow** when CTR 24h < 2.5 % |
| L | 11 | *(blank header, holds the video id)* | human/tool | **video_id — 11 chars, the join key** |
| M | 12 | channel URL | human | `https://www.youtube.com/@…` (or a login mail on some tabs) |
| **N** | 13 | SỐ NGÀY LIST | **machine** | `int(hours_since_publish // 24)` |
| **O** | 14 | VIEW | **machine** | lifetime views |
| **P** | 15 | CTR TỔNG | **machine** | lifetime CTR, string `6,30%` |
| **Q** | 16 | CTR 24H | **machine** | previous-day CTR, string `4,40%` (or blank) |
| **R** | 17 | VIEW CŨ | **machine** | previous run's O |
| **S** | 18 | CTR 24H CŨ | **machine** | previous run's Q |
| T | 19 | VIDEO GỐC | human | |
| U | 20 | ĐỀ XUẤT | human | **stale machine text from older runs** (e.g. `518h · 2.900 view · …`) |
| V | 21 | Thumbnail impressions 24h (F tab only) | unused | 1/104 filled |
| W | 22 | Bình Luận Ghim (N/O/M tabs) | human | pinned-comment text |

`TONGHOP` tab: row 1 = lane names in columns B..I, column A = `Ep01`, `Ep02`, …; cells hold
`Listed` / `SỬA CTR` / human free text (`daily_sheet.py:62-110`).

### Schema pitfalls for any consumer
1. **Column L header is blank on most tabs** but the id is always at index 11 (`CLAUDE.md`, and verified:
   reading `'F-teinengo-real'!L2:L500` returns the ids).
2. **`P`/`Q`/`S` are locale strings**, not numbers: `6,30%`. `O`/`N`/`R` are integers as text.
3. **Blank ≠ 0.** Blank means Studio had no value (dash / insufficient data).
4. **Column D is not a path** even though its header says KỊCH BẢN — it holds status words. Only column C
   is a path.
5. Rows with no id in L are invisible to the job (`daily_0500_run.py:103`).

---

## 3. SCHEMA — `youtube_postpublish_metrics.csv` (70 columns)

`tools/studio_collect.py:64-77` defines `COLUMNS`. Groups:

| Group | Columns | Fill (n/174) |
|---|---|---|
| Identity | `channel, lane, episode, video_id, title, publish_time, snapshot_time, hours_since_publish, video_length_sec` | `episode` **0**; others 170–174 |
| Reach/lifetime | `impressions, ctr, views, unique_viewers, engaged_views_from_impressions, watch_time_from_impressions_hours, avd_sec, apv_pct` | 127–169 |
| Traffic | `recommendation_pct, browse_pct, suggested_pct, search_pct, direct_pct, external_pct` | 41–146 (`external_pct` weakest) |
| Retention | `ret_5s, ret_10s, ret_20s, ret_30s, ret_60s` | **only `ret_30s` = 116; the other four are 0** |
| Suggesting/search | `top_suggesting_video_1/2, top_suggesting_channel_1/2, top_search_term_1, search_term_1_pct` | videos 141–147, **channels 0**, search 145 |
| Versioning (declared, never written) | `thumbnail_version, title_version, hook_type, topic, packaging_version, packaging_changed_at, description_version, post_change_*` | **all 0** |
| SOP status (declared, never written) | `distribution_status, traffic_mode, packaging_status, hook_status, body_status, recommended_action, notes` | **all 0** |
| Derived daily windows | `last_data_day, impressions_last_24h, ctr_last_24h, views_last_24h, impressions_previous_24h, ctr_previous_24h, views_previous_24h, impressions_last_48h, ctr_last_48h, views_last_48h, impressions_last_72h, ctr_last_72h, views_last_72h, peak_day_impressions, distribution_change_pct, current_distribution_status, mark_needed, daily_series` | 130–156 |

**Two distinct stories here, and they must not be confused:**
- Columns that are **declared but never populated** (`ret_5s/10s/20s/60s`, `*_suggesting_channel_*`,
  `episode`, `topic`, `hook_type`, `*_version`, `post_change_*`, and all SOP status fields) — these are
  **NOT_FOUND in practice**, regardless of the schema listing them.
- Columns that are populated but only by the **manual** collector, hence stale.

---

## 4. HISTORY: WHAT ACTUALLY EXISTS, DAY BY DAY

### 4.1 The only real per-day series in the CSV
`daily_series` = `{"YYYY-MM-DD": [impressions, ctr, views], …}` written by `studio_daily.summarize()`
(`studio_daily.py:181`).
- Rows with a series: **141 / 174**
- Day-points per row: **min 1, median 8, max 23**
- Videos with ≥1 series: 84 across 8 lanes (`F 17, L 17, M 11, N 10, O 9, satori 8, toshi 4, iroga 3`)
- **Series end 2026-10-16** (Studio's "2 days still processing" lag) and the file itself stops 2026-10-18.

### 4.2 The daily-0500 backups — the real (and overlooked) history
Every run first dumps the whole tab, so **`reports/daily_0500/<date>/<tab>_truoc.json` is a daily snapshot
of N/O/P/Q for every video**, independent of the CSV. Measured over all 12 days:

```
days of backups: 12   (2026-10-16 … 2026-10-27)
distinct video_ids with >=1 measured snapshot: 115
history depth distribution (days per video): {2:4, 3:12, 4:17, 6:3, 7:11, 8:9, 9:33, 10:26}
videos with >=7 days: 79      videos with >=10 days: 26
total (video,day) observations: 836
  of which Q (CTR 24H) filled: 669
  of which P (CTR total) filled: 792
```

Observations per day: 16, 61, 17, 70, 73, 37, 90, 85, 99, 104, 84, 100 (2026-10-16 → 10-27).
The early days are thin because the tab set grew (see the per-day tab lists in `08`).

**This is the single most reusable asset for YIE**: 836 (video, day) observations of
`days_listed / views / ctr_total / ctr_24h`, already on disk, no browser needed to read it.

### 4.3 Snapshot-age coverage (24h / 48h / 7d / 28d)
The task asks whether snapshots exist at fixed video ages. Measured on the CSV:

| Age bucket | Rows |
|---|---|
| ≤72 h | 41 / 170 with an age |
| 24–47 h | 20 |
| 48–71 h | 16 |
| Age range overall | 14 h … 565 h |

There is **no age-keyed snapshot design**: rows are taken whenever a human ran `studio_collect.py`. The
daily-0500 backups are **calendar-keyed**, not age-keyed, so a video published at 17:30 is sampled at
~11.5 h, ~35.5 h, ~59.5 h… — never exactly at 24/48/72 h. The SOP's "compare A@48h vs B@48h" rule therefore
has to be reconstructed by interpolation, not read off.

### 4.4 Overwrite vs append
| Store | Behaviour |
|---|---|
| Sheet N–S | **Overwritten every run** (that is the point). History survives only because of the `_truoc.json` backup and the `_RS_goc.json` first-rotation guard (`daily_0500_run.py:120-125`). |
| Sheet K | Overwritten with today's verdict; previous K text is lost except in the backup. |
| CSV | **Append-only** (`studio_collect.py:394` opens mode `"a"`), but header migration rewrites the file once (`migrate_csv_header()`, `:291-309`). |
| spike snapshots | Append + prune older than 80 h (`spike_state.py:39-47 KEEP_SNAP_HOURS`) — **deliberately destroys history beyond 80 h**. |
| `meta.json` | Append to `videos{}` cache, rewritten atomically (`_save()` uses `.tmp` + `os.replace`). |

---

## 5. IDENTITY AND JOIN KEYS

| Join | Available? | Evidence |
|---|---|---|
| `video_id` → row | **Yes**, stable 11-char id in Sheet col L / CSV `video_id` | 138 ids in Sheet, 84 in CSV, **0 duplicates across tabs** |
| `video_id` → `channel_id` | **Yes** via Data API `snippet.channelId` at run time (`daily_0500_run.py:86`) but **not stored** — the Sheet has no channel-id column, and CSV `channel` holds the id (174/174 valid `UC…`) | CSV only |
| `channel_id` → lane | **Yes**, but by convention only: `tools/daily_lanes.json` maps tab→profile; `CLAUDE.md` maps tab→mail→channel | no database, config file only |
| `video_id` → episode number | **NO.** CSV `episode` is 0/174. The only episode key is the Sheet **row position / STT** and the folder name (`ep01-…`) in col C. | verified |
| `video_id` → title | Yes (Sheet E, CSV `title`) but **titles are edited after publish**, so sheet title ≠ live title (CLAUDE.md warning) | |
| `video_id` → description | Yes (Sheet E, mixed with title) | |
| `video_id` → thumbnail | Sheet G holds a URL (`https://yourimageshare.com/...`) — a **hosted copy**, not necessarily the live thumbnail | |
| `video_id` → script | **Only indirectly** via the folder in col C. `CHANEL/<lane>/<ep>/` has subtitles/summary but **no script.txt**; `FlowHandoff_local/jobs/<lane>/<ep>/` has `script.txt` in 129/150 dirs. | see `06` |

---

## 6. THE ONE REAL DATABASE IN THE REPO (adjacent module)

`comment_care/state/comment_care.sqlite` — 11 tables, not performance data but the only normalised store:

| Table | Rows | Notable columns |
|---|---|---|
| `channels` | 5 | `channel_id, lane, channel_name, handle, sheet_tab, mode, footer_policy` |
| `videos` | 59 | `video_id, channel_id, title, published_at, comment_count, ep_dir, context_json` |
| `comments` | 330 | `comment_id, video_id, parent_id, text, like_count, is_owner, is_reply` |
| `classifications` | 50 | `primary_cat, secondary_cats, model, provider, prompt_version` |
| `decisions` | 62 | `decision, risk, policy_version, reason` |
| `drafts` | 44 | `text_body, final_text, model, judge_model, rule_qc_json, judge_json` |
| `replies` | 41 | `youtube_reply_id, status, sent_at, idempotency_key` |
| `runs` | 10 | `mode, channels_json, counts_json, quota_used` |
| `llm_calls` | 123 | `stage, provider, model, tokens_in, tokens_out, elapsed_s` |
| `review_queue` | 42 | `draft_id, decision, edited_text` |
| `reactions` | 0 | `like_status, heart_status` |

`videos.ep_dir` here **is** the `video_id → episode folder` link that the metrics side lacks. This is the
best existing model for how a YIE schema should look (`channel_id`/`video_id` as natural keys, `runs` for
provenance, `llm_calls` for cost).

---

## 7. DATA-QUALITY CHECKS PERFORMED (read-only)

| Check | Result |
|---|---|
| Duplicate `(video_id, snapshot_time)` in CSV | **0** |
| Duplicate `video_id` across Sheet tabs | **0** (138 unique) |
| `channel` column format `UC[\w-]{22}` | 174/174 valid |
| Rows where `views > impressions` | 0 |
| `publish_time` unparseable | 4/174 |
| Traffic sources sum ≠ 100 (±1 pp) | 16 of 28 fully-populated rows; 1 gross outlier at **199.5 %** (`YnuthHXJug4`, `external_pct=100.0`) |
| Literal `—` stored as a value | 0 (blanks used instead — correct) |
| Literal `0` where data is missing | 0 found |
| `episode` populated | **0/174** |
| `_truoc.json` files with malformed rows | none found; one backup had a row with 0 cells (guarded by consumers) |
| Backup completeness | 12/12 days present; tabs per day vary 7–9 (see `08`) |
| Sheet `Q` regression 2026-10-27 | **12 rows lost a previously-present Q** (F 10, L 1, N 1) — see `08` gap G3 |

---

## 8. RECORD COUNTS (the numbers the hand-over report must quote)

| Metric | Verified value | How measured |
|---|---|---|
| Channels (own, with video ids in Sheet) | **17 lane tabs exist; 12 have ≥1 video_id; 7 were processed today** | Sheets API + log |
| Distinct videos in Sheet | **138** | Sheets API scan of 17 tabs |
| Distinct videos with ≥1 daily-0500 observation | **115** | scan of 12 backup days |
| Distinct videos in CSV | **84** | CSV scan |
| Rows in CSV | **174** | CSV scan |
| (video, day) observations in backups | **836** | backup scan |
| Videos written by the 05:00 job on 2026-10-27 | **88** | log |
| Days of backup history | **12** (2026-10-16 … 2026-10-27) | directory listing |
| Date range of CSV | **2026-09-23 12:14 … 2026-10-18 06:48** | CSV scan |
