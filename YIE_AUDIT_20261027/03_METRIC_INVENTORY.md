# 03 — METRIC INVENTORY

**Method note (important):** the task says *"Tuyệt đối không đánh dấu có dữ liệu chỉ vì mã nguồn chứa tên
trường"*. Every "Đang có?" verdict below is backed by **fill counts measured in actual output files**, not
by the existence of a column name. Three separate stores are distinguished because they have very
different reliability:

| Store | What it is | Size / freshness | Written by |
|---|---|---|---|
| **SHEET** | The Google Sheet lanes (`N,O,P,Q,R,S,K`) | live, updated daily | the 05:00 job |
| **CSV** | `youtube_postpublish_metrics.csv` (70 columns) | **174 rows, 84 videos, 8 channels, last row 2026-10-18 06:48** | `tools/studio_collect.py` — **manual only, stale** |
| **SPIKE** | `view_spike/state/snapshots.jsonl` | 2 744 lines `{t,vid,views}`, last 2026-10-18 07:52 | `spike_watch.py` — task **Disabled** |

Fill counts quoted as `n/174` are over CSV rows; `n/104` over the 104 video rows in the 7 tabs the 05:00
job wrote on 2026-10-27.

---

## 1. THE MAIN TABLE

Legend — **Đang có?**: `DIRECT` = scraped and stored; `DERIVED` = computed by the code from scraped values;
`CHANNEL` = channel level only; `NO` = not collected. **Độ chi tiết**: `lifetime` / `daily` / `video` /
`channel`.

| Metric | Đang có? | Nguồn | Trường dữ liệu | Định nghĩa | Độ chi tiết |
|---|---|---|---|---|---|
| **Views** | **DIRECT** | Studio Reach tab, "Views" (`sheet_metrics_sync.py:308`) + Data API `viewCount` (`daily_0500_run.py:88`) | SHEET `O` (lifetime) · CSV `views` (163/174) | Total views | lifetime, per video; CSV also has daily via `daily_series` |
| **Impressions** | **DIRECT** | Studio Reach, "Thumbnail impressions" (`:214`, `:335`) | SHEET: only the **24h** value, stored nowhere in the Sheet (used to build `K` text) · CSV `impressions` (169/174) | Thumbnail impressions | lifetime (CSV only) + daily (CSV `daily_series`, 141/174 rows) |
| **CTR** | **DIRECT** | Studio Reach, "Thumbnail click-through rate" (`:215`, `:333`) | SHEET `P` (lifetime, 100/104) + `Q` (24h, 80/104) + `S` (previous run's 24h, 84/104) · CSV `ctr` (148/174) | impressions→views ratio | lifetime + 24h + daily (CSV) |
| **Watch time** | **DIRECT (CSV only)** | Studio, "Watch time from impressions" (`studio_collect.py:219`) | CSV `watch_time_from_impressions_hours` (**146/174**) | hours | lifetime, per video |
| **Average view duration** | **DIRECT (CSV only)** | Studio, "Average view duration" (`:198`) | CSV `avd_sec` (**127/174**) | seconds | lifetime, per video |
| **Average percentage viewed** | **DIRECT (CSV only)** | Studio, "Average percentage viewed" (`:200`) | CSV `apv_pct` (**127/174**) | % of video length | lifetime, per video |
| **Retention 30s** | **DIRECT (CSV only)** | Studio overview text `"N% of viewers are still watching at around the 0:30 mark"` (`:202-204`) | CSV `ret_30s` (**116/174**) | % still watching at 0:30 | single mark, lifetime |
| **Retention 60s** | **NO** | — | CSV `ret_60s` exists but **0/174 filled** | — | **column exists, never populated** |
| **Retention 5s / 10s / 20s** | **NO** | — | CSV `ret_5s`, `ret_10s`, `ret_20s` — **0/174 filled** | — | **column exists, never populated** |
| **Audience retention curve** | **NO** | — | — | — | not parsed anywhere (`grep retention` → only the 30s mark) |
| **Browse traffic** | **DIRECT (CSV only)** | Studio Reach, "Browse features" (`:220`) | CSV `browse_pct` (**146/174**) | % of views | lifetime, per video |
| **Suggested traffic** | **DIRECT (CSV only)** | Studio Reach, "Suggested videos" (`:221`) + "…% from YouTube recommending your content" (`:226`) | CSV `suggested_pct` (145/174), `recommendation_pct` (139/174) | % of views | lifetime |
| **Search traffic** | **DIRECT (CSV only)** | Studio Reach, "YouTube search" (`:222`) | CSV `search_pct` (140/174) | % of views | lifetime |
| **Direct / External traffic** | **DIRECT (CSV only)** | Studio Reach, "Direct or unknown" / "External sites or apps" (`:223-224`) | CSV `direct_pct` (92/174), `external_pct` (**41/174**) | % of views | lifetime |
| **Subscribers gained** | **NO** | — | — | — | no Audience/Engagement tab code at all |
| **Revenue / RPM** | **NO** | — | — | — | no Revenue tab code (`grep -rniE "revenue\|rpm\|cpm"` → 0 relevant) |

### Additional real metrics not in the task's list

| Metric | Đang có? | Nguồn | Trường | Ghi chú |
|---|---|---|---|---|
| Unique viewers | DIRECT (CSV) | Studio Reach (`:217`) | CSV `unique_viewers` (131/174) | lifetime |
| Engaged views from impressions | DIRECT (CSV) | `:218` | CSV `engaged_views_from_impressions` (147/174) | lifetime |
| Video length | DIRECT | Studio overview `0:00 / mm:ss` (`:191`) | CSV `video_length_sec` (**174/174**) | needed to read AVD/APV correctly |
| Publish date | DIRECT | Studio overview range header (`:181`) **and** Data API `publishedAt` (`daily_0500_run.py:86`) | CSV `publish_time` (170/174) | `hours_since_publish` is computed from **00:00 of the publish day**, so it can overshoot by up to 17.5 h (CLAUDE.md) — the daily job instead uses the API's exact `publishedAt` (`daily_0500_run.py:158-159`) |
| Video age (hours) | DERIVED | `now − publishedAt` | CSV `hours_since_publish` (170/174); Sheet `N` = `int(hours//24)` | |
| 24h / previous-24h / 48h / 72h impressions, CTR, views | DERIVED | `studio_daily._window()` sums the daily table (`studio_daily.py:82-88`) | CSV `impressions_last_24h` etc. (141/174) | **CSV only** — the 05:00 job does not compute these |
| Daily series `{date: [impressions, ctr, views]}` | DIRECT | Studio Advanced mode table (`studio_daily.py:48-64`) | CSV `daily_series` (**141/174 rows**, 1–23 day-points, median 8) | the only true daily history in the CSV |
| Distribution status (`NOT_TESTED`/`EARLY_TEST`/`NEAR_DEAD`/`EXPANDING`/…) | DERIVED | `studio_daily.status()` (`:91-107`) | CSV `current_distribution_status` (156/174) | rule engine |
| Peak day impressions | DERIVED | max of daily series | CSV `peak_day_impressions` (141/174) | |
| Distribution change % | DERIVED | 48h window vs peak | CSV `distribution_change_pct` (130/174) | |
| Mark decision | DERIVED | `daily_k_rules.k_note()` | CSV `mark_needed` (141/174) · SHEET `K` + yellow fill | see `08` for a rule contradiction |
| Top suggesting **video** (title) | DIRECT | Studio "Content suggesting this video" (`:232-244`) | CSV `top_suggesting_video_1` (147/174), `_2` (141/174) | titles only |
| Top suggesting **channel** | **NO** | — | CSV `top_suggesting_channel_1/2` exist, **0/174 filled** | the SOP requires this when suggested ≥40% — it is never collected |
| Top search term + its % | DIRECT | Studio "YouTube search terms" (`:250-272`) | CSV `top_search_term_1` (145/174), `search_term_1_pct` (145/174) | 1 term only |
| Public view count (API) | DIRECT | Data API `videos.list` | `view_spike/state/snapshots.jsonl` (2 744 pts) + `api_meta()` | used for spike detection; **~26% lower than Studio** (CLAUDE.md, measured twice) |
| Views/hour (API tier) | DERIVED | `spike_state.rate_per_hour()` | `view_spike/state/status.json` | only for videos ≤72 h |
| Realtime views (Studio chart) | DIRECT | `spike_studio_realtime.py` hover over `yta-realtime-chart` | in-memory → `alerts.jsonl` (4 lines total) | **task Disabled**, not running |
| Competitor channel subscriber count | DIRECT | `viral_hunt/ytweb.py` regex on `登録者…人` | `reports/viral_hunt/` | **own channels: NO** |

---

## 2. WHAT THE 05:00 JOB ACTUALLY STORES (the only daily-updated store)

`read_video_full()` returns exactly six fields (`sheet_metrics_sync.py:339-340`):
`{days, views, ctr_total, ctr_24h, imp_24h, ok}`.

Of those, **five reach the Sheet**: `N` (days), `O` (views), `P` (ctr_total), `Q` (ctr_24h),
plus `R`/`S` rotation; and `imp_24h` is used only to write prose into `K`
(`daily_0500_run.py:163-166`). Everything else in the Sheet is human-authored.

Measured fill on 2026-10-27 across the 104 video rows in the 7 processed tabs:

| Column | Fill | Meaning |
|---|---|---|
| N — SỐ NGÀY LIST | 103/104 | days since publish |
| O — VIEW | 103/104 | lifetime views |
| P — CTR TỔNG | 100/104 | lifetime CTR |
| Q — CTR 24H | **80/104** | 24h CTR — **blank on 24 rows** (see `08`, gap G3) |
| R — VIEW CŨ | 100/104 | previous run's O |
| S — CTR 24H CŨ | 84/104 | previous run's Q |
| K — GHI CHÚ | 104/104 | prose verdict |
| T — VIDEO GỐC | 80/104 | human-authored (original video link) |
| U — ĐỀ XUẤT | 58/104 | **stale**: contains old K-style notes from earlier runs (e.g. `F` row2 U = `518h · 2.900 view · …` while K = today's verdict) |
| V, W, X, Y, Z | 1, 1, 0, 0, 0 | effectively unused (`V` header `Thumbnail impressions 24h` exists in F only, 1 filled) |

**Conclusion: the daily system's entire machine-readable payload is 4 numbers + 1 derived string per video
per day.** That is enough for a CTR-trend alert; it is not enough for the YIE vision (retention, traffic
mix, watch time) without adding collection.

---

## 3. LEVEL COVERAGE

| Level | Available metrics |
|---|---|
| **Video, lifetime** | views, impressions, CTR, watch time¹, AVD¹, APV¹, retention@30s¹, 5 traffic sources¹, unique viewers¹, engaged views¹, video length, publish date |
| **Video, daily** | impressions, CTR, views (`daily_series`, CSV only¹) |
| **Video, 24h windows** | impressions/CTR/views for last-24h, previous-24h, last-48h, last-72h (CSV only¹) + `Q` in Sheet |
| **Channel** | **NOTHING for own channels.** Only competitor channel subscriber counts via `viral_hunt` scrape |
| **Lane** | derived externally by grouping videos (no stored lane-level aggregate; `TONGHOP` tab holds human status text, not metrics) |

¹ = CSV path only, i.e. **stale since 2026-10-18 and only 8 of the lanes**. These metrics are *reachable*
from the same Studio pages the daily job already opens — `studio_collect.collect_video()` proves it parses
them — but the daily job does not call that function.

---

## 4. DATA-QUALITY FINDINGS ON THE METRIC VALUES

Measured on the CSV (`py -3.13` scan of all 174 rows):

| Check | Result |
|---|---|
| Duplicate `(video_id, snapshot_time)` | 0 — clean |
| Duplicate `(video_id, age bucket)` | 5 pairs — same video snapshotted twice at a similar age |
| `channel` column holds a real `UC…` id | 174/174 valid format |
| `episode` column | **0/174 filled** — there is no episode number in the CSV at all |
| Number formatting | **inconsistent across the two writers**: CSV uses dot decimals (`"3900.0"`, `"6.3"`); the Sheet uses Vietnamese comma decimals (`"6,30%"`). Any consumer that parses both must branch per source. |
| Traffic-source percentages sum | of 28 rows with all five sources, **16 are off 100 % by >1 pp**; all are under-sum (97.3–98.8 %) except **one outlier: `YnuthHXJug4` 2026-10-18 has `external_pct = 100.0`** while browse = 94.4 → sum **199.5 %** |
| `—` vs `0` convention | CSV stores **blank** for `—` (no literal `—` cells, no literal-zero cells found), so "no data" and "zero" are distinguishable — good — but only if consumers treat blank as *unknown*, never as 0 |
| `views > impressions` | 0 rows (sanity holds) |
| `publish_time` parseable `Mon D, YYYY` | 170/174 (4 blanks) |

### The one confirmed *corruption* pattern: `external_pct`
`studio_collect.py:224` reads `External sites or apps` with `pct_after(...)`. In the outlier row the parser
attached the **total-traffic proportion** ("Proportion of your total traffic: 100.0%") to the external
bucket. The code already documents two sibling versions of this exact bug (suggesting-video and search-term
blocks, `:232-236`, `:250-258`) — `external_pct` was never given the same guard.

---

## 5. VERDICT FOR YIE

| YIE requirement | Status today |
|---|---|
| Daily performance history | **PARTIAL** — real daily impressions/CTR/views exist only in the CSV `daily_series` (141 rows, stale) and in the per-day Sheet backups (`04`); the live daily job stores only lifetime + one 24h CTR |
| CTR / impressions history | **PARTIAL** — see above |
| Retention history | **NO** — one 30 s mark at lifetime, CSV only, stale |
| Watch time | **CSV only, stale** |
| Cross-episode comparison within a lane | **PARTIAL** — possible (video_id + lane exist), but no episode number and no lane aggregate |
| Anomaly detection | **PARTIAL** — `view_spike` computes views/hour but its task is Disabled |
| Topic/hook/title/thumbnail recommendation inputs | **NO** — `topic`, `hook_type`, `title_version`, `thumbnail_version` are **0/174** in the CSV |
| Dashboard | **NO** |
