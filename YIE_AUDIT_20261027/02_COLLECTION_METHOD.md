# 02 — COLLECTION METHOD (how YouTube data is actually obtained)

Audit only. No API calls to YouTube were made and no browser/Studio page was opened during this audit.
Everything below is read from source, logs and existing output files.

---

## 1. ANSWER IN ONE LINE

Data is collected by **driving a real, visible Chrome window (GPMLogin / AdsPower / a dedicated
Chrome-9222 profile) through Playwright's CDP connection, clicking through YouTube Studio like a human**.
The YouTube Analytics API is **not** used at all. The YouTube Data API is used only for three cheap
metadata fields.

---

## 2. METHOD BY SOURCE

| Source | Used? | Where | What it yields |
|---|---|---|---|
| **YouTube Studio UI via Chrome CDP + Playwright** | **YES — primary** | `tools/sheet_metrics_sync.py:249 read_video_full()`, `tools/studio_human.py`, `tools/studio_collect.py:163 collect_video()` | impressions, CTR, views, watch time, AVD, APV, traffic sources, search terms, suggesting videos, retention@30s |
| **YouTube Analytics API** (`youtubeanalytics.googleapis.com`) | **NO** | `grep -rn "youtubeAnalytics\|yt-analytics\|analytics/v2\|reports.query"` over all `*.py` → **0 matches** | — |
| **YouTube Data API v3** (`videos.list`) | YES — metadata only | `view_spike/spike_sources.py:55 _get()`; called by `tools/daily_0500_run.py:83 api_meta()` | `publishedAt`, `channelId`, `channelTitle`, `viewCount` (public) |
| **YouTube web scraping** (no API key) | YES — separate module only | `viral_hunt/ytweb.py`, `viral_hunt/run_daily.py` | search results, channel subscriber counts, like/comment counts |
| **Google Sheets API** | YES | `tools/daily_sheet.py:16 svc()`, `view_spike/spike_sources.py:38` | reads video ids + current cell values; writes N–S/K |

### Why Studio and not the Analytics API
`CLAUDE.md` (Data section) states impressions/CTR are **not** available in the public YouTube Analytics API,
which matches Google's documented behaviour. The code confirms the consequence: every impression/CTR
number in this system comes from a DOM scrape of Studio.

---

## 3. BROWSER: HEADED, AND IT TAKES OVER THE SCREEN

| Question | Answer | Evidence |
|---|---|---|
| Headless? | **No.** Zero matches for `headless` in `tools/`, `view_spike/` | `grep -rn "headless"` → no output |
| Visible window? | **Yes**, and it is explicitly maximized | `studio_human.py:107 maximize()` → `Browser.setWindowBounds ... windowState: maximized`; called at `daily_0500_run.py:228,251` |
| Does it take over mouse/keyboard? | **Effectively yes.** The task runs in the **interactive** user session (`-LogonType Interactive`, `create_task_0500.ps1:37`) and the child calls `page.bring_to_front()` (`daily_0500_run.py:227,250`), then clicks by moving the real cursor (`studio_human.py:85-92 _click_xy()` → `page.mouse.move(...)` + `page.mouse.click(...)`). | as cited |
| Does it disturb the user? | **Yes, for 90–111 minutes from 05:00**, opening up to 3 Chrome windows in rotation, each brought to front. Measured duration: 95 min on 2026-10-27. | log tail `===== XONG DA LUONG: 95 phut` |
| Mitigation in code | Only *timing* randomization (`human_pace.py`) — pauses between videos 20–55 s, long break every 12 videos, extra backoff after a Studio error. It does **not** make the browser invisible or non-interfering. | `daily_0500_run.py:134-137`, `human_pace.py:67-77` |

**This is the single biggest constraint for YIE**: any YIE component that wants to read Studio must
share this same mouse-stealing, screen-occupying mechanism, or must not read Studio at all.

---

## 4. PROFILE / IDENTITY HANDLING

| Engine | Used for | How opened | Evidence |
|---|---|---|---|
| **GPMLogin** (`http://127.0.0.1:9495/api/v1`) | 10 of 11 groups | `_gpm_find(mail)` matches profile name against full mail **and** the part before `@`; `_gpm_start()` | `daily_profiles.py:48-112` |
| **AdsPower** (`http://127.0.0.1:50325`) | 1 group (`Lane-N`, `user_id k15wbjoo`) | `_ads_start()` | `daily_profiles.py:128-138`; `daily_lanes.json:12` |
| **Dedicated Chrome, fixed CDP port 9222** | lanes `A-shinya_shiryoshitsu` + `M-teinengo-anaba` | `_open_9222()` with `--user-data-dir E:\CLAUDE\YOUTUBE\HAOVIABATTU_PROFILE` | `daily_profiles.py:139-154`; `daily_lanes.json:4` |

**Shared-profile risk (real):** the 9222 Chrome profile is the same one the upload project `AUTO_LIST`
uses. `daily_profiles.py:9-10` documents that if it is already open the tool only attaches and does not
close it, precisely because an upload may be in progress. So the 05:00 job **does** read a browser profile
that serves other work — it just refuses to kill it.

Multi-channel identities: `K-yakkyoku-sukatto` + `Lane-O` share one mail profile, and `sengoku-uragawa` +
`Lane-J` share another — `daily_lanes.json:8,11`. Channel switching is done in the UI by
`switch_channel()` (`studio_human.py:320`) and re-verified by `verify_channel()` (`:252`).

---

## 5. HOW MANY CHANNELS / VIDEOS PER RUN

Measured 2026-10-27:

| Measure | Value | Evidence |
|---|---|---|
| Lane groups in config | 11 | `tools/daily_lanes.json` |
| Sheet tabs actually processed | **7** (of 14 configured) | log: `A-shinya_shiryoshitsu, F-teinengo-real, L-shakai-no-naze, Lane-N, Lane-O, Lane-P, M-teinengo-anaba` |
| Videos read and written | **88** | `grep -c "DA GHI SHEET" reports/daily_0500/2026-10-27.log` |
| Videos attempted | 100 (rows carrying N+O in that day's pre-write backups) | pre-write JSON scan |
| Tabs configured but skipped | `E-70dai-kenko`, `G`, `K-yakkyoku-sukatto`, `kokoro-kazoku`, `sengoku-uragawa`, `Lane-J`, `Lane-Q` | log: `LOI lane` / `KHONG chuyen duoc sang kenh` / `ProfileUsingByOther` |

Per-lane writes on 2026-10-27: F 20, Lane-O 16, Lane-N 16, M 15, L 9, Lane-P 7, A 5.

Historical range: 81 (10-26) … 107 (10-24) writes per day.

---

## 6. PAGINATION, RETRY, ERROR DETECTION

| Concern | Implemented? | Evidence |
|---|---|---|
| Pagination of the video list | **No.** Reads only the first screen of `ytcp-video-row` elements, up to 20 polls × 3 s, then `rows[:limit]` | `studio_collect.py:276-289 list_videos()` |
| Pagination of per-video tables | N/A (single-page DOM scrape) | — |
| Retry per video | **Yes, 2 attempts**, with `after_oops()` backoff | `daily_0500_run.py:139-151` |
| Retry per lane | Implicit only via the 3-strike breaker; **no retry of a failed lane** | `daily_0500_run.py:130-133` |
| Retry of profile open | **Yes, 4 tries**; on `ProfileUsingByOther` at 05:00 it stops+restarts the profile | `daily_profiles.py:83-112` |
| Missing-data detection | **Partial.** Studio's `—` becomes `None` → the cell is left **empty**, never `0` | `sheet_metrics_sync.py:187-198 num()`, `213 vn_pct()` |
| "Not enough traffic data" detection | **Yes**, with two hard-won guards against reading the *next* section's numbers | `studio_collect.py:232-236`, `:250-258` (comments record the actual mis-reads: "Area 51", lane M ep01/ep07/ep14) |
| Oops-page detection | **Yes.** `_oops(parts)`; re-clicks Reach after a long pause | `sheet_metrics_sync.py:232-247`, `:289-294` |
| Stale-day detection | **Yes.** `report_end_day()` uses the range header, not the last row present, because Studio drops 0-impression days | `studio_daily.py:70-79` |
| Silent-wrong-number detection | **Weak.** The only guard is a 24 s comparison of two snapshots (`_reach_snapshot`) | `sheet_metrics_sync.py:316-330` |

Measured failures on 2026-10-27 (from the log):
- 7 lanes lost to `Navigation to "https://studio.youtube.com/" is interrupted by another navigation to "https://www.youtube.com/"` — a navigation race, not a Studio error.
- 3 videos dropped with `khong doc duoc trang Reach 24h -> bo qua`.
- 1 profile lost to `GPM khong mo duoc profile sau 4 lan: ProfileUsingByOther`.
- 1 channel switch failure: `KHONG chuyen duoc sang kenh UC…` (id withheld).

---

## 7. CAN DATA BE OBTAINED WITHOUT OPENING EACH VIDEO PAGE?

**No, not with the current method — and this is a hard architectural fact.**

The daily job *deliberately* navigates to each video individually. Two documented reasons:

1. Direct URL navigation to a video's analytics page triggers a blanket `Oops, something went wrong`
   from Studio. `sheet_metrics_sync.py:252-255`:
   > *"CAM goto URL video… Ly do: goto URL tung video lam Studio tra 'Oops, something went wrong' hang
   > loat (lane A 19-20/10: 5 video lien tiep, 457s/video, 0 so doc duoc)."*
2. Even the Reach tab must be reached by **clicking the word "Reach"**, because `/analytics/tab-reach/...`
   is permanently broken (CLAUDE.md trap #2; `studio_human.py:354 click_tab()`).

A partial exception exists: `studio_daily.collect_daily()` reads the **Advanced-mode daily table**, which
returns a whole time series for one video in one page load. That is still one page per video, but it is
**1 page instead of 3** (overview + Reach + date-range dance). The 05:00 job does **not** use it
(`grep studio_daily tools/daily_0500_run.py` → no match); only the manual `studio_collect.py` does.

**Cost per video, measured:** ~35–140 s in the 05:00 run (e.g. 05:39:49 → 05:42:00 → 05:44:10 → 05:46:35
for four consecutive F videos ≈ 140 s each including pauses; the fastest lane averaged ~13 min for 7
videos). `human_pace.py:7-9` records an earlier measurement of median 13.5 s/video when pacing was off,
which caused Studio to return `Oops` — i.e. **the slow pace is a functional requirement, not politeness.**

---

## 8. QUOTA AND RATE LIMITS — WHAT IS ACTUALLY CONFIRMED

| Limit | Confirmed? | Evidence |
|---|---|---|
| Data API: 1 unit per `videos.list`, ≤50 ids per call | **Yes, by code design** | `spike_sources.py:12-17` docstring; `_get()` batches by 50 (`:55-63`) |
| Data API: project exhausted 10 000 units/day, HTTP 403 `exceeded your quota` | **Yes — observed** | `viral_hunt/run_daily.py:4-5`: *"project đã cạn 10.000 unit/ngày (HTTP 403 `exceeded your quota`)"* → that module was rewritten to scrape the web instead |
| Data API usage of the 05:00 job | Small: 1 call per tab with ≤50 ids (7 tabs → ≤7 units/run) | `daily_0500_run.py:83-92` |
| Studio: undocumented rate limiting | **Yes, observed as `Oops` storms** | `human_pace.py:7-9` (5 consecutive videos, 457 s each, 0 numbers) |
| Studio: any documented quota | **NOT_VERIFIED** — no documented number; behaviour is empirical only | — |
| Sheets API quota | Not measured; no errors found in logs | — |

---

## 9. WHAT THE COLLECTOR CANNOT SEE (by construction)

- **Revenue / RPM / CPM** — no Revenue tab interaction anywhere (`grep -rniE "revenue|rpm|cpm"` → only one
  unrelated hit in a probe script's label list). Monetisation data is **NOT_FOUND**.
- **Audience tab / subscriber gain-loss** — no `Audience`/`Engagement` tab code exists
  (`grep -n "Audience\|audience\|Engagement"` over `tools/` and `view_spike/` → 0 matches).
- **Retention curve** — only a single 30 s mark is parsed (`studio_collect.py:202-204`).
- **Per-video data older than the tab window** — the daily job never asks for a date range other than
  "yesterday", so it cannot backfill history.

See `03_METRIC_INVENTORY.md` for the field-by-field verdict.
