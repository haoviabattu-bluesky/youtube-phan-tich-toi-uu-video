# YIE_SAMPLE_SCHEMA.md — schema of `YIE_SAMPLE_DATA.json`

This file describes the sample export. **The sample is real data with pseudonymised identifiers** — not
synthetic data. Read §6 for exactly what was removed and why.

---

## 1. PROVENANCE

| Item | Value |
|---|---|
| Generated | 2026-10-27, during this audit |
| Sources | `youtube_postpublish_metrics.csv` (174 rows) and `reports/daily_0500/<date>/<tab>_truoc.json` (12 days) |
| Selection | 3 channels × 5 videos; all available days per video, capped at **14** |
| Row counts | `channels` 3 · `videos` 15 · `video_daily` 203 · `sheet_daily_snapshot` 145 |
| Date ranges | `video_daily` 2026-10-03 … 2026-10-16 · `sheet_daily_snapshot` 2026-10-16 … 2026-10-27 |
| Real underlying corpus | 138 videos in the Sheet, 84 in the CSV, 115 with daily observations, 836 (video, day) observations |

---

## 2. THE FIVE TABLES

```
channels (3)
   channel_id  CH_01..CH_03   ← pseudonym, stable across all tables
   lane        real lane key  (kept: it is a series name, not an account)

videos (15)                    ← one row per video, "latest known" lifetime snapshot
   video_id            VID_001..VID_015   ← pseudonym, stable
   channel_id          FK → channels
   title_redacted      always true (titles identify the channel)
   publish_month       "Sep 25"  (month+day only; year dropped)
   video_length_sec    float
   snapshot_time       "2026-10-18 06:41" — when the lifetime row was captured
   hours_since_publish float  (age at snapshot_time)
   lifetime{...}       lifetime metrics block (see §3)
   traffic_sources_lifetime_pct{...}   five sources + recommendation share
   top_suggesting_video_1_present  bool  ← presence flag only; the title itself is withheld
   top_search_term_1_present       bool
   search_term_1_pct               float ← share of traffic from the top search term
   mark_needed                     enum  ← the rule verdict: BO_QUA_1000 | NO | THUMB | TITLE+THUMB
   current_distribution_status     enum  ← NOT_TESTED | EARLY_TEST | NEAR_DEAD | EXPANDING | STABLE …

video_daily (203)              ← the ONLY real per-day series in the source (Studio advanced table)
   video_id, channel_id, day (YYYY-MM-DD)
   impressions  int
   ctr_pct      float
   views        int
   source       "studio_advanced_table"

sheet_daily_snapshot (145)     ← what the 05:00 job recorded, one row per video per day
   video_id, channel_id, day
   days_listed       float  (Sheet col N)
   views_lifetime    float  (col O)
   ctr_total_pct     float  (col P)
   ctr_24h_pct       float | null (col Q)
   source            "daily_0500_truoc_json"
```

`video_daily` and `sheet_daily_snapshot` are **deliberately two tables, not one**: they come from two
different collectors, have different windows, and do not agree (`03` §4, `08` R3/R5). Merging them would hide
exactly the inconsistency YIE must handle.

---

## 3. THE `lifetime` BLOCK

| Field | Unit | Source column | Notes |
|---|---|---|---|
| `impressions` | count | `impressions` | thumbnail impressions |
| `ctr_pct` | percent 0–100 | `ctr` | |
| `views` | count | `views` | |
| `unique_viewers` | count | `unique_viewers` | |
| `engaged_views_from_impressions` | count | `engaged_views_from_impressions` | |
| `watch_time_from_impressions_hours` | hours | `watch_time_from_impressions_hours` | |
| `avd_sec` | seconds | `avd_sec` | **meaningless without `video_length_sec`** — SOP rule |
| `apv_pct` | percent | `apv_pct` | |
| `retention_30s_pct` | percent | `ret_30s` | the **only** retention mark collected |

---

## 4. TYPE AND UNIT CONVENTIONS

| Convention | Value |
|---|---|
| `null` | Studio reported **no value** (`—`: not enough data). **It is NOT zero.** 32 of the 145 `ctr_24h_pct` values are null — that is real, and it is the single most important convention for a consumer. |
| `ctr_pct` / `apv_pct` / `retention_30s_pct` | percent, 0–100 (not a fraction) |
| `avd_sec` | seconds, integer |
| `watch_time_*_hours` | hours, float |
| `days_listed` | float, but always integral (days since publish) |
| ids | strings, stable across tables; `CH_xx` / `VID_xxx` |
| dates | `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM` (local, UTC+7) |

---

## 5. HOW THE TWO NUMBER FORMATS WERE RECONCILED

The sources disagree and this is a real trap (`08` S1):

| Source | Raw | Parsed |
|---|---|---|
| CSV | `"3900.0"`, `"6.3"` | dot decimal |
| CSV | `"5:27"` (`avd_sec`) | → 327 s |
| Sheet JSON | `"6,30%"` | comma decimal + `%` → `6.3` |
| Sheet JSON | `"2.900"` (views) | dot as **thousands** separator → `2900` |
| Sheet JSON | `"—"` | → `null` |

A single naive parser converts `6,30%` to `630` and `2.900` to `2.9`. The generator uses **two separate
parsers**, one per source. Any YIE ingest must do the same.

---

## 6. WHAT WAS REMOVED (and what was kept)

| Removed | Why |
|---|---|
| Titles, descriptions, tags | they identify the channel and the niche |
| Channel names, `@handles`, `channel_id` values | replaced by `CH_01..03` |
| All email addresses and the tab↔mail mapping | login identity |
| All filesystem paths (Sheet col C, script paths, thumbnail paths) | local paths |
| Cookies, tokens, keys, session data | **never read at all** — no credential file was opened for values |
| Suggesting-video and search-term **text** | kept only as `*_present: true/false` + the numeric share |
| Absolute dates of publish (year) | `publish_month` keeps "Sep 25" only |

| Kept | Why |
|---|---|
| All metric **names, types, units** | required by the task: schema fidelity |
| Numeric values, unrounded | so the sample can be used to test parsers and charts |
| `lane` strings | they are series names, not accounts |
| Pseudonymised ids | so the three tables can be joined exactly as in production |
| The `null` pattern | it is the most important semantic in the dataset |

---

## 7. HOW TO VALIDATE A CONSUMER AGAINST THIS SAMPLE

1. `videos` ⋈ `video_daily` on `video_id` → 15 videos, 203 rows, 14 days max per video.
2. `videos` ⋈ `sheet_daily_snapshot` on `video_id` → 145 rows; `ctr_24h_pct` null on 32.
3. `videos` ⋈ `channels` on `channel_id` → exactly 5 videos per channel.
4. For any video, `sheet_daily_snapshot.views_lifetime` should be **non-decreasing** over `day` — but in the
   real data it is **not** for 5 of the 15 sampled videos (`VID_003` 3400→3351, `VID_006` 2904→2900, and 3
   others). Studio's lifetime view counter occasionally revises **downward**. A consumer must tolerate that
   and must never assume monotonicity when computing deltas.
5. `video_daily` and `sheet_daily_snapshot` must **not** be treated as the same series — their date ranges do
   not overlap by design (2026-10-03…16 vs 2026-10-16…27) and their `ctr` definitions differ.

If a consumer passes those five checks, its parsing/joining matches this audit's.
