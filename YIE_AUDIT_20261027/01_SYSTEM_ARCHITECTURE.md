# 01 — SYSTEM ARCHITECTURE

Audit date: 2026-10-27 · Audit only, no code/config/scheduler changes made.

---

## 0. CORRECTION TO THE PREMISE (read first)

The task describes "the system that auto-runs at **00:00**". **No such job exists.**

| Claim | Reality | Evidence |
|---|---|---|
| Runs at 00:00 | Runs at **05:00 daily** | `schtasks /query /tn DailyMetrics0500 /fo LIST /v` → `Start Time: 5:00:00 AM`, `Schedule Type: Daily`, `Task To Run: pythonw.exe "...\tools\daily_parallel.py" --scheduled --workers 3` |
| — | Task name is `DailyMetrics0500`, created by `tools/create_task_0500.ps1` line 22 (`New-ScheduledTaskTrigger -Daily -At '05:00'`) | `tools/create_task_0500.ps1:22` |
| — | No scheduled task at 00:00 anywhere on the box | `schtasks /query /fo TABLE` → only `DailyMetrics0500` at 05:00, plus `H2devHenGioTap` (every minute), `RedbubblePipelineDaily` 18:00, and 3 **Disabled** tasks (`ViewSpikeWatch`, `ViralHunt0300`, `LaneFeed0100`) |

**Consequence for YIE:** any integration plan keyed to "the 00:00 run" must be re-keyed to 05:00, and
must tolerate the run finishing anywhere between ~90 and ~111 minutes after start (measured below).

---

## 1. PROJECT ROOT AND LANGUAGE

| Item | Value | Evidence |
|---|---|---|
| Root | `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO` | directory listing; `README.md:1-3` |
| Language | Python **3.13** (invoked as `py -3.13` / `pythonw.exe` from `C:\Users\xxx\AppData\Local\Programs\Python\Python313\`) | `tools/create_task_0500.ps1:7` |
| VCS | git, branch `main` | `git status` |
| Test suite | **none** | no `pytest.ini`/`tests/` for the analytics tools; only `comment_care/tests/` exists (unrelated module) |

Note: the daily pipeline files are **untracked in git** (206 untracked entries; `tools/daily_0500_run.py`,
`tools/daily_parallel.py`, `tools/studio_human.py`, `tools/studio_daily.py`, `view_spike/`, `niche_watch/`
are all `??`). Only `tools/studio_collect.py` and `tools/sheet_metrics_sync.py` are tracked, and both
have uncommitted modifications. This matters for YIE: **the running code has no version history.**

---

## 2. ENTRYPOINT AND MODULE MAP

Entrypoint (scheduler → parent → children):

```
pythonw.exe tools\daily_parallel.py --scheduled --workers 3      ← Task Scheduler DailyMetrics0500
   └─ (per profile group, in a thread) opens GPM/AdsPower/Chrome-9222 profile
        └─ subprocess: python.exe tools\daily_0500_run.py --no-lock --attach <ws> --tab <tabs>
              └─ per tab: do_tab() → per video: sheet_metrics_sync.read_video_full()
```

| File | LOC | Role | Key functions |
|---|---|---|---|
| `tools/daily_parallel.py` | 153 | Parent: opens N profiles concurrently, hands CDP ws to children, closes profiles | `main()`, `take_lock()`, `run_bucket()` (L111), `child_cmd()` (L63) |
| `tools/daily_0500_run.py` | 276 | Child: per-lane orchestration, rotate O→R/Q→S, write N–Q + K, paint row | `do_tab()` (L101), `main()` (L196), `api_meta()` (L83), `lock_take()` (L58) |
| `tools/sheet_metrics_sync.py` | 422 | Studio reader (Playwright) + Sheet writer for the 4 columns | `read_video_full()` (L249), `read_video()` (L249 sibling), `vn_pct()` (L213) |
| `tools/studio_human.py` | 512 | "Human path" DOM driver: click video row, click tabs, set date range, switch channel | `click_video()` (L206), `click_tab()` (L354), `set_day_range()` (L387), `set_latest_day()` (L460), `switch_channel()` (L320), `verify_channel()` (L252) |
| `tools/studio_daily.py` | 183 | Parses Studio's **Advanced-mode daily table** → `daily_series` + 24h/48h/72h windows | `collect_daily()` (L108), `parse_table()` (L48), `report_end_day()` (L70), `summarize()` (L149), `status()` (L91) |
| `tools/studio_collect.py` | 408 | **Separate, manual** full-metric collector → CSV (not used by 05:00) | `collect_video()` (L163), `list_videos()` (L276), `main()` (L312) |
| `tools/daily_sheet.py` | 110 | Google Sheets read/backup/write + yellow fill + TONGHOP summary tab | `read_tab()` (L26), `write()` (L45), `tonghop()` (L73) |
| `tools/daily_k_rules.py` | 37 | Column-K text + yellow decision | `k_note()` (L21), `THRESHOLD = 2.5` (L10) |
| `tools/daily_profiles.py` | 183 | GPM/AdsPower/Chrome-9222 profile lifecycle, `ProfileUsingByOther` recovery | `open_group()` (L155), `_gpm_start()` (L83), `_open_9222()` (L139) |
| `tools/daily_lanes.json` | 16 | **Routing table**: 11 groups → 14 tabs | `groups[]` |
| `tools/human_pace.py` | 93 | Randomized human-timing pauses | `pause()` (L43), `between_videos()` (L67), `after_oops()` (L75) |
| `view_spike/spike_sources.py` | 124 | Data API tier-1 source (viewCount) | `_get()` (L55), `sheet_video_ids()` (L38), `refresh_meta()` (L80) |
| `view_spike/spike_state.py` | 99 | Shared `run.lock`, snapshots, alert cooldown | `acquire_lock()` (L82), `release_lock()` (L95) |

---

## 3. ACTIVATION AND ORCHESTRATION

### 3.1 Trigger
`schtasks /query /tn DailyMetrics0500 /fo LIST /v` (measured 2026-10-27):
```
Task To Run : C:\Users\xxx\...\pythonw.exe "E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\daily_parallel.py" --scheduled --workers 3
Start In    : E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO
Schedule    : Daily, Start Time 5:00:00 AM
Last Run    : 10/27/2026 5:00:01 AM     Last Result: 0
Next Run    : 10/28/2026 5:00:00 AM     Status: Ready
```
Task settings from `tools/create_task_0500.ps1:26-34`: `StartWhenAvailable`, `ExecutionTimeLimit 2h`,
`MultipleInstances IgnoreNew`, `RestartCount 2` / `RestartInterval 15min`, `LogonType Interactive`.
Interactive is required because Chrome/GPM windows must exist.

### 3.2 Concurrency model
`daily_parallel.py:93-98` — workers = `min(--workers, len(groups))` = **3**; groups are bin-packed by tab
count (`sorted(..., key=lambda x: -len(x["tabs"]))`, L96). Each worker is a thread that walks its bucket
**sequentially** (open profile → run child → close profile → next).

Measured 2026-10-27 run (`reports/daily_0500/2026-10-27.log`):
```
05:00:03 ===== DA LUONG 3 profile cung luc | 11 nhom | tat ca tab =====
05:00:03   luong 1: ['cdp9222', '<PROFILE_1>', '<PROFILE_2>', '<PROFILE_3>']
05:00:03   luong 2: ['<PROFILE_4>', '<PROFILE_5>', '<PROFILE_6>', '<PROFILE_7>']
05:00:03   luong 3: ['<PROFILE_8>', '<PROFILE_9>', '<PROFILE_10>']
...
06:35:18 ===== XONG DA LUONG: 95 phut (3 profile cung luc)
```
So: **3 lanes in parallel, 11 lane-groups, 88 video reads, 95 minutes** on 2026-10-27. Previous days:
99 writes (10-23), 107 (10-24), 104 (10-25), 81 (10-26) — same 90–111 min envelope
(`grep -c "DA GHI SHEET" reports/daily_0500/<day>.log`).

### 3.3 Lock / queue / retry
| Mechanism | Where | Behaviour |
|---|---|---|
| Global lock | `view_spike/state/run.lock`, `spike_state.acquire_lock()` | Parent takes it before work (L104), child skips taking it via `--no-lock` (L106-107). Stale-PID detection: `take_lock()` L49-52 removes the lock if the recorded PID is dead. Waits up to **15 min** then aborts. |
| Lock heartbeat | `daily_0500_run.py:79 lock_touch()` | Called per video (L128) so a long run is not declared dead. |
| No job queue | — | Work list = live Sheet rows, re-read per tab (`daily_sheet.read_tab`). There is **no persisted queue**; a crashed run is re-run from scratch tomorrow. |
| Per-video retry | `daily_0500_run.py:139-151` | 2 attempts, with `hp.after_oops()` backoff between. |
| Lane circuit breaker | `daily_0500_run.py:36,130` | `MAX_CONSEC_FAIL = 3` consecutive unreadable videos → stop that lane. |
| Profile-busy policy | `daily_profiles.py` + `--scheduled` | At 05:00 only: `ProfileUsingByOther` → `profiles/stop/<id>` → kill the **matching PID** (matched by `--user-data-dir`) → restart. Manual runs never do this (CLAUDE.md trap #9). |
| Task-level retry | Task Scheduler | `RestartCount 2`, `RestartInterval 15 min`. |

### 3.4 Completion detection
There is **no completion event, no exit-status contract, and no machine-readable run record**.
- Success signal is the human-readable log line `===== XONG: ... =====` in `reports/daily_0500/<date>.log`.
- The only side effect a consumer could watch is the Sheet itself.
- A desktop toast is fired at the end (`daily_0500_run.py:270-272` → `spike_notify.toast`), which is
  invisible to any program.
- Per-video progress is written to the Sheet **incrementally** (`daily_0500_run.py:170-176`, comment:
  "kiem xong TAP NAO GHI SHEET TAP DO NGAY"), so a partial run leaves a partially-updated Sheet with
  no marker saying it is partial. **YIE cannot distinguish "complete" from "died at video 60 of 88".**

### 3.5 Logs and run state
| Path | Content | Evidence |
|---|---|---|
| `reports/daily_0500/<YYYY-MM-DD>.log` | Full human log, one line per click/read/write | 12 files, 2026-10-16 … 2026-10-27; largest 185 KB |
| `reports/daily_0500/<date>/<tab>_truoc.json` | **Pre-write snapshot of the whole tab** (values + K-cell yellow flags) | e.g. `2026-10-27/F-teinengo-real_truoc.json`, 86 KB, 24 rows |
| `reports/daily_0500/<date>/<tab>_RS_goc.json` | First-rotation R/S values of the day (prevents double-rotation on same-day re-runs) | `daily_0500_run.py:120-125` |
| `reports/daily_0500/<date>/TONGHOP_truoc_<tab>_<HHMMSS>.json` | Pre-write snapshot of the summary tab | e.g. `TONGHOP_truoc_F-teinengo-real_055959.json` |
| `view_spike/state/run.lock` | PID + epoch of current holder | `spike_state.py:82-99` |
| `view_spike/state/snapshots.jsonl` | 2 744 lines of `{t, vid, views}` (API tier-1) | measured |

**The `<tab>_truoc.json` files are the single most valuable artefact for YIE** — see `04_DATABASE_AND_HISTORY.md`.

---

## 4. ACTUAL FLOW (start → report)

```
05:00:00  Task Scheduler starts daily_parallel.py (pythonw, interactive)
          │
05:00:03  bin-pack 11 groups into 3 buckets; take run.lock (waits ≤15 min if held)
          │
          ├── worker 1 ─┐
          ├── worker 2 ─┼─ for each group in its bucket, SEQUENTIALLY:
          └── worker 3 ─┘      open profile (GPM API / AdsPower API / Chrome 9222)
                               │   (serialized by open_lock — only one profile opens at a time, L109/L122)
                               └─ spawn child: daily_0500_run.py --attach <ws> --tab <tabs>
                                    │
                                    ├─ Sheets: read tab A1:S500 + K-column background colours
                                    ├─ YouTube Data API: videos.list (snippet,statistics) for all ids in tab
                                    │     → publishedAt, channelId, channelTitle, viewCount
                                    ├─ switch Studio to the tab's channel (switch_channel/verify_channel)
                                    ├─ backup whole tab → reports/daily_0500/<date>/<tab>_truoc.json
                                    │
                                    └─ for each row with an 11-char video_id in column L:
                                         hp.between_videos()            (20-55 s)
                                         read_video_full(page, vid)     (2 attempts)
                                           Content → click the video row → Analytics → Reach
                                           read lifetime: Views, CTR, Thumbnail impressions
                                           click date menu → Custom → yesterday → Apply
                                           read day-scoped: CTR, Thumbnail impressions
                                         compute hours = now − publishedAt (API)
                                         k_note(hours, views, ctr_total, ctr_24h, imp_24h)
                                         write N,O,P,Q + K to the row; paint whole row yellow
                                         tonghop(): mark "SỬA CTR" in TONGHOP tab
                                         (Sheet write happens PER VIDEO, not at lane end)
          │
06:3x     all workers join; release run.lock
06:35     log "===== XONG DA LUONG: 95 phut" + Windows toast
          │
          ▼
      OUTPUT = Google Sheet cells (N–S, K, TONGHOP).  NO file, NO JSON, NO CSV, NO event.
```

**There is no "report export" step.** The run's only durable machine-readable output is the Google Sheet
plus the per-tab pre-write JSON backups. `youtube_postpublish_metrics.csv` is **not** written by this job
(see `04`).

---

## 5. SEPARATE, NON-SCHEDULED COLLECTORS IN THE SAME REPO

These exist and are relevant to YIE because they contain metric-parsing code the daily job does not use:

| Tool | Invocation | Writes | Status |
|---|---|---|---|
| `tools/studio_collect.py` | manual, `--mail/--ws/--port --lane` | appends to `youtube_postpublish_metrics.csv` (70 cols) | **last row 2026-10-18**; not scheduled |
| `tools/studio_daily.py` | library, called by `studio_collect.py` only | adds `*_last_24h`, `daily_series` to the same CSV row | not called by 05:00 chain (`grep studio_daily tools/daily_0500_run.py` → no match) |
| `tools/sol_packaging_review.py` | manual, per-video | `reports/<vid>/sol_packaging_review.md` | 1 output exists (`reports/yCSzCQN_VsE/`) |
| `view_spike/spike_watch.py` | scheduled **but disabled** | `view_spike/state/alerts.jsonl` (4 lines) | `schtasks` → `Status: Disabled` |
| `viral_hunt/run_daily.py` | scheduled **but disabled** | `reports/viral_hunt/` | `Status: Disabled`, last run 2026-10-23 |
| `niche_watch/run_evening.py` | `install_tasks.ps1` exists but **tasks are not registered** | `niche_watch/state/` | `schtasks /query /tn NicheWatch1800` → *"The system cannot find the file specified"* |

`niche_watch` is the only consumer that performs YouTube browsing with like/subscribe actions; it is
**not registered** on this machine, so it did not run on schedule.

---

## 6. FACTS MOST LIKELY TO BREAK A NAIVE YIE INTEGRATION

1. **No completion signal** — YIE cannot tell a finished run from a half-finished one (§3.4).
2. **Sheet is written per video, non-atomically** — a reader polling the Sheet can observe a
   half-updated tab with no marker (`daily_0500_run.py:170-176`).
3. **Run duration is 90–111 min** and drifts; `ExecutionTimeLimit` is 2 h, so a slow day can be killed
   mid-run with the Sheet half-written.
4. **The output is a human-formatted Sheet**, not a data store: `P`/`Q` are strings like `6,30%`,
   `O` is `2900`, `K` is prose (`daily_k_rules.py:21-31`).
5. **The daily job captures only 5 numbers per video per day** (`N,O,P,Q` + `imp_24h`), all
   lifetime-or-single-day — no retention, no traffic-source split, no watch time (see `03`).
6. **Running code is untracked in git** — YIE pinned to this repo cannot rely on commit hashes.
